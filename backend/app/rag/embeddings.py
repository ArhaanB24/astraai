import math
import numpy as np
from typing import List


class SimpleEmbeddingProvider:
    """
    Deterministic Embedding Generator for RAG vector search.
    Computes normalized semantic feature vectors for text chunks.
    """

    DIMENSION = 384

    def get_embedding(self, text: str) -> List[float]:
        # Hash words to deterministic vector dimensions
        vec = np.zeros(self.DIMENSION, dtype=float)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for idx, word in enumerate(words):
            h = hash(word) % self.DIMENSION
            vec[h] += 1.0 / (math.log(idx + 2))

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


embedding_provider = SimpleEmbeddingProvider()
