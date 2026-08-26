from pathlib import Path
import chromadb

from app.rag.ingest import load_knowledge_base
from app.rag.embeddings import GeminiEmbeddings


CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "aster_row_knowledge"


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH)
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME
        )

        self.embeddings = GeminiEmbeddings()

    def build_index(self):
        """Build the ChromaDB index from the knowledge base."""
        documents = load_knowledge_base()

        if not documents:
            raise ValueError("No knowledge-base documents found.")

        # Clear old index so rebuilding is deterministic.
        existing = self.collection.get()

        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])

        texts = [doc["text"] for doc in documents]

        vectors = self.embeddings.embed_documents(texts)

        self.collection.add(
            ids=[doc["id"] for doc in documents],
            documents=texts,
            embeddings=vectors,
            metadatas=[doc["metadata"] for doc in documents],
        )

        print(f"Indexed {len(documents)} chunks.")

    def search(self, query: str, n_results: int = 8) -> list[dict]:
        """Search the knowledge base and apply metadata-aware ranking."""

        query_vector = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        ranked = []

        for i, text in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Convert Chroma distance to a rough similarity score.
            semantic_score = 1 / (1 + distance)

            score = semantic_score

            # Prefer active policies.
            if metadata.get("status") == "active":
                score += 0.08

            # Strongly penalize superseded content.
            elif metadata.get("status") == "superseded":
                score -= 0.15

            # Prefer official policy content.
            if metadata.get("policy_authority") == "official":
                score += 0.03

            # Internal content should not control customer answers.
            if metadata.get("audience") == "internal":
                score -= 0.20

            # Draft/non-customer material gets another penalty.
            if metadata.get("customer_answering") is False:
                score -= 0.20

            ranked.append({
                "text": text,
                "metadata": metadata,
                "distance": distance,
                "score": score,
            })

        ranked.sort(key=lambda item: item["score"], reverse=True)

        return ranked


if __name__ == "__main__":
    retriever = Retriever()
    retriever.build_index()