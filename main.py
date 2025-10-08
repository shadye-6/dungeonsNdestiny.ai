# main.py
from interface.cli import get_player_input, display_output
from memory.working import WorkingMemory
from memory.persistent import PersistentMemory
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt

# Initialize memories
working_mem = WorkingMemory(limit=5)
persistent_mem = PersistentMemory(path="storage/world_state.json")

print("🛡️  AI Dungeon Master is ready! Type 'exit' to quit.")

# Main loop
while True:
    # 1️⃣ Get player input
    player_input = get_player_input()
    if player_input.lower() in ["exit", "quit"]:
        print("Exiting AI Dungeon Master...")
        break

    # 2️⃣ Retrieve relevant persistent memory
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input, top_k=3))

    # 3️⃣ Get working memory context
    working_context = working_mem.get_context()

    # 4️⃣ Build prompt for LLM
    prompt = build_prompt(working_context, retrieved_context, player_input)

    # 5️⃣ Generate DM response
    response = generate_response(prompt)

    # 6️⃣ Display output to player
    display_output(response)

    # 7️⃣ Update working memory
    working_mem.add_turn("Player", player_input)
    working_mem.add_turn("DM", response)

    # 8️⃣ Summarize DM response for long-term memory
    summary = summarize_for_memory(response)
    summary_emb = embed_text(summary)
    persistent_mem.add_memory(summary, summary_emb)
