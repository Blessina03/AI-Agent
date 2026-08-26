"""
Conflict detection between knowledge base documents.
"""


def normalize_text(text: str):
    """
    Normalize text for comparison.
    """

    return (
        text.lower()
        .replace("\n", " ")
        .strip()
    )



def extract_keywords(text):

    """
    Extract important policy keywords.
    """

    words = normalize_text(text).split()

    ignored = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "your",
        "you",
        "are",
        "can"
    }


    return {
        word
        for word in words
        if word not in ignored
    }



def detect_conflicts(results):

    """
    Detect contradictions between active official documents.

    Returns:
        {
          "conflict": True/False,
          "documents": []
        }
    """


    active_docs = []


    for result in results:


        metadata = result["metadata"]


        if (

            metadata.get("status") == "active"

            and

            metadata.get("policy_authority") == "official"

        ):


            active_docs.append(

                {

                    "title":
                    metadata.get("title"),


                    "content":
                    result["text"]

                }

            )



    if len(active_docs) < 2:

        return {

            "conflict": False,

            "documents": []

        }



    conflicts = []



    for i in range(len(active_docs)):


        for j in range(i + 1, len(active_docs)):


            doc1 = active_docs[i]

            doc2 = active_docs[j]


            words1 = extract_keywords(
                doc1["content"]
            )


            words2 = extract_keywords(
                doc2["content"]
            )


            overlap = (
                len(words1.intersection(words2))
                /
                max(
                    len(words1.union(words2)),
                    1
                )
            )


            # Low similarity between official docs
            # on same topic indicates possible conflict

            if overlap < 0.15:


                conflicts.append(

                    {

                        "source_1":
                        doc1["title"],


                        "source_2":
                        doc2["title"]

                    }

                )


    return {


        "conflict":
        len(conflicts) > 0,


        "documents":
        conflicts

    }