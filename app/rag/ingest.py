from pathlib import Path
from typing import Any
import re
import yaml


KB_PATH = Path("knowledge-base")


def parse_document(file_path: Path) -> dict[str, Any]:
    """Parse YAML front matter and Markdown body."""
    text = file_path.read_text(encoding="utf-8")

    metadata = {}
    body = text

    # Extract YAML front matter between --- markers.
    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n(.*)$",
        text,
        re.DOTALL,
    )

    if match:
        metadata = yaml.safe_load(match.group(1)) or {}

        # ChromaDB only accepts primitive metadata values.
        # PyYAML automatically converts dates into Python date objects,
        # so convert date/datetime values into ISO-format strings.
        for key, value in metadata.items():
            if hasattr(value, "isoformat"):
                metadata[key] = value.isoformat()

        body = match.group(2)

    metadata["filename"] = file_path.name

    return {
        "metadata": metadata,
        "body": body.strip(),
    }


def split_into_chunks(
    body: str,
    max_chars: int = 1200,
) -> list[dict[str, str]]:
    """
    Split Markdown into heading-aware chunks.

    Each chunk keeps its relevant heading so source references
    remain useful to the user.
    """
    lines = body.splitlines()

    chunks = []
    current_heading = "General"
    current_text: list[str] = []

    def save_chunk():
        if not current_text:
            return

        content = "\n".join(current_text).strip()

        if content:
            chunks.append(
                {
                    "heading": current_heading,
                    "text": content,
                }
            )

    for line in lines:
        stripped = line.strip()

        # Start a new chunk when a Markdown heading is found.
        if stripped.startswith("#"):
            save_chunk()

            current_heading = re.sub(
                r"^#+\s*",
                "",
                stripped,
            )

            current_text = []
            continue

        if stripped:
            current_text.append(line)

            # Prevent excessively large chunks.
            current_length = len("\n".join(current_text))

            if current_length >= max_chars:
                save_chunk()
                current_text = []

    # Save the final chunk.
    save_chunk()

    return chunks


def load_knowledge_base() -> list[dict[str, Any]]:
    """Load and chunk every Markdown document in knowledge-base."""
    documents = []

    for file_path in sorted(KB_PATH.glob("*.md")):
        parsed = parse_document(file_path)

        chunks = split_into_chunks(parsed["body"])

        for index, chunk in enumerate(chunks):
            metadata = dict(parsed["metadata"])

            metadata["heading"] = chunk["heading"]
            metadata["chunk_index"] = index

            documents.append(
                {
                    "id": f"{file_path.stem}-{index}",
                    "text": chunk["text"],
                    "metadata": metadata,
                }
            )

    return documents


if __name__ == "__main__":
    docs = load_knowledge_base()

    print(f"Loaded {len(docs)} chunks.")

    for doc in docs[:5]:
        print("\n---")
        print(doc["metadata"]["filename"])
        print(doc["metadata"]["heading"])
        print(doc["text"][:300])