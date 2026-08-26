from app.rag.retriever import Retriever


def main():
    retriever = Retriever()

    queries = [
        "How many days do I have to return an item?",
        "What is the return shipping fee?",
        "What happens if I receive the wrong item?",
        "Can I return a gift card?",
    ]

    for query in queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = retriever.search(query, n_results=5)

        for i, result in enumerate(results, start=1):
            metadata = result["metadata"]

            print(f"\n{i}. Score: {result['score']:.4f}")
            print(f"   Document: {metadata.get('document_id')}")
            print(f"   Title: {metadata.get('title')}")
            print(f"   Status: {metadata.get('status')}")
            print(f"   Authority: {metadata.get('policy_authority')}")
            print(f"   Heading: {metadata.get('heading')}")
            print(f"   Text: {result['text'][:250]}")


if __name__ == "__main__":
    main()