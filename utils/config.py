import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI_PASSWORD = os.getenv("MONGODB_PASSWORD")

MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS_WORKING_MEMORY = 5
TOP_K_RETRIEVAL = 5

MONGO_URI = (
    f"mongodb+srv://shadye:{MONGO_URI_PASSWORD}"
    "@textembeddings.lxxktdc.mongodb.net/"
    "?retryWrites=true&w=majority&appName=TextEmbeddings"
)

MONGO_DB_NAME = "dungeon_master"
MONGO_COLLECTION_NAME = "memories"
CHARACTER_COLLECTION = "characters"
QUEST_COLLECTION = "quests"
REWARD_COLLECTION = "rewards"
WORLD_STATE_COLLECTION = "world_state"
SESSION_COLLECTION = "sessions"
