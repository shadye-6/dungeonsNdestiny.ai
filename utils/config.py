import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Model Settings ---
MODEL_NAME = "gemini-2.5-flash-lite"
MAX_TURNS_WORKING_MEMORY = 5  # short-term memory
TOP_K_RETRIEVAL = 3           # number of relevant memories to retrieve

# --- Memory Storage ---
WORLD_STATE_PATH = "storage/world_state.json"
MEMORY_INDEX_PATH = "storage/memory_index.pkl"


# --- Logging ---
LOG_LEVEL = "INFO"

# utils/config.py

MONGO_URI = "mongodb+srv://shadye:QcI9sBf7YotyPV3O@textembeddings.lxxktdc.mongodb.net/?retryWrites=true&w=majority&appName=TextEmbeddings"
MONGO_DB_NAME = "dungeon_master"
MONGO_COLLECTION_NAME = "memories"

# Collections
MEMORY_COLLECTION = "memories"
CHARACTER_COLLECTION = "characters"
QUEST_COLLECTION = "quests"
REWARD_COLLECTION = "rewards"

