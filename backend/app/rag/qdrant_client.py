from typing import List, Dict, Any, Optional
import numpy as np
from app.rag.embeddings import embedding_provider
from app.core.config import settings

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class VectorStoreService:
    """
    Qdrant Vector Database Integration with Local In-Memory Fallback.
    Stores and retrieves mutual fund factsheets, AMC reports, and SEBI document chunks.
    """

    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self.in_memory_docs: List[Dict[str, Any]] = []
        self.qclient = None

        if QDRANT_AVAILABLE:
            try:
                self.qclient = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
                # Create collection if not exists
                collections = [c.name for c in self.qclient.get_collections().collections]
                if self.collection_name not in collections:
                    self.qclient.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=qmodels.VectorParams(
                            size=embedding_provider.DIMENSION,
                            distance=qmodels.Distance.COSINE
                        )
                    )
            except Exception as e:
                print(f"Qdrant connection warning (using in-memory vector fallback): {e}")
                self.qclient = None

    def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        for idx, chunk in enumerate(chunks):
            content = chunk["content"]
            metadata = chunk["metadata"]
            vector = embedding_provider.get_embedding(content)

            item = {
                "id": str(idx + len(self.in_memory_docs) + 1),
                "vector": vector,
                "payload": {
                    "content": content,
                    **metadata
                }
            }
            self.in_memory_docs.append(item)

            if self.qclient:
                try:
                    self.qclient.upsert(
                        collection_name=self.collection_name,
                        points=[
                            qmodels.PointStruct(
                                id=idx + len(self.in_memory_docs),
                                vector=vector,
                                payload={"content": content, **metadata}
                            )
                        ]
                    )
                except Exception as e:
                    print(f"Qdrant upsert error: {e}")

        return True

    def search(self, query: str, top_k: int = 4, filter_fund_name: Optional[str] = None) -> List[Dict[str, Any]]:
        query_vec = embedding_provider.get_embedding(query)
        results = []

        # Search in-memory vector collection
        for item in self.in_memory_docs:
            payload = item["payload"]
            if filter_fund_name and filter_fund_name.lower() not in payload.get("fund_name", "").lower():
                continue

            doc_vec = np.array(item["vector"])
            q_vec = np.array(query_vec)
            score = float(np.dot(doc_vec, q_vec))

            results.append({
                "content": payload["content"],
                "document_name": payload.get("title", payload.get("source", "Official Factsheet")),
                "source": payload.get("source", "AMC Disclosure"),
                "page_number": payload.get("page_number", 1),
                "section": payload.get("section", "Fund Strategy"),
                "relevance_score": round(score, 2),
                "url": payload.get("url")
            })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]


vector_store = VectorStoreService()

# Auto-ingest Obsidian Vault on initialization
try:
    from app.rag.ingestion import ingest_obsidian_vault
    ingest_obsidian_vault()
except Exception as e:
    print(f"Obsidian Vault auto-ingestion warning: {e}")
