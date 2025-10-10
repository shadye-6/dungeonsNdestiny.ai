# 🔮 Dungeons N Destiny 

An AI-driven Dungeon Master that delivers **persistent, interactive storytelling** with both short-term and long-term memory, enabling consistent, evolving gameplay across sessions.

---

## 🧭 Project Overview

This project implements an **AI Dungeon Master** capable of:
- Remembering past events, player choices, and characters.
- Maintaining narrative consistency across ~100 turns. (can be scaled to 500).
- Managing evolving quests and NPC interactions.
- Using a hybrid memory architecture with both short-term and persistent recall.

---

## ⚙️ Architecture Summary

| Component | Description |
|------------|-------------|
| **Working Memory** | Short-term (≈5 turns) memory for immediate context using a deque. |
| **Persistent Memory** | Long-term (≈100 turns) semantic recall using FAISS (vector similarity) + MongoDB storage. |
| **LLM Engine** | Uses Gemini API (or sentence-transformers locally) for narrative generation and embeddings. |
| **Summarizer** | Compresses DM responses before saving to long-term memory. |
| **Quest & NPC Modules** | Structured JSON extraction and persistence for NPCs, quests, and rewards. |

---

## 📦 Requirements

- Python 3.10+
- MongoDB (local or remote)
- Dependencies:

```bash
pip install google-generativeai sentence-transformers faiss-cpu pymongo numpy tqdm
```

---

## 🔑 Environment Variables

| Variable | Description |
|-----------|-------------|
| `MONGO_URI` | MongoDB connection string (`mongodb://localhost:27017`) |
| `EMBEDDING_BACKEND` | `gemini` or `sentence` |
| `GEMINI_API_KEY` | Required for Gemini backend |

---

## 🚀 How to Run

```bash
# 1. Clone repo
git clone https://github.com/shadye-6/dungeonsNdestiny.ai
cd dungeonmaster.ai-main

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt   # or use commands above

# 4. Start MongoDB (Docker example)
docker run -d -p 27017:27017 mongo:6.0

# 5. Run
export MONGO_URI="mongodb://localhost:27017"
export EMBEDDING_BACKEND="sentence"
python main.py
```

---

## 🧠 System Flow

1. Player input is received in CLI.
2. Recent turns are fetched from **WorkingMemory**.
3. Relevant long-term memories are retrieved from FAISS via semantic search.
4. `prompt_builder.py` constructs the prompt using both.
5. LLM generates narrative + JSON (NPCs, quests).
6. `npc_and_quest_parser.py` extracts structured data.
7. Summary is generated and stored back into PersistentMemory.
8. NPC and Quest logs update automatically.

---

## 🧩 Features

- Two-tier memory (short-term + long-term)
- Persistent world and NPC memory via MongoDB
- Quest tracking and reward logging
- Modular, interpretable design
- Supports multiple LLM/embedding backends

---

## 📽️ Demo Recording
```
Demo Recording: https://drive.google.com/your-demo-link
```

## 📊 Evaluation Mapping

| Criteria | Implementation |
|-----------|----------------|
| **Gameplay & Robustness** | Interactive narrative loop (`main.py`) |
| **Short-Term Recall** | `WorkingMemory` |
| **Long-Term Recall** | `PersistentMemory` (Mongo + FAISS) |
| **Architecture & Code** | Modular, documented, reproducible |
| **Presentation & Report** | README + `report.pdf` |
| **Bonus** | NPC & Quest memory modules |

---

## 👥 Authors
Developed by **Team kawAI**  
Contributors: *[Pragadeesh SK, Dakshin]*
