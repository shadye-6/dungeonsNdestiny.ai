import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from pymongo import MongoClient

from memory.persistent import PersistentMemory
from memory.working import WorkingMemory
from memory.character_memory import CharacterMemory
from memory.quest_log import QuestLog
from memory.world_state import WorldState
from memory.npc_and_quest_parser import parse_llm_output
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt
from utils.config import MONGO_URI, MONGO_DB_NAME


# ---- Secret resolution -------------------------------------------------
def get_secret(key: str) -> str:
    value = os.getenv(key)
    if value is None and hasattr(st, "secrets"):
        value = st.secrets.get(key)
    if value is None:
        raise ValueError(f"Secret '{key}' not found in environment or st.secrets")
    os.environ[key] = value  # propagate to downstream modules
    return value


try:
    get_secret("GEMINI_API_KEY")
    get_secret("MONGODB_PASSWORD")
except ValueError as e:
    st.error(f"⚠️ Missing required secret: {e}. Set it in your .env file or Streamlit secrets.")
    st.stop()

try:
    get_secret("EMBEDDING_BACKEND")
except ValueError:
    pass  # defaults to "sentence" via os.getenv fallback in embeddings.py


# ---- Cached resource init ----------------------------------------------
@st.cache_resource
def get_persistent_mem():
    return PersistentMemory()


@st.cache_resource
def get_character_mem():
    return CharacterMemory()


@st.cache_resource
def get_quest_log():
    return QuestLog()


@st.cache_resource
def get_world_state():
    return WorldState()


@st.cache_resource
def get_sessions_col():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB_NAME]["sessions"]


# ---- Session history persistence ---------------------------------------
def save_history(history: list):
    get_sessions_col().replace_one(
        {"session_id": "default"},
        {"session_id": "default", "history": history},
        upsert=True
    )


def load_history() -> list:
    doc = get_sessions_col().find_one({"session_id": "default"})
    return doc.get("history", []) if doc else []


