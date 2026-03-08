from sentence_transformers import SentenceTransformer
from typing import List


class LocalEmbedder:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            print("Loading embedding model... (first time only)")
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Embedding model ready.")
        return cls._instance

    def embed(self, text: str) -> List[float]:
        vector = self._model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()


# Singleton instance
embedder = LocalEmbedder()
