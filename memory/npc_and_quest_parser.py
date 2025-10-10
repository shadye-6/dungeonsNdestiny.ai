# memory/npc_and_quest_parser.py
import json
import re

def parse_llm_output(llm_text: str):
    """
    Returns:
    - dm_text: narrative for player
    - npcs: list of dicts {npc_name, interaction, context}
    - quests: list of dicts {quest_name, progress, description, reward}
    """
    # Find JSON at the end
    json_match = re.search(r'\{.*\}\s*$', llm_text, flags=re.DOTALL)
    if not json_match:
        return llm_text.strip(), [], []

    json_text = json_match.group()
    dm_text = llm_text[:json_match.start()].strip()

    try:
        data = json.loads(json_text)
        npcs = data.get("npcs", [])
        quests = data.get("quests", [])
    except json.JSONDecodeError:
        npcs = []
        quests = []

    return dm_text, npcs, quests
