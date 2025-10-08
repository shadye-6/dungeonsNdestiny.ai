# memory/persistent_memory.py
import json
from memory.embeddings import embed_text
from utils.helpers import cosine_similarity

class PersistentMemory:
    def __init__(self, path="storage/world_state.json"):
        self.path = path
        self.load()

    def load(self):
        try:
            with open(self.path, "r") as f:
                self.memory = json.load(f)
        except FileNotFoundError:
            self.memory = []

    def add_memory(self, summary, embedding):
        self.memory.append({"summary": summary, "embedding": embedding})
        self.save()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def retrieve(self, query, top_k=3):
        query_emb = embed_text(query)
        # simple cosine similarity retrieval
        scored = [(m, cosine_similarity(query_emb, m["embedding"])) for m in self.memory]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m["summary"] for m, _ in scored[:top_k]]
