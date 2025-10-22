import os
from dotenv import load_dotenv
import streamlit as st
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from interface.cli import get_player_input, display_output
from memory.persistent import PersistentMemory
from memory.character_memory import CharacterMemory
from memory.quest_log import QuestLog
from memory.npc_and_quest_parser import parse_llm_output
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt

# ---- Load environment variables ----
load_dotenv()

def get_secret(key: str):
    value = os.getenv(key)
    if value is None:
        value = st.secrets.get(key) if hasattr(st, "secrets") else None
    if value is None:
        raise ValueError(f"Secret '{key}' not found!")
    return value

# ---- Secrets ----
EMBEDDING_BACKEND = get_secret("EMBEDDING_BACKEND")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
MONGODB_PASSWORD = get_secret("MONGODB_PASSWORD")

# ---- Initialize memories and quest log ----
persistent_mem = PersistentMemory()
character_mem = CharacterMemory()
quest_log = QuestLog()

# ---- Streamlit UI ----
st.set_page_config(page_title="Dungeons N Destiny", layout="wide")
st.title("🛡️ Dungeons N Destiny: The Shattered Crown")
st.markdown("Type your actions below. The AI Dungeon Master will respond to your adventure!")

# ---- Session state ----
if "history" not in st.session_state:
    st.session_state.history = []
if "quests" not in st.session_state:
    st.session_state.quests = []
if "npc_history" not in st.session_state:
    st.session_state.npc_history = {}

# ---- Layout columns ----
col1, col2 = st.columns([3, 2])

# ---- Input box at the top ----
with col1:
    player_input = st.text_input("Your action:", key="player_input")
    submit = st.button("Submit")

# ---- Handle player input ----
if submit and player_input:

    # Detect NPC interaction
    npc_name = None
    if "talk to" in player_input.lower():
        npc_name = player_input.split("talk to")[-1].strip().title()

    # Working memory: last 5 summaries
    working_context = "\n".join(persistent_mem.get_recent_memories(5))
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=500))

    # Include NPC previous interactions
    if npc_name:
        npc_history = "\n".join(character_mem.get_memory(npc_name))
        if npc_history:
            retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"
            st.session_state.npc_history[npc_name] = npc_history

    # Quest context for prompt
    active_quests = quest_log.get_active_quests()
    quest_context_text = ""
    if active_quests:
        quest_context_text = "\n".join([
            f"- {q['quest_name']} (Progress: {q['progress_status']}/10)\n  Summary: {q.get('progress_summary', q['summary'])}"
            for q in active_quests
        ])
        st.session_state.quests = active_quests

    # Rewards context
    reward_context = quest_log.get_rewards_context()

    # Build prompt
    prompt = build_prompt(
        working_context + f"\nActive Quests:\n{quest_context_text}",
        retrieved_context,
        player_input,
        reward_context=reward_context
    )

    # Generate DM response
    response = generate_response(prompt)
    dm_text, npcs, quests = parse_llm_output(response)

    # ---- Update chat and memories ----
    st.session_state.history.append(f"**You:** {player_input}")
    st.session_state.history.append(f"**DM:** {dm_text}")  # Only DM text

    # Update NPC memory
    for npc in npcs:
        character_mem.add_interaction(npc["npc_name"], npc["context"])
        if npc["npc_name"] in st.session_state.npc_history:
            st.session_state.npc_history[npc["npc_name"]] += f"\n{npc['context']}"
        else:
            st.session_state.npc_history[npc["npc_name"]] = npc["context"]

    # Update quest memory
    for quest in quests:
        quest_name = quest["quest_name"]
        is_mandatory = quest.get("mandatory", False)

        if quest_log.get_active_quest_by_name(quest_name) is None:
            quest_log.add_quest(
                quest_name=quest_name,
                summary=quest["description"],
                reward=quest.get("reward", "unknown reward"),
                mandatory=is_mandatory
            )
        else:
            quest_log.update_progress(
                quest_name,
                increment=1,
                new_summary=quest["description"]
            )

    # Summarize and persist DM text
    summary = summarize_for_memory(dm_text)
    summary_emb = embed_text(summary)
    persistent_mem.add_memory(summary, summary_emb)

# ---- Display chat in left column (below input) ----
with col1:
    st.markdown("### 💬 Chat (Latest on Top)")
    for msg in reversed(st.session_state.history):
        st.markdown(msg)

# ---- Display quests & NPCs in right column ----
with col2:
    st.markdown("### 📜 Active Quests")
    if st.session_state.quests:
        for q in st.session_state.quests:
            st.markdown(f"**{q['quest_name']}** (Progress: {q['progress_status']}/10)")
            st.text(f"Summary: {q.get('progress_summary', q['summary'])}")
    else:
        st.markdown("_No active quests._")

    st.markdown("### 🗣️ NPC Interactions")
    if st.session_state.npc_history:
        for npc, history in st.session_state.npc_history.items():
            st.markdown(f"**{npc}**")
            st.text(history)
    else:
        st.markdown("_No NPC interactions yet._")
