# memory/persistent_memory.py
import os
import json
import numpy as np
import faiss
from memory.embeddings import embed_text

class PersistentMemory:
    def __init__(self, path="storage/world_state.json"):
        """
        PersistentMemory with FAISS, auto-detects embedding dimension on first add.
        """
        self.path = path
        self.memory = []  # list of {"summary": ..., "embedding": ...}
        self.ids = []     # FAISS index IDs
        self._index = None  # FAISS index (will be initialized after first embedding)
        self.dim = None     # will store embedding dimension

        # ensure storage folder exists
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        # load existing memory if available
        self.load()

    def load(self):
        """Load memory from JSON and rebuild FAISS index if data exists."""
        try:
            with open(self.path, "r") as f:
                self.memory = json.load(f)
            self.ids = list(range(len(self.memory)))
            if self.memory:
                # auto-detect dimension
                self.dim = len(self.memory[0]["embedding"])
                self._index = faiss.IndexFlatIP(self.dim)
                vectors = np.array([m["embedding"] for m in self.memory], dtype="float32")
                self._index.add(vectors)
        except FileNotFoundError:
            self.memory = []
            self.ids = []

    def save(self):
        """Save memory to JSON file."""
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def add_memory(self, summary, embedding):
        """Add a new memory entry (embedding auto-normalized)."""
        embedding = np.array(embedding, dtype="float32")
        # normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # Initialize FAISS index if first embedding
        if self._index is None:
            self.dim = embedding.shape[0]
            self._index = faiss.IndexFlatIP(self.dim)

        # Safety check
        if embedding.shape[0] != self.dim:
            raise ValueError(f"Embedding dimension {embedding.shape[0]} does not match FAISS index dimension {self.dim}")

        # store memory
        self.memory.append({"summary": summary, "embedding": embedding.tolist()})
        self.ids.append(len(self.memory) - 1)
        self._index.add(np.array([embedding], dtype="float32"))

        self.save()

    def retrieve(self, query, top_k=3):
        """Retrieve top-k most similar memories."""
        query_emb = np.array(embed_text(query), dtype="float32")
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm

        if self._index is None or len(self.memory) == 0:
            return []

        distances, indices = self._index.search(np.array([query_emb], dtype="float32"), top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.memory):
                results.append(self.memory[idx]["summary"])
        return results
