import faiss
import numpy as np
from pymongo import MongoClient
from memory.embeddings import embed_text
from utils.config import MONGO_URI, MONGO_DB_NAME, CHARACTER_COLLECTION


class CharacterMemory:
    def __init__(self):
        # In-memory store for last 50 memories per NPC
        self.npc_memories = {}

        # FAISS indices per NPC
        self.npc_indices = {}

        # MongoDB connection for persistence
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        self.collection = db[CHARACTER_COLLECTION]

        # Load memories and initialize FAISS indices
        self._load_existing_memories()

    def _load_existing_memories(self):
        """Load the last 50 interactions per NPC from MongoDB and build FAISS indices."""
        npc_data = {}

        for doc in self.collection.find({}, {"npc_name": 1, "interaction": 1, "embedding": 1}):
            npc_name = doc["npc_name"]
            if npc_name not in npc_data:
                npc_data[npc_name] = []
            npc_data[npc_name].append({
                "text": doc["interaction"],
                "embedding": np.array(doc["embedding"], dtype="float32")
            })

        for npc_name, interactions in npc_data.items():
            # Keep only the latest 50
            interactions = interactions[-50:]
            self.npc_memories[npc_name] = interactions

            # Build FAISS index
            if interactions:
                dim = interactions[0]["embedding"].shape[0]
                index = faiss.IndexFlatIP(dim)
                embeddings = np.array([e["embedding"] for e in interactions], dtype="float32")
                index.add(embeddings)
                self.npc_indices[npc_name] = index

        print(f"✅ Loaded FAISS memory for {len(npc_data)} NPC(s) from MongoDB")

    def _rebuild_faiss_index(self, npc_name: str):
        """Rebuild FAISS index for an NPC (when their memory list changes)."""
        entries = self.npc_memories.get(npc_name, [])
        if not entries:
            return
        dim = entries[0]["embedding"].shape[0]
        index = faiss.IndexFlatIP(dim)
        embeddings = np.array([e["embedding"] for e in entries], dtype="float32")
        index.add(embeddings)
        self.npc_indices[npc_name] = index

    def add_interaction(self, npc_name: str, interaction_text: str):
        """Add a new interaction to memory and persist it."""
        embedding_array = np.array(embed_text(interaction_text), dtype="float32")
        entry = {"text": interaction_text, "embedding": embedding_array}

        # In-memory store (limit to 50)
        if npc_name not in self.npc_memories:
            self.npc_memories[npc_name] = []
        self.npc_memories[npc_name].append(entry)
        if len(self.npc_memories[npc_name]) > 50:
            self.npc_memories[npc_name] = self.npc_memories[npc_name][-50:]

        # Rebuild FAISS index for this NPC
        self._rebuild_faiss_index(npc_name)

        # MongoDB persistence
        doc = {
            "npc_name": npc_name,
            "interaction": interaction_text,
            "embedding": embedding_array.tolist()
        }
        self.collection.insert_one(doc)

        # print(f"💬 Logged NPC interaction: {npc_name} -> {interaction_text[:50]}...")

    def get_memory(self, npc_name: str, query: str = None, top_k: int = 5):
        """
        Retrieve up to `top_k` relevant memories for an NPC.
        If query is None, returns the last `top_k` interactions.
        Uses prebuilt FAISS index for semantic similarity search.
        """
        if npc_name not in self.npc_memories or not self.npc_memories[npc_name]:
            return []

        entries = self.npc_memories[npc_name]
        texts = [e["text"] for e in entries]

        # If no query, return last few
        if query is None:
            return texts[-top_k:]

        # Semantic recall using prebuilt FAISS index
        index = self.npc_indices.get(npc_name)
        if index is None or index.ntotal == 0:
            return texts[-top_k:]

        query_emb = np.array([embed_text(query)], dtype="float32")
        scores, indices = index.search(query_emb, top_k)

        return [texts[i] for i in indices[0] if 0 <= i < len(texts)]

    def get_all_interactions(self, npc_name: str):
        """Fetch all persisted NPC interactions from MongoDB."""
        docs = self.collection.find({"npc_name": npc_name})
        return [doc["interaction"] for doc in docs]
