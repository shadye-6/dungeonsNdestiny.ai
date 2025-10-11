import faiss
import numpy as np
from pymongo import MongoClient
from memory.embeddings import embed_text
from utils.config import MONGO_URI, MONGO_DB_NAME, CHARACTER_COLLECTION

class CharacterMemory:
    def __init__(self):
        # In-memory store for last 100 memories per NPC
        self.npc_memories = {}

        # MongoDB connection for persistence
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        self.collection = db[CHARACTER_COLLECTION]

    def add_interaction(self, npc_name: str, interaction_text: str):
        embedding_array = np.array(embed_text(interaction_text), dtype="float32")
        entry = {"text": interaction_text, "embedding": embedding_array}

        # In-memory store
        if npc_name not in self.npc_memories:
            self.npc_memories[npc_name] = []
        self.npc_memories[npc_name].append(entry)
        if len(self.npc_memories[npc_name]) > 100:
            self.npc_memories[npc_name] = self.npc_memories[npc_name][-100:]

        # MongoDB persistence
        doc = {
            "npc_name": npc_name,
            "interaction": interaction_text,
            "embedding": embedding_array.tolist()
        }

        print(f"💬 Logging NPC interaction: {npc_name} -> {interaction_text[:50]}...")
        result = self.collection.insert_one(doc)
        print(f"✅ Inserted into MongoDB with _id: {result.inserted_id}")

    def get_memory(self, npc_name: str, query: str = None, top_k: int = 5):
        """
        Retrieve up to `top_k` relevant memories for an NPC.
        If query is None, returns the last `top_k` interactions.
        Uses FAISS similarity search on in-memory embeddings.
        """
        if npc_name not in self.npc_memories or not self.npc_memories[npc_name]:
            return []

        entries = self.npc_memories[npc_name]
        texts = [e["text"] for e in entries]
        embeddings = np.array([e["embedding"] for e in entries], dtype="float32")

        if query is None:
            return texts[-top_k:]

        # FAISS similarity search
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)

        query_emb = np.array([embed_text(query)], dtype="float32")
        scores, indices = index.search(query_emb, top_k)

        return [texts[i] for i in indices[0] if i < len(texts)]

    def get_all_interactions(self, npc_name: str):
        """Fetch all persisted NPC interactions from MongoDB."""
        docs = self.collection.find({"npc_name": npc_name})
        return [doc["interaction"] for doc in docs]
