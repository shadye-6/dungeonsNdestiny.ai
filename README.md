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

## Requirements

- Python 3.10+
- MongoDB (local or Atlas)

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key
MONGODB_PASSWORD=your_mongodb_password
EMBEDDING_BACKEND=sentence   # or "gemini"
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required) |
| `MONGODB_PASSWORD` | MongoDB Atlas password (required) |
| `EMBEDDING_BACKEND` | `sentence` (default, local) or `gemini` (API-based) |

---

## Running

### CLI

```bash
python main.py
```

### Web UI (Streamlit)

```bash
streamlit run web_app/streamlit_app.py
```

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
