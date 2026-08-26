from app.rag.retriever import Retriever


if __name__ == "__main__":
    print("Building Aster & Row knowledge index...")

    retriever = Retriever()
    retriever.build_index()

    print("Knowledge index built successfully.")