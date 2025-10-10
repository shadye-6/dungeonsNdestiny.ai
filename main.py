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

print("🛡️ AI Dungeon Master is ready! Type 'start' to continue or 'exit' to quit.\n")

print("📜 General Rules:")
print("- Each turn, you (the player) provide input to interact with the world.")
print("- You may talk to NPCs, explore locations, solve puzzles, or accept quests.")
print("- Optional side quests can be accepted or declined; main storyline quests must be completed.")
print("- Your progress in quests, items obtained, and key choices affect the main storyline.")
print("- You can type 'abandon quest' to give up on optional quests (no rewards).")
print("- Have fun and immerse yourself in the world of 'The Shattered Crown'!\n")


while True:
    player_input = get_player_input()
    if player_input.lower() in ["exit", "quit"]:
        print("Exiting AI Dungeon Master...")
        break

    # Detect NPC interaction
    npc_name = None
    if "talk to" in player_input.lower():
        npc_name = player_input.split("talk to")[-1].strip().title()

    # Working memory: last 5 summaries
    working_context = "\n".join(persistent_mem.get_recent_memories(5))

    # Persistent memory for storyline and plot progression
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=100))

    # Include NPC-specific history
    if npc_name:
        npc_history = "\n".join(character_mem.get_memory(npc_name))
        if npc_history:
            retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"

    # Quest context
    active_quests = quest_log.get_active_quests()
    quest_context = ""
    if active_quests:
        quest_context = "\n".join([
            f"- {q['quest_name']} (Progress: {q['progress_status']}/10)\nSummary: {q.get('progress_summary', '')}"
            for q in active_quests
        ])

    # Rewards context
    reward_context = quest_log.get_rewards_context()

    # Build LLM prompt
    prompt = build_prompt(
        working_context + f"\nActive Quests:\n{quest_context}",
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
        quest_name = quest["quest_name"]
        is_mandatory = quest.get("mandatory", False)

        # --- Mandatory Main Storyline Quests ---
        if is_mandatory:
            if quest_log.get_active_quest_by_name(quest_name) is None:
                quest_log.add_quest(
                    quest_name=quest_name,
                    summary=quest["description"],
                    reward=quest.get("reward", "unknown reward"),
                    mandatory=True
                )
                display_output(f"📜 Main Quest Added: {quest_name}")
            else:
                quest_log.update_progress(
                    quest_name,
                    increment=1,
                    new_summary=quest["description"]
                )
                display_output(f"📜 Main Quest Progress Updated: {quest_name}")

        # --- Optional Side Quests ---
        else:
            # Only offer to accept if not already active
            if quest_log.get_active_quest_by_name(quest_name) is None:
                display_output(f"🗺️ Optional Quest Available: {quest_name}\nDescription: {quest['description']}")
                player_choice = get_player_input("Do you want to accept this quest? (yes/no) ").lower()
                if player_choice in ["yes", "y"]:
                    quest_log.add_quest(
                        quest_name=quest_name,
                        summary=quest["description"],
                        reward=quest.get("reward", "unknown reward"),
                        mandatory=False
                    )
                    display_output(f"✅ Optional Quest Accepted: {quest_name}")
                else:
                    display_output(f"❌ Optional Quest Declined: {quest_name}")
            else:
                quest_log.update_progress(
                    quest_name,
                    increment=1,
                    new_summary=quest["description"]
                )
                display_output(f"📜 Optional Quest Progress Updated: {quest_name}")

    # Abandon quests mid-way
    if "abandon quest" in player_input.lower():
        quest_log.abandon_all_quests()
        display_output("🛑 All active quests abandoned. No rewards received.")
