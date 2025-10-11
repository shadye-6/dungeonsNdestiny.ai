import os
from dotenv import load_dotenv
import streamlit as st
load_dotenv()

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
MONGO_URI_PASSWORD = st.secrets.get("MONGODB_PASSWORD", "")

MODEL_NAME = "gemini-2.5-flash-lite"
MAX_TURNS_WORKING_MEMORY = 5  # short-term memory
TOP_K_RETRIEVAL = 3           # number of relevant memories to retrieve

WORLD_STATE_PATH = "storage/world_state.json"
MEMORY_INDEX_PATH = "storage/memory_index.pkl"

LOG_LEVEL = "INFO"

MONGO_URI = f"mongodb+srv://shadye:{MONGO_URI_PASSWORD}@textembeddings.lxxktdc.mongodb.net/?retryWrites=true&w=majority&appName=TextEmbeddings"

MONGO_DB_NAME = "dungeon_master"
MONGO_COLLECTION_NAME = "memories"

MEMORY_COLLECTION = "memories"
CHARACTER_COLLECTION = "characters"
QUEST_COLLECTION = "quests"
REWARD_COLLECTION = "rewards"

