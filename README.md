# Dungeons N Destiny

An AI-driven Dungeon Master delivering **persistent, interactive storytelling** with a multi-tier memory architecture. The system maintains narrative coherence across hundreds of turns by combining short-term conversation context, long-term semantic recall, NPC character memory, world state tracking, and a dynamic quest log.

---

## Architecture

```
Player Input
     │
     ▼
┌─────────────────────────────────────────────────┐
│              Prompt Builder                      │
│  Working Memory  │  Persistent Memory (RAG)      │
│  (last 5 turns)  │  (FAISS + MongoDB, top-5)     │
│                  │  World State Context          │
│                  │  Active Quests & Rewards      │
└─────────────────────────────────────────────────┘
     │
     ▼
   Gemini LLM  (gemini-2.5-flash)
     │
     ▼
  Narrative + JSON {npcs, quests, world_events}
     │
     ├── Summarizer → PersistentMemory (MongoDB + FAISS)
     │                WorkingMemory (in-memory deque)
     │
     ├── NPC Parser → CharacterMemory (per-NPC FAISS + MongoDB)
     │
     ├── Quest Parser → QuestLog (MongoDB)
     │                  Rewards (MongoDB)
     │
     └── World Event Parser → WorldState (MongoDB)
```

| Module | Description |
|---|---|
| `memory/working.py` | Short-term deque — last 5 turn summaries for immediate context |
| `memory/persistent.py` | Long-term semantic recall — FAISS over MongoDB-stored embeddings (up to 500 turns) |
| `memory/character_memory.py` | Per-NPC FAISS index — NPCs remember past interactions and evolve accordingly |
| `memory/quest_log.py` | Dynamic quest log — tracks progress (1–10), completion, rewards, mandatory vs optional |
| `memory/world_state.py` | World event log — visited locations, collected items, key decisions fed back into every prompt |
| `memory/summarizer.py` | Compresses DM responses before storing to long-term memory |
| `memory/embeddings.py` | Embedding backend — `sentence-transformers` (default) or Gemini `text-embedding-004` |
| `llm/story_engine.py` | Gemini API wrapper with error recovery |
| `llm/prompt_builder.py` | Assembles the full DM prompt from all memory layers |
| `memory/npc_and_quest_parser.py` | Extracts structured JSON (NPCs, quests, world events) from LLM output |

---

## Setup Guide

### Prerequisites

- Python 3.10 or later
- Git

### 1. Clone the repository

```bash
git clone https://github.com/shadye-6/dungeonsNdestiny.ai.git
cd dungeonsNdestiny.ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> The first run will download the `all-MiniLM-L6-v2` sentence-transformer model (~90 MB). This only happens once and is cached locally.

### 4. Get a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in and click **Create API key**
3. Copy the key — you'll need it in the next step

### 5. Configure environment variables

Create a file named `.env` in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_PASSWORD=your_mongodb_password_here
EMBEDDING_BACKEND=sentence
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for LLM generation and (optionally) embeddings |
| `MONGODB_PASSWORD` | Yes | Password for the shared MongoDB Atlas instance |
| `EMBEDDING_BACKEND` | No | `sentence` (default, fully local) or `gemini` (uses Gemini embedding API) |

> **MongoDB:** The project connects to a shared MongoDB Atlas cluster. The `MONGODB_PASSWORD` for that cluster is provided separately by the team. Alternatively, to use a local MongoDB instance, replace the `MONGO_URI` in `utils/config.py` with `mongodb://localhost:27017`.

### 6. Run

**Command-line interface:**

```bash
python main.py
```

**Web UI (Streamlit):**

```bash
streamlit run web_app/streamlit_app.py
```

Then open `http://localhost:8501` in your browser.

---

## Features

- **Two-tier memory**: short-term deque (5 turns) + long-term semantic search (FAISS/RAG, up to 500 turns)
- **NPC character memory**: each NPC maintains a FAISS-indexed interaction history; re-encounters are contextually aware
- **Dynamic quest log**: mandatory main-story quests tracked automatically; optional side quests prompt the player for accept/decline
- **World state tracking**: locations, items, and key decisions logged and fed into every prompt for narrative consistency
- **Dual interface**: CLI for raw gameplay; Streamlit web UI with sidebar panels for quests, NPC history, world state, and memory stats
- **Session persistence**: Streamlit chat history survives browser refresh (stored in MongoDB)
- **Stable across 30+ turns**: summarizer + error recovery ensure the game loop never crashes

---

## Demo

[Demo Recording](https://drive.google.com/file/d/1cK5EMd80leFlOht1cnNjoOcAEAxI1EdY/view?usp=drive_link)

---

## Authors

Developed by **Team kawAI** — Pragadeesh S K, Dakshin
