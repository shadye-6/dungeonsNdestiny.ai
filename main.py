# main.py
from interface.cli import get_player_input, display_output
from memory.persistent import PersistentMemory
from memory.character_memory import CharacterMemory
from memory.quest_log import QuestLog
from memory.npc_and_quest_parser import parse_llm_output
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt

# Initialize systems
persistent_mem = PersistentMemory()
character_mem = CharacterMemory()
quest_log = QuestLog()

print("🛡️ AI Dungeon Master is ready! Type 'exit' to quit.")

while True:
    player_input = get_player_input()
    if player_input.lower() in ["exit", "quit"]:
        print("Exiting AI Dungeon Master...")
        break

    # Simple heuristic for NPC detection
    npc_name = None
    if "talk to" in player_input.lower():
        npc_name = player_input.split("talk to")[-1].strip().title()

    # 🧠 Retrieve working memory (last 5 summaries)
    working_context = "\n".join(persistent_mem.get_recent_memories(5))

    # 🗃️ Retrieve persistent memory for long-term context (last 100 for FAISS)
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=100))

    # Include NPC-specific history
    if npc_name:
        npc_history = "\n".join(character_mem.get_memory(npc_name))
        if npc_history:
            retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"

    # Quest context (only one active quest)
    active_quest = quest_log.get_active_quest()
    quest_context = ""
    if active_quest:
        quest_context = (
            f"- {active_quest['quest_name']} (Progress: {active_quest['progress_status']}/10)\n"
            f"Summary: {active_quest.get('summary', '')}"
        )

    # Rewards context
    reward_context = quest_log.get_rewards_context()

    # Build LLM prompt
    prompt = build_prompt(
        working_context + f"\nActive Quest:\n{quest_context}",
        retrieved_context,
        player_input,
        reward_context=reward_context
    )

    # Generate DM response
    response = generate_response(prompt)
    dm_text, npcs, quests = parse_llm_output(response)
    display_output(dm_text)

    # Summarize and persist story context
    summary = summarize_for_memory(dm_text)
    summary_emb = embed_text(summary)
    persistent_mem.add_memory(summary, summary_emb)

    # Update NPC memory
    for npc in npcs:
        character_mem.add_interaction(npc["npc_name"], npc["context"])

    # Handle quests

    for quest in quests:
        # Accept new quest only if no active quest exists
        if quest_log.get_active_quest() is None and quest["progress"].lower() == "started":
            quest_log.add_quest(
                quest_name=quest["quest_name"],
                summary=quest["description"],
                reward=quest.get("reward", "unknown reward")  # <-- fixed keyword
            )
            display_output(f"🗺️ New Quest Accepted: {quest['quest_name']}")

        # Update current quest progress
        elif quest_log.get_active_quest() is not None:
            quest_log.update_progress(increment=1, new_summary=quest["description"])
            display_output(f"📜 Quest Progress Updated: {quest['quest_name']}")


    # Abandon quest mid-way
    if "abandon quest" in player_input.lower():
        quest_log.abandon_quest()
        display_output("🛑 Quest abandoned. No rewards received.")
