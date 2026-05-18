from interface.cli import get_player_input, display_output
from memory.persistent import PersistentMemory
from memory.working import WorkingMemory
from memory.character_memory import CharacterMemory
from memory.quest_log import QuestLog
from memory.npc_and_quest_parser import parse_llm_output
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt

persistent_mem = PersistentMemory()
working_mem = WorkingMemory(limit=5)
working_mem.load_from(persistent_mem.get_recent_memories(5))
character_mem = CharacterMemory()
quest_log = QuestLog()

print("🛡️ AI Dungeon Master is ready! Type 'start' to begin or 'exit' to quit.\n")
print("📜 Rules:")
print("- Each turn, describe your action to interact with the world.")
print("- You may talk to NPCs, explore locations, solve puzzles, or accept quests.")
print("- Optional side quests can be accepted or declined; main story quests are mandatory.")
print("- Type 'abandon quest' to drop all active optional quests (no rewards).\n")


while True:
    player_input = get_player_input()
    if player_input.lower() in ["exit", "quit"]:
        print("Exiting AI Dungeon Master...")
        break

    # Detect explicit NPC interaction for targeted memory retrieval
    npc_name = None
    if "talk to" in player_input.lower():
        npc_name = player_input.split("talk to")[-1].strip().title()

    working_context = working_mem.get_context()
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=5))

    if npc_name:
        npc_history = "\n".join(character_mem.get_memory(npc_name, query=player_input, top_k=5))
        if npc_history:
            retrieved_context += f"\nPrevious {npc_name} Interactions:\n{npc_history}"

    active_quests = quest_log.get_active_quests()
    quest_context = ""
    if active_quests:
        quest_context = "\n".join([
            f"- {q['quest_name']} (Progress: {q['progress_status']}/10)\n  Summary: {q.get('progress_summary', '')}"
            for q in active_quests
        ])

    reward_context = quest_log.get_rewards_context()

    prompt = build_prompt(
        working_context + (f"\nActive Quests:\n{quest_context}" if quest_context else ""),
        retrieved_context,
        player_input,
        reward_context=reward_context
    )

    response = generate_response(prompt)
    dm_text, npcs, quests, world_events = parse_llm_output(response)
    display_output(dm_text)

    # Persist this turn to long-term and short-term memory
    summary = summarize_for_memory(dm_text)
    summary_emb = embed_text(summary)
    persistent_mem.add_memory(summary, summary_emb)
    working_mem.push(summary)

    # Update NPC character memory
    for npc in npcs:
        npc_name_val = npc.get("npc_name", "")
        context = npc.get("context", "")
        if npc_name_val and context:
            character_mem.add_interaction(npc_name_val, context)

    # Handle quests
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
                display_output(f"📜 Main Quest Added: {quest_name}")
            else:
                quest_log.update_progress(quest_name, increment=1, new_summary=quest["description"])
                display_output(f"📜 Main Quest Progress Updated: {quest_name}")
        else:
            if quest_log.get_active_quest_by_name(quest_name) is None:
                display_output(f"\n🗺️ Optional Quest Available: {quest_name}\n   {quest['description']}")
                player_choice = get_player_input("Accept this quest? (yes/no): ").strip().lower()
                if player_choice in ["yes", "y"]:
                    quest_log.add_quest(
                        quest_name=quest_name,
                        summary=quest["description"],
                        reward=quest.get("reward", "unknown reward"),
                        mandatory=False
                    )
                    display_output(f"✅ Quest Accepted: {quest_name}")
                else:
                    display_output(f"❌ Quest Declined: {quest_name}")
            else:
                quest_log.update_progress(quest_name, increment=1, new_summary=quest["description"])

    if "abandon quest" in player_input.lower():
        quest_log.abandon_all_quests()
        display_output("🛑 All active quests abandoned.")
