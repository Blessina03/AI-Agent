from dotenv import load_dotenv
from google import genai
import os


load_dotenv()


class GeminiEmbeddings:
    """Generate document/query embeddings using Gemini."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from .env")

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-embedding-001"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for document chunks."""
        embeddings = []

        for text in texts:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config={
                    "task_type": "RETRIEVAL_DOCUMENT",
                    "output_dimensionality": 768,
                },
            )

            embeddings.append(response.embeddings[0].values)

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Create an embedding for a user query."""
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={
                "task_type": "RETRIEVAL_QUERY",
                "output_dimensionality": 768,
            },
        )

        return response.embeddings[0].values