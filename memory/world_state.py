from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB_NAME, WORLD_STATE_COLLECTION


class WorldState:
    """
    Tracks significant world events across the entire campaign:
    locations visited, items found, and key decisions made.

    This context is fed back into the prompt each turn so the LLM
    maintains narrative consistency without relying on raw conversation history.
    """

    def __init__(self):
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        self.collection = db[WORLD_STATE_COLLECTION]

    def log_event(self, event_type: str, name: str = "", detail: str = ""):
        """
        Record a world event.
        event_type: "location" | "item" | "decision" | "enemy_defeated"
        """
        self.collection.insert_one({
            "type": event_type,
            "name": name,
            "detail": detail,
        })

    def get_visited_locations(self) -> list:
        docs = self.collection.find({"type": "location"}, {"name": 1})
        seen = set()
        locations = []
        for d in docs:
            loc = d.get("name", "").strip()
            if loc and loc not in seen:
                seen.add(loc)
                locations.append(loc)
        return locations

    def get_collected_items(self) -> list:
        docs = self.collection.find({"type": "item"}, {"name": 1})
        seen = set()
        items = []
        for d in docs:
            item = d.get("name", "").strip()
            if item and item not in seen:
                seen.add(item)
                items.append(item)
        return items

    def get_key_decisions(self, limit: int = 5) -> list:
        docs = list(
            self.collection.find({"type": "decision"}, {"detail": 1})
            .sort("_id", -1)
            .limit(limit)
        )
        return [d["detail"] for d in reversed(docs)]

    def get_context(self) -> str:
        """Return a formatted world state block for injection into the LLM prompt."""
        locations = self.get_visited_locations()
        items = self.get_collected_items()
        decisions = self.get_key_decisions()

        parts = []
        if locations:
            parts.append(f"Visited Locations: {', '.join(locations[-8:])}")
        if items:
            parts.append(f"Items Found: {', '.join(items)}")
        if decisions:
            parts.append("Key Decisions:\n" + "\n".join(f"- {d}" for d in decisions))

        return "\n".join(parts) if parts else "No world events recorded yet."

    def count(self) -> int:
        return self.collection.count_documents({})
