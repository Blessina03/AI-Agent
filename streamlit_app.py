import streamlit as st

from app.agent import run_agent


st.set_page_config(
    page_title="Aster & Row Support",
    page_icon="🛍️",
    layout="centered",
)


st.title("Aster & Row Support")
st.caption("Customer support assistant")


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


question = st.chat_input("How can we help you?")


if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking information..."):
            try:
                answer = run_agent(question)

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as error:
                # Show the real error during debugging
                st.error("Agent Error:")
                st.code(str(error))

                # Also print it in terminal
                print("AGENT ERROR:", error)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "An internal error occurred. "
                            "Please check the terminal logs."
                        ),
                    }
                )