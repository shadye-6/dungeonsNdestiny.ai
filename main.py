# main.py
from interface.cli import get_player_input, display_output
from memory.working import WorkingMemory
from memory.persistent import PersistentMemory
from llm.story_engine import generate_response
from llm.prompt_builder import build_prompt
from memory.summarizer import summarize_for_memory
from memory.embeddings import embed_text

vector = embed_text("The hero entered the haunted castle.")


working_mem = WorkingMemory()
persistent_mem = PersistentMemory()

while True:
    player_input = get_player_input()
    retrieved_context = "\n".join(persistent_mem.retrieve(player_input))
    working_context = working_mem.get_context()

    prompt = build_prompt(working_context, retrieved_context, player_input)
    response = generate_response(prompt)

    display_output(response)

    # update memories
    working_mem.add_turn("Player", player_input)
    working_mem.add_turn("DM", response)
    summary = summarize_for_memory(response)
    persistent_mem.add_memory(summary, embed_text(summary))
