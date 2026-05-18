import numpy as np
import faiss
from pymongo import MongoClient
from memory.embeddings import embed_text
from utils.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME

MAX_FAISS_ENTRIES = 500


class PersistentMemory:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[MONGO_COLLECTION_NAME]

        self._index = None
        self.dim = None
        self.memory_cache = []

        self._load_latest_faiss_entries()

    def _load_latest_faiss_entries(self):
        docs = list(self.collection.find().sort("_id", -1).limit(MAX_FAISS_ENTRIES))
        docs.reverse()
        self.memory_cache = docs

        if docs:
            self.dim = len(docs[0]["embedding"])
            self._index = faiss.IndexFlatIP(self.dim)
            vectors = np.array([d["embedding"] for d in docs], dtype="float32")
            self._index.add(vectors)

    def add_memory(self, summary: str, embedding):
        embedding = np.array(embedding, dtype="float32")
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        doc = {"summary": summary, "embedding": embedding.tolist()}
        self.collection.insert_one(doc)

        if self._index is None:
            self.dim = embedding.shape[0]
            self._index = faiss.IndexFlatIP(self.dim)
            self.memory_cache = []

        self.memory_cache.append(doc)

        if len(self.memory_cache) > MAX_FAISS_ENTRIES:
            # Oldest entry evicted — FAISS has no delete, so rebuild
            self.memory_cache.pop(0)
            vectors = np.array([d["embedding"] for d in self.memory_cache], dtype="float32")
            self._index.reset()
            self._index.add(vectors)
        else:
            self._index.add(embedding.reshape(1, -1))

    def retrieve(self, query: str, top_k: int = 5) -> list:
        if self._index is None or not self.memory_cache:
            return []

        query_emb = np.array(embed_text(query), dtype="float32")
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        k = min(top_k, len(self.memory_cache))
        distances, indices = self._index.search(query_emb.reshape(1, -1), k)

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.memory_cache):
                results.append(self.memory_cache[idx]["summary"])
        return results

    def get_recent_memories(self, n: int = 5) -> list:
        docs = list(self.collection.find().sort("_id", -1).limit(n))
        docs.reverse()
        return [d["summary"] for d in docs]

    def count(self) -> int:
        return self.collection.count_documents({})
