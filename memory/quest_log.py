from pymongo import MongoClient
from utils.config import MONGO_URI, MONGO_DB_NAME, QUEST_COLLECTION, REWARD_COLLECTION

class QuestLog:
    def __init__(self):
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        self.collection = db[QUEST_COLLECTION]
        self.rewards = db[REWARD_COLLECTION]

    def get_active_quests(self):
        """Return all active quests."""
        return list(self.collection.find({"active": True, "completed": False, "abandoned": False}))

    def get_active_quest_by_name(self, quest_name):
        """Return a specific active quest by name."""
        return self.collection.find_one({"quest_name": quest_name, "active": True, "completed": False, "abandoned": False})

    def add_quest(self, quest_name, summary, reward, mandatory=False):
        """Add a new quest."""
        quest_data = {
            "quest_name": quest_name,
            "summary": summary,
            "progress_status": 1,           # 1-10
            "progress_summary": "Quest accepted.",
            "reward": reward,
            "active": True,
            "completed": False,
            "reward_collected": False,
            "abandoned": False,
            "mandatory": mandatory          # True = main story, False = optional
        }
        self.collection.insert_one(quest_data)
        return quest_data

    def update_progress(self, quest_name, increment=1, new_summary=None):
        quest = self.collection.find_one({
            "quest_name": quest_name,
            "abandoned": False
        })
        if not quest:
            return None

        new_status = min(10, quest.get("progress_status", 1) + increment)
        updates = {
            "$set": {
                "progress_status": new_status,
                "progress_summary": new_summary or quest.get("progress_summary", "")
            }
        }

        if new_status >= 10:
            updates["$set"].update({
                "completed": True,
                "active": False
            })
        self.collection.update_one({"_id": quest["_id"]}, updates)
        updated_quest = self.collection.find_one({"_id": quest["_id"]})

        if updated_quest["completed"] and not updated_quest.get("reward_collected", False):
            self._issue_reward(updated_quest)

        return updated_quest


    def abandon_all_quests(self):
        """Abandon all active quests."""
        self.collection.update_many(
            {"active": True, "completed": False},
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
