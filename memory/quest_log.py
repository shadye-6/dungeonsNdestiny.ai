from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB_NAME, QUEST_COLLECTION, REWARD_COLLECTION

class QuestLog:
    def __init__(self):
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        self.collection = db[QUEST_COLLECTION]
        self.rewards = db[REWARD_COLLECTION]

    def get_active_quest(self):
        """Return the active quest (progress_status < 10 and not abandoned)."""
        return self.collection.find_one({"active": True, "completed": False, "abandoned": False})

    def add_quest(self, quest_name, summary, reward):
        """Add a new quest only if no active quest exists."""
        if self.get_active_quest():
            return None  # Cannot accept a new quest while one is active

        quest_data = {
            "quest_name": quest_name,
            "summary": summary,
            "progress_status": 1,           # 1-10
            "progress_summary": "Quest accepted.",
            "reward": reward,
            "active": True,
            "completed": False,
            "reward_collected": False,
            "abandoned": False
        }
        self.collection.insert_one(quest_data)
        return quest_data

    def update_progress(self, increment=1, new_summary=None):
        quest = self.get_active_quest()
        if not quest:
            return None

        new_status = min(10, quest["progress_status"] + increment)
        updates = {"$set": {"progress_status": new_status}}
        if new_summary:
            updates["$set"]["progress_summary"] = new_summary

        if new_status >= 10:
            updates["$set"].update({"completed": True, "active": False})
            self.collection.update_one({"_id": quest["_id"]}, updates)
            self._issue_reward(quest)
        else:
            self.collection.update_one({"_id": quest["_id"]}, updates)

    def abandon_quest(self):
        """Mark the active quest as abandoned permanently."""
        quest = self.get_active_quest()
        if not quest:
            return
        self.collection.update_one(
            {"_id": quest["_id"]},
            {"$set": {"active": False, "abandoned": True}}
        )

    def _issue_reward(self, quest):
        if quest.get("reward_collected"):
            return
        reward_data = {
            "quest_name": quest["quest_name"],
            "reward": quest["reward"],
            "description": f"Reward from quest '{quest['quest_name']}'"
        }
        self.rewards.insert_one(reward_data)
        self.collection.update_one(
            {"_id": quest["_id"]},
            {"$set": {"reward_collected": True}}
        )

    def get_rewards_context(self):
        """Return all obtained rewards as a string for prompt context."""
        rewards = list(self.rewards.find({}))
        if not rewards:
            return ""
        return "\n".join([f"- {r['reward']} ({r['description']})" for r in rewards])
