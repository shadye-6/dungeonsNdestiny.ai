from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB_NAME, CHARACTER_COLLECTION

class CharacterMemory:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB_NAME]
        self.collection = self.db[CHARACTER_COLLECTION]

    def add_interaction(self, npc_name, context):
        """Add a new NPC interaction"""
        doc = {"npc_name": npc_name, "context": context}
        self.collection.insert_one(doc)

    def get_memory(self, npc_name):
        """Retrieve all previous interactions for an NPC"""
        docs = self.collection.find({"npc_name": npc_name})
        return [d["context"] for d in docs]
