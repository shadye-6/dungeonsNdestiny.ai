import os
import numpy as np
import faiss
from pymongo import MongoClient
from memory.embeddings import embed_text
from utils.config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME

MAX_FAISS_ENTRIES = 100  # only index last 100 entries in FAISS

class PersistentMemory:
    def __init__(self):
        # MongoDB setup
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[MONGO_COLLECTION_NAME]

        # In-memory FAISS index for fast retrieval
        self._index = None
        self.dim = None
        self.memory_cache = []  # cache last N entries for FAISS

        # Load latest N entries from MongoDB into FAISS
        self._load_latest_faiss_entries()

    def _load_latest_faiss_entries(self):
        # Retrieve last MAX_FAISS_ENTRIES sorted by insertion order
        docs = list(
            self.collection.find().sort("_id", -1).limit(MAX_FAISS_ENTRIES)
        )
        docs.reverse()  # so oldest is first

        self.memory_cache = docs

        if docs:
            self.dim = len(docs[0]["embedding"])
            self._index = faiss.IndexFlatIP(self.dim)
            vectors = np.array([d["embedding"] for d in docs], dtype="float32")
            self._index.add(vectors)

    def add_memory(self, summary, embedding):
        """Add memory to MongoDB and FAISS."""
        embedding = np.array(embedding, dtype="float32")
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Store in MongoDB
        doc = {"summary": summary, "embedding": embedding.tolist()}
        self.collection.insert_one(doc)

        # Update FAISS index cache
        if self._index is None:
            self.dim = embedding.shape[0]
            self._index = faiss.IndexFlatIP(self.dim)
            self.memory_cache = []

        # Maintain cache of last MAX_FAISS_ENTRIES
        self.memory_cache.append(doc)
        if len(self.memory_cache) > MAX_FAISS_ENTRIES:
            self.memory_cache.pop(0)  # remove oldest

        # Rebuild FAISS index
        vectors = np.array([d["embedding"] for d in self.memory_cache], dtype="float32")
        self._index.reset()
        self._index.add(vectors)

    def retrieve(self, query, top_k=3):
        """Retrieve top-k similar summaries using FAISS on latest entries."""
        if self._index is None or len(self.memory_cache) == 0:
            return []

        query_emb = np.array(embed_text(query), dtype="float32")
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        distances, indices = self._index.search(np.array([query_emb], dtype="float32"), top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.memory_cache):
                results.append(self.memory_cache[idx]["summary"])
        return results
