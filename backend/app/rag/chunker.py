from typing import List, Dict, Any


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Chunks document text into overlapping passages while preserving page, section, and source metadata.
    """
    if metadata is None:
        metadata = {}

    words = text.split()
    chunks = []
    chunk_idx = 0
    i = 0

    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk_str = " ".join(chunk_words)

        chunk_meta = metadata.copy()
        chunk_meta["chunk_index"] = chunk_idx

        chunks.append({
            "content": chunk_str,
            "metadata": chunk_meta
        })

        chunk_idx += 1
        i += (chunk_size - chunk_overlap)

    return chunks
