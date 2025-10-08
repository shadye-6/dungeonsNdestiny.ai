# utils/config.py

import os

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyB3iUURQxuOVnyDIKTPnLn0KR5kPdcGLKs")

# --- Model Settings ---
MODEL_NAME = "gemini-2.5-flash"
MAX_TURNS_WORKING_MEMORY = 5  # short-term memory
TOP_K_RETRIEVAL = 3           # number of relevant memories to retrieve

# --- Memory Storage ---
WORLD_STATE_PATH = "storage/world_state.json"
MEMORY_INDEX_PATH = "storage/memory_index.pkl"

# --- Logging ---
LOG_LEVEL = "INFO"
