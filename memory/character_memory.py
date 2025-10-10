import faiss
import numpy as np
from memory.embeddings import embed_text

class CharacterMemory:
    def __init__(self):
        # { npc_name: [ {"text": str, "embedding": np.array}, ... ] }
        self.npc_memories = {}

    def add_interaction(self, npc_name: str, interaction_text: str):
        """Add a new memory for an NPC (with embedding)."""
        embedding = embed_text(interaction_text)
        entry = {"text": interaction_text, "embedding": np.array(embedding, dtype="float32")}

        if npc_name not in self.npc_memories:
            self.npc_memories[npc_name] = []
        self.npc_memories[npc_name].append(entry)

        # Keep only the 100 most recent
        if len(self.npc_memories[npc_name]) > 100:
            self.npc_memories[npc_name] = self.npc_memories[npc_name][-100:]

    def get_memory(self, npc_name: str, query: str = None, top_k: int = 5):
        """
        Retrieve up to `top_k` most relevant memories for an NPC
        using FAISS similarity search over the last 100 entries.
        If no query is provided, return the most recent 5.
        """
        if npc_name not in self.npc_memories or not self.npc_memories[npc_name]:
            return []

        entries = self.npc_memories[npc_name]
        texts = [e["text"] for e in entries]
        embeddings = np.array([e["embedding"] for e in entries], dtype="float32")

        # If no query, just return last few
        if query is None:
            return texts[-top_k:]

        # Build FAISS index
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  
        index.add(embeddings)

        query_emb = np.array([embed_text(query)], dtype="float32")
        scores, indices = index.search(query_emb, top_k)

        # Return top matches
        return [texts[i] for i in indices[0] if i < len(texts)]
