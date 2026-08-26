from pathlib import Path

from app.rag.ingest import (
    parse_document,
    split_into_chunks,
    load_knowledge_base,
)


def test_parse_document_reads_metadata_and_body(tmp_path):
    document = tmp_path / "test.md"

    document.write_text(
        """---
document_id: TEST-001
title: Test Policy
status: active
effective_date: 2026-08-01
policy_authority: official
---

# Test Policy

This is test policy content.
""",
        encoding="utf-8",
    )

    result = parse_document(document)

    assert result["metadata"]["document_id"] == "TEST-001"
    assert result["metadata"]["title"] == "Test Policy"
    assert result["metadata"]["status"] == "active"
    assert result["metadata"]["effective_date"] == "2026-08-01"
    assert result["body"] == "# Test Policy\n\nThis is test policy content."


def test_split_into_chunks_preserves_headings():
    body = """# Return Policy

Returns are allowed within 30 days.

## Refunds

Refunds are issued within 5-7 business days.
"""

    chunks = split_into_chunks(body)

    assert len(chunks) == 2
    assert chunks[0]["heading"] == "Return Policy"
    assert chunks[1]["heading"] == "Refunds"
    assert "30 days" in chunks[0]["text"]
    assert "5-7 business days" in chunks[1]["text"]


def test_split_into_chunks_respects_max_chars():
    body = """# Policy

This is a long piece of policy content that should be split
into multiple chunks when the maximum character limit is small.
"""

    chunks = split_into_chunks(body, max_chars=50)

    assert len(chunks) > 1


def test_load_knowledge_base_returns_chunks():
    documents = load_knowledge_base()

    assert len(documents) > 0

    for document in documents:
        assert "id" in document
        assert "text" in document
        assert "metadata" in document

        assert document["text"].strip()
        assert document["metadata"]["filename"]
        assert document["metadata"]["heading"]


def test_knowledge_base_chunk_ids_are_unique():
    documents = load_knowledge_base()

    ids = [document["id"] for document in documents]

    assert len(ids) == len(set(ids))