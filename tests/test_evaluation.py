from app.tools.orders import lookup_order
from app.rag.retriever import Retriever


class FakeEmbeddings:
    """Fake embeddings so evaluation tests never call Gemini."""

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


# ---------------------------------------------------------
# ORDER SAFETY EVALUATION
# ---------------------------------------------------------

def test_cancelled_order_does_not_expose_stale_shipping_data():
    result = lookup_order("ORD-1004")

    assert result["found"] is True
    assert result["status"] == "cancelled"

    assert "tracking_number" not in result
    assert "carrier" not in result
    assert "estimated_delivery" not in result


def test_returned_order_does_not_expose_stale_shipping_data():
    result = lookup_order("ORD-1008")

    assert result["found"] is True
    assert result["status"] == "returned"

    assert "tracking_number" not in result
    assert "carrier" not in result
    assert "estimated_delivery" not in result


def test_unknown_order_is_not_guessed():
    result = lookup_order("ORD-9999")

    assert result["found"] is False
    assert result["order_id"] == "ORD-9999"


def test_exception_order_requires_human_handoff():
    result = lookup_order("ORD-1010")

    assert result["found"] is True
    assert result["status"] == "exception"
    assert "human handoff" in result["operational_note"].lower()


def test_shipped_order_without_eta_does_not_invent_eta():
    result = lookup_order("ORD-1011")

    assert result["found"] is True
    assert result["status"] == "shipped"
    assert result["estimated_delivery"] is None


def test_internal_customer_information_is_never_returned():
    result = lookup_order("ORD-1007")

    forbidden_fields = {
        "customer",
        "name",
        "email",
        "shipping_address",
        "internal",
        "risk_score",
        "warehouse_note",
        "support_tags",
    }

    assert forbidden_fields.isdisjoint(result.keys())


# ---------------------------------------------------------
# RAG RELIABILITY EVALUATION
# ---------------------------------------------------------

def test_active_policy_beats_superseded_policy(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Legacy policy: 45 days.",
            "Current policy: 30 days.",
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

    results = retriever.search("return window", n_results=2)

    assert results[0]["metadata"]["status"] == "active"


def test_internal_content_is_ranked_below_customer_content(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Internal migration note.",
            "Approved customer policy.",
        ]],
        "metadatas": [[
            {
                "status": "active",
                "policy_authority": "official",
                "audience": "internal",
                "customer_answering": False,
            },
            {
                "status": "active",
                "policy_authority": "official",
                "audience": "customer",
                "customer_answering": True,
            },
        ]],
        "distances": [[0.1, 0.1]],
    }

    results = retriever.search("return policy", n_results=2)

    assert results[0]["metadata"]["audience"] == "customer"


def test_non_official_content_does_not_beat_official_content(monkeypatch):
    retriever = create_retriever(monkeypatch)

    retriever.collection.query = lambda **kwargs: {
        "documents": [[
            "Unofficial policy information.",
            "Official policy information.",
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