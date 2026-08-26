import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.rag.retriever import Retriever
from app.tools.orders import lookup_order
from app.rag.conflicts import detect_conflicts


load_dotenv()


DEBUG = os.getenv(
    "DEBUG",
    "false"
).lower() == "true"



SYSTEM_PROMPT = """

You are the Aster & Row customer support assistant.

Answer customers using ONLY:

1. Knowledge base search
2. Order lookup tool


KNOWLEDGE BASE RULES:

- Use knowledge search for:

returns,
refunds,
shipping,
warranty,
products,
membership,
gift cards,
support questions


- Prefer:

active policies,
official documents,
customer-facing documents


- Never use:

internal notes,
drafts,
migration documents,
superseded policies


- If information is missing say:

"I could not verify this information from the knowledge base."


ORDER RULES:

- Always use lookup_order for specific orders.

- Never invent:

order status,
tracking,
ETA,
refunds,
delivery dates.


- Only provide customer-safe fields.


PRIVACY RULES:

Never reveal:

customer names,
emails,
addresses,
warehouse notes,
risk scores,
internal tags.


SHIPPING RULES:

- Order status is authoritative.
- Never calculate delivery dates.
- Never guess ETA.


ACTION RULES:

This assistant is READ ONLY.

Never claim:

refund completed,
replacement created,
address changed,
cancellation completed,
escalation completed.


CONFLICT RULES:

If active official documents conflict:

- Explain that sources disagree.
- Do not choose randomly.
- Recommend contacting support.


ANSWER STYLE:

- Be concise.
- Do not reveal reasoning.
- Include sources when knowledge base is used.

"""



# -------------------------
# Persistent Gemini session
# -------------------------

_chat_session = None



def get_chat(client, tools):

    global _chat_session


    if _chat_session is None:


        _chat_session = client.chats.create(

            model="gemini-3.6-flash",

            config=types.GenerateContentConfig(

                system_instruction=SYSTEM_PROMPT,

                tools=tools,

                temperature=0.1

            )

        )


    return _chat_session




# -------------------------
# Citation storage
# -------------------------

retrieved_sources = []



# -------------------------
# RAG tool
# -------------------------

def search_knowledge_base(query: str):

    global retrieved_sources


    retriever = Retriever()


    results = retriever.search(

        query,

        n_results=6

    )


    if not results:

        return (
            "No relevant knowledge-base information was found."
        )


    retrieved_sources = []


    formatted = []


    conflict_result = detect_conflicts(
        results
    )


    for result in results:


        metadata = result["metadata"]


        title = metadata.get(
            "title"
        )


        if (

            metadata.get("status") == "active"

            and

            metadata.get("policy_authority") == "official"

        ):

            retrieved_sources.append(
                title
            )


        formatted.append(

            {

                "title":
                title,


                "status":
                metadata.get("status"),


                "authority":
                metadata.get(
                    "policy_authority"
                ),


                "heading":
                metadata.get(
                    "heading"
                ),


                "content":
                result["text"],


                "score":
                round(
                    result["score"],
                    4
                )

            }

        )



    if conflict_result["conflict"]:


        formatted.append(

            {

                "WARNING":

                "Multiple active official documents contain conflicting information.",


                "conflicting_documents":

                conflict_result["documents"]

            }

        )



    if DEBUG:


        print(
            "\n========== RAG DEBUG =========="
        )


        print(

            json.dumps(
                formatted,
                indent=2
            )

        )



    return json.dumps(

        formatted,

        indent=2

    )





# -------------------------
# Agent
# -------------------------

def run_agent(user_message: str):


    global retrieved_sources


    retrieved_sources = []



    api_key = os.getenv(
        "GEMINI_API_KEY"
    )


    if not api_key:

        raise ValueError(
            "GEMINI_API_KEY missing"
        )



    client = genai.Client(
        api_key=api_key
    )


    tools = [

        search_knowledge_base,

        lookup_order

    ]



    chat = get_chat(

        client,

        tools

    )


    response = chat.send_message(

        user_message

    )


    answer = response.text



    if retrieved_sources:


        sources = list(

            dict.fromkeys(
                retrieved_sources
            )

        )


        sources = sources[:3]


        answer += "\n\nSources:\n"


        for source in sources:

            answer += (
                f"- {source}\n"
            )


    return answer





# -------------------------
# CLI
# -------------------------

if __name__ == "__main__":


    print(
        "Aster & Row Support Agent"
    )


    print(
        "Type 'exit' to quit.\n"
    )


    while True:


        question = input(
            "You: "
        ).strip()



        if question.lower() == "exit":

            break



        if not question:

            continue



        try:


            answer = run_agent(
                question
            )


            print(
                f"\nAssistant: {answer}\n"
            )


        except Exception as error:


            print(
                f"\nError: {error}\n"
            )