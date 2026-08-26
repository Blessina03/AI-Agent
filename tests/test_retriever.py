from app.rag.retriever import Retriever


class FakeEmbeddings:
    """Fake embeddings so retriever tests do not call Gemini API."""

    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


def create_retriever(monkeypatch):
    """Create a Retriever without calling the Gemini API."""
    monkeypatch.setattr(
        "app.rag.retriever.GeminiEmbeddings",
        FakeEmbeddings,
    )

    return Retriever()


def test_retriever_can_be_created_without_gemini_api(monkeypatch):
    retriever = create_retriever(monkeypatch)

    assert retriever.collection is not None
    assert isinstance(retriever.embeddings, FakeEmbeddings)


def test_active_policy_is_ranked_above_superseded_policy(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Old return policy",
            "Current return policy",
        ]],
        "metadatas": [[
            {
                "status": "superseded",
                "policy_authority": "official",
            },
            {
                "status": "active",
                "policy_authority": "official",
            },
        ]],
        "distances": [[0.1, 0.1]],
    }

    results = retriever.search("return policy", n_results=2)

    assert results[0]["metadata"]["status"] == "active"


def test_official_policy_is_ranked_above_non_official_policy(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Unofficial return information",
            "Official return policy",
        ]],
        "metadatas": [[
            {
                "status": "active",
                "policy_authority": "unofficial",
            },
            {
                "status": "active",
                "policy_authority": "official",
            },
        ]],
        "distances": [[0.1, 0.1]],
    }

    results = retriever.search("return policy", n_results=2)

    assert results[0]["metadata"]["policy_authority"] == "official"


def test_internal_content_is_penalized(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Internal support notes",
            "Customer-facing policy",
        ]],
        "metadatas": [[
            {
                "status": "active",
                "policy_authority": "official",
                "audience": "internal",
            },
            {
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
            },
        ]],
        "distances": [[0.1, 0.1]],
    }

    results = retriever.search("return policy", n_results=2)

    assert results[0]["metadata"]["audience"] == "customer"


def test_non_customer_answering_content_is_penalized(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Draft internal content",
            "Approved customer content",
        ]],
        "metadatas": [[
            {
                "status": "active",
                "policy_authority": "official",
                "customer_answering": False,
            },
            {
                "status": "active",
                "policy_authority": "official",
                "customer_answering": True,
            },
        ]],
        "distances": [[0.1, 0.1]],
    }

    results = retriever.search("return policy", n_results=2)

    assert results[0]["metadata"]["customer_answering"] is True