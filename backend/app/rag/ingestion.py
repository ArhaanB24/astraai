import os
import re
from typing import Dict, Any
from app.rag.chunker import chunk_text
from app.rag.qdrant_client import vector_store


def parse_frontmatter_and_content(file_content: str) -> tuple[Dict[str, Any], str]:
    """
    Extracts YAML-style frontmatter key-values from Obsidian Markdown files.
    """
    metadata: Dict[str, Any] = {}
    content = file_content

    if file_content.startswith("---"):
        parts = file_content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2].strip()

            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key:
                        metadata[key] = val

    return metadata, content


def ingest_obsidian_vault():
    """
    Recursively scans and ingests the ArthaAI Obsidian Knowledge Vault (`arths/`).
    Chunks markdown notes and upserts semantic vector embeddings into the vector store.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    vault_dir = os.path.join(project_root, "arths")

    if not os.path.exists(vault_dir):
        # Fallback to local knowledge directory if arths is not found
        vault_dir = os.path.join(project_root, "knowledge")
        if not os.path.exists(vault_dir):
            return

    for root, dirs, files in os.walk(vault_dir):
        # Skip internal Obsidian configuration directory
        if ".obsidian" in root:
            continue

        for filename in files:
            if filename.endswith(".md") or filename.endswith(".txt"):
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                fm_metadata, body_content = parse_frontmatter_and_content(raw_content)

                doc_title = fm_metadata.get("title") or filename.replace(".md", "").replace(".txt", "").replace("_", " ").title()
                doc_source = fm_metadata.get("source") or os.path.relpath(filepath, vault_dir)
                doc_name = fm_metadata.get("document_name") or doc_title
                doc_section = fm_metadata.get("section") or "General Knowledge"
                fund_name = fm_metadata.get("fund_name") or doc_title

                chunks = chunk_text(
                    body_content,
                    chunk_size=150,
                    chunk_overlap=20,
                    metadata={
                        "title": doc_title,
                        "source": doc_source,
                        "document_name": doc_name,
                        "section": doc_section,
                        "document_type": "obsidian_note",
                        "fund_name": fund_name,
                        "url": fm_metadata.get("url"),
                        "category": fm_metadata.get("category", "Financial Knowledge")
                    }
                )
                vector_store.upsert_chunks(chunks)


# Auto-ingest on module load
ingest_obsidian_vault()
