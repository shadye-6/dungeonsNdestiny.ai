# memory/npc_and_quest_parser.py
import json
import re

def parse_llm_output(llm_text: str):
    """
    Parses LLM output into:
    - dm_text: narrative for player
    - npcs: list of dicts {npc_name, interaction, context}
    - quests: list of dicts {quest_name, progress, description, reward, mandatory}

    Quests are treated as optional unless explicitly marked mandatory.
    """
    # Extract JSON object at the end of the text
    json_match = re.search(r'\{.*\}\s*$', llm_text, flags=re.DOTALL)
    if not json_match:
        return llm_text.strip(), [], []

    dm_text = llm_text[:json_match.start()].strip()
    try:
        data = json.loads(json_match.group())
        npcs = data.get("npcs", [])
        quests_raw = data.get("quests", [])
        quests = []

        for q in quests_raw:
            # canonical keys with defaults
            quest_name = q.get("quest_name", "Unnamed Quest")
            progress = q.get("progress", "Started")
            description = q.get("description", "")
            reward = q.get("reward", "unknown reward")
            mandatory = bool(q.get("mandatory", False))  # optional by default

            # Include quest if it's mandatory or has meaningful progress
            if mandatory or progress.lower() in ["started", "in progress", "completed"]:
                quests.append({
                    "quest_name": quest_name,
                    "progress": progress,
                    "description": description,
                    "reward": reward,
                    "mandatory": mandatory
                })

    except json.JSONDecodeError:
        npcs = []
        quests = []

    return dm_text, npcs, quests
