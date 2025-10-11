import streamlit as st
from memory.persistent import PersistentMemory
from memory.character_memory import CharacterMemory
from memory.quest_log import QuestLog
from memory.npc_and_quest_parser import parse_llm_output
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt

st.markdown('<style>' + open("web_app/assets/style.css").read() + '</style>', unsafe_allow_html=True)


# Initialize persistent objects only once (avoid re-init per rerun)
if "persistent_mem" not in st.session_state:
    st.session_state.persistent_mem = PersistentMemory()
    st.session_state.character_mem = CharacterMemory()
    st.session_state.quest_log = QuestLog()
    st.session_state.chat_history = []  # [(player_input, dm_output)]

persistent_mem = st.session_state.persistent_mem
character_mem = st.session_state.character_mem
quest_log = st.session_state.quest_log

# --- Streamlit UI ---
st.title("🛡️ AI Dungeon Master: The Shattered Crown")
st.markdown("""
Welcome to the world of **Eryndor**!  
Explore, fight, talk, and uncover the mystery of *The Shattered Crown*.

### ⚔️ General Rules:
- Each turn, type your action (explore, talk, fight, use item, etc.).
- Side quests can be accepted or declined.
- Main quests are mandatory for story progression.
- Type **"abandon quest"** to give up all optional quests.
""")

# Player input box
player_input = st.text_input("Your action:", key="player_input")

if st.button("Submit Turn"):
    if player_input.strip() == "":
        st.warning("Please enter an action.")
    else:
        npc_name = None
        if "talk to" in player_input.lower():
            npc_name = player_input.split("talk to")[-1].strip().title()

        # Working & retrieved memory
        working_context = "\n".join(persistent_mem.get_recent_memories(5))
        retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=100))

        # NPC-specific memory
        if npc_name:
            npc_history = "\n".join(character_mem.get_memory(npc_name))
            if npc_history:
                retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"

        # Active quests + rewards
        active_quests = quest_log.get_active_quests()
        quest_context = ""
        if active_quests:
            quest_context = "\n".join([
                f"- {q['quest_name']} (Progress: {q['progress_status']}/10) – {q.get('progress_summary', '')}"
                for q in active_quests
            ])
        reward_context = quest_log.get_rewards_context()

        # Build prompt
        prompt = build_prompt(
            working_context + f"\nActive Quests:\n{quest_context}",
            retrieved_context,
            player_input,
            reward_context
        )

        # Generate DM response
        response = generate_response(prompt)
        dm_text, npcs, quests = parse_llm_output(response)

        # Display DM text
        st.markdown(f"**🧙 Dungeon Master:** {dm_text}")

        # Summarize & save to persistent memory
        summary = summarize_for_memory(dm_text)
        summary_emb = embed_text(summary)
        persistent_mem.add_memory(summary, summary_emb)

        # NPC updates
        for npc in npcs:
            character_mem.add_interaction(npc["npc_name"], npc["context"])

        # Quest management
        for quest in quests:
            quest_name = quest["quest_name"]
            is_mandatory = quest.get("mandatory", False)

            if is_mandatory:
                if quest_log.get_active_quest_by_name(quest_name) is None:
                    quest_log.add_quest(
                        quest_name=quest_name,
                        summary=quest["description"],
                        reward=quest.get("reward", "unknown reward"),
                        mandatory=True
                    )
                    st.success(f"📜 Main Quest Added: {quest_name}")
                else:
                    quest_log.update_progress(
                        quest_name,
                        increment=1,
                        new_summary=quest["description"]
                    )
                    st.info(f"📜 Main Quest Progress Updated: {quest_name}")
            else:
                if quest_log.get_active_quest_by_name(quest_name) is None:
                    with st.expander(f"🗺️ Optional Quest: {quest_name}"):
                        st.markdown(f"**Description:** {quest['description']}")
                        accept = st.button(f"Accept '{quest_name}'?", key=quest_name)
                        if accept:
                            quest_log.add_quest(
                                quest_name=quest_name,
                                summary=quest["description"],
                                reward=quest.get("reward", "unknown reward"),
                                mandatory=False
                            )
                            st.success(f"✅ Optional Quest Accepted: {quest_name}")
                else:
                    quest_log.update_progress(
                        quest_name,
                        increment=1,
                        new_summary=quest["description"]
                    )
                    st.info(f"📜 Optional Quest Progress Updated: {quest_name}")

        # Abandon quest logic
        if "abandon quest" in player_input.lower():
            quest_log.abandon_all_quests()
            st.warning("🛑 All active quests abandoned. No rewards received.")

        # Update chat history
        st.session_state.chat_history.append((player_input, dm_text))

# --- Display Chat History ---
if st.session_state.chat_history:
    st.markdown("### 📖 Adventure Log")
    for turn, (player, dm) in enumerate(st.session_state.chat_history, start=1):
        st.markdown(f"**Turn {turn}:**")
        st.markdown(f"🧍‍♂️ **You:** {player}")
        st.markdown(f"🧙 **DM:** {dm}")
        st.markdown("---")