# ---- Streamlit page config ---------------------------------------------
st.set_page_config(page_title="Dungeons N Destiny", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🛡️ Dungeons N Destiny: The Shattered Crown")
st.markdown("Describe your action below. The Dungeon Master will respond.")

# ---- Session state init ------------------------------------------------
if "history_loaded" not in st.session_state:
    st.session_state.history = load_history()
    st.session_state.history_loaded = True

if "working_mem" not in st.session_state:
    wm = WorkingMemory(limit=5)
    wm.load_from(get_persistent_mem().get_recent_memories(5))
    st.session_state.working_mem = wm

if "turn" not in st.session_state:
    st.session_state.turn = 0

if "pending_quests" not in st.session_state:
    st.session_state.pending_quests = []

if "npc_history" not in st.session_state:
    st.session_state.npc_history = {}


# ---- Layout ------------------------------------------------------------
col_main, col_sidebar = st.columns([3, 1])

# ---- Quest offer prompt (shown before input when there are pending quests) ---
if st.session_state.pending_quests:
    with col_main:
        st.markdown("---")
        st.markdown("### 🗺️ Quest Offer")
        to_remove = []
        for i, quest in enumerate(st.session_state.pending_quests):
            with st.container():
                st.markdown(f"**{quest['quest_name']}**")
                st.caption(quest.get("description", ""))
                c1, c2 = st.columns([1, 1])
                if c1.button("✅ Accept", key=f"accept_{i}_{quest['quest_name']}"):
                    get_quest_log().add_quest(
                        quest_name=quest["quest_name"],
                        summary=quest["description"],
                        reward=quest.get("reward", "unknown reward"),
                        mandatory=False
                    )
                    st.session_state.history.append(f"*Quest accepted: {quest['quest_name']}*")
                    to_remove.append(i)
                if c2.button("❌ Decline", key=f"decline_{i}_{quest['quest_name']}"):
                    st.session_state.history.append(f"*Quest declined: {quest['quest_name']}*")
                    to_remove.append(i)
        for i in reversed(to_remove):
            st.session_state.pending_quests.pop(i)
        if to_remove:
            save_history(st.session_state.history)
            st.rerun()
        st.markdown("---")

# ---- Player input ------------------------------------------------------
with col_main:
    with st.form("player_form", clear_on_submit=True):
        player_input = st.text_input(
            "Your action:",
            placeholder="e.g. I approach the hooded figure near the fountain...",
        )
        submitted = st.form_submit_button("Submit")

# ---- Handle submission -------------------------------------------------
if submitted and player_input.strip():
    pm = get_persistent_mem()
    cm = get_character_mem()
    ql = get_quest_log()
    ws = get_world_state()

    npc_name = None
    if "talk to" in player_input.lower():
        npc_name = player_input.split("talk to")[-1].strip().title()

    working_context = st.session_state.working_mem.get_context()
    retrieved_context = "\n".join(pm.retrieve(player_input, top_k=5))
    world_state_context = ws.get_context()

    if npc_name:
        npc_history = "\n".join(cm.get_memory(npc_name, query=player_input, top_k=5))
        if npc_history:
            retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"

    active_quests = ql.get_active_quests()
    quest_context = ""
    if active_quests:
        quest_context = "\n".join([
            f"- {q['quest_name']} (Progress: {q['progress_status']}/10)\n  Summary: {q.get('progress_summary', q['summary'])}"
            for q in active_quests
        ])

    reward_context = ql.get_rewards_context()

    prompt = build_prompt(
        working_context + (f"\nActive Quests:\n{quest_context}" if quest_context else ""),
        retrieved_context,
        player_input,
        reward_context=reward_context,
        world_state_context=world_state_context
    )

    response = generate_response(prompt)
    dm_text, npcs, quests, world_events = parse_llm_output(response)

    st.session_state.turn += 1
    st.session_state.history.append(f"**You (Turn {st.session_state.turn}):** {player_input}")
    st.session_state.history.append(f"**DM:** {dm_text}")

    # Log world events from this turn
    for event in world_events:
        ws.log_event(event["type"], event.get("name", ""), event["detail"])

    # Persist memory
    summary = summarize_for_memory(dm_text)
    summary_emb = embed_text(summary)
    pm.add_memory(summary, summary_emb)
    st.session_state.working_mem.push(summary)

    # NPC character memory
    for npc in npcs:
        npc_n = npc.get("npc_name", "")
        context = npc.get("context", "")
        if npc_n and context:
            cm.add_interaction(npc_n, context)
            if npc_n in st.session_state.npc_history:
                st.session_state.npc_history[npc_n] += f"\n{context}"
            else:
                st.session_state.npc_history[npc_n] = context

    # Quests — mandatory auto-add, optional go into pending list
    for quest in quests:
        quest_name = quest["quest_name"]
        is_mandatory = quest.get("mandatory", False)
        active = ql.get_active_quest_by_name(quest_name)

        if active is not None:
            ql.update_progress(quest_name, increment=1, new_summary=quest["description"])
        elif not ql.quest_exists_by_name(quest_name):
            if is_mandatory:
                ql.add_quest(
                    quest_name=quest_name,
                    summary=quest["description"],
                    reward=quest.get("reward", "unknown reward"),
                    mandatory=True
                )
                st.session_state.history.append(f"*📜 Main quest added: {quest_name}*")
            else:
                already_pending = any(q["quest_name"] == quest_name for q in st.session_state.pending_quests)
                if not already_pending:
                    st.session_state.pending_quests.append(quest)
        # else: quest already completed or abandoned — skip

    # Abandon quest via text
    if "abandon quest" in player_input.lower():
        ql.abandon_all_quests()
        st.session_state.history.append("*🛑 All active quests abandoned.*")

    save_history(st.session_state.history)
    st.rerun()

# ---- Main chat display -------------------------------------------------
with col_main:
    st.markdown("### 💬 Story")
    if st.session_state.history:
        for msg in reversed(st.session_state.history):
            st.markdown(msg)
    else:
        st.markdown("*Type your first action to begin the adventure...*")

# ---- Sidebar -----------------------------------------------------------
with col_sidebar:
    st.markdown("### 📜 Active Quests")
    active = get_quest_log().get_active_quests()
    if active:
        for q in active:
            progress_pct = int((q["progress_status"] / 10) * 100)
            st.markdown(f"**{q['quest_name']}**")
            st.progress(progress_pct)
            st.caption(q.get("progress_summary", q["summary"]))
    else:
        st.markdown("*No active quests.*")

    st.markdown("---")
    st.markdown("### 🗣️ NPCs Encountered")
    if st.session_state.npc_history:
        for npc, history in st.session_state.npc_history.items():
            with st.expander(npc):
                st.text(history[-300:] if len(history) > 300 else history)
    else:
        st.markdown("*No NPC interactions yet.*")

    st.markdown("---")
    st.markdown("### 🌍 World State")
    ws = get_world_state()
    locations = ws.get_visited_locations()
    items = ws.get_collected_items()
    if locations:
        st.markdown("**Locations visited:**")
        st.caption(", ".join(locations[-6:]))
    if items:
        st.markdown("**Items found:**")
        st.caption(", ".join(items))
    if not locations and not items:
        st.markdown("*No world events recorded yet.*")

    st.markdown("---")
    st.markdown("### 🧠 Memory Stats")
    pm = get_persistent_mem()
    st.metric("Turn", st.session_state.turn)
    st.metric("Memories stored", pm.count())
    st.metric("World events", ws.count())
    st.metric("Short-term window", len(st.session_state.working_mem))

    st.markdown("---")
    if st.button("🛑 Abandon All Quests"):
        get_quest_log().abandon_all_quests()
        st.session_state.history.append("*🛑 All active quests abandoned.*")
        save_history(st.session_state.history)
        st.rerun()

    if st.button("🗑️ Clear Session History"):
        st.session_state.history = []
        save_history([])
        st.rerun()
