import json
import re

def parse_llm_output(llm_text: str):
    """
    Parses LLM output into:
    - dm_text: narrative for player
    - npcs: list of dicts {npc_name, interaction, context}
    - quests: list of dicts {quest_name, progress, description, reward, mandatory}
    """

    # Match JSON inside triple backticks or at the end
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_text, flags=re.DOTALL)
    if not json_match:
        json_match = re.search(r'(\{.*\})\s*$', llm_text, flags=re.DOTALL)

    if not json_match:
        # No JSON found
        return llm_text.strip(), [], []

    json_text = json_match.group(1)
    dm_text = llm_text[:json_match.start()].strip()

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        print("⚠️ JSON decode failed in parse_llm_output")
        return dm_text, [], []

    npcs = data.get("npcs", [])
    quests_raw = data.get("quests", [])

    quests = []
    for q in quests_raw:
        quest_name = q.get("quest_name", "Unnamed Quest")
        progress = q.get("progress", "Started")
        description = q.get("description", "")
        reward = q.get("reward", "unknown reward")
        mandatory = bool(q.get("mandatory", False))

        # Include quest if it has meaningful progress or is mandatory
        if mandatory or progress.lower() in ["started", "in progress", "completed"]:
            quests.append({
                "quest_name": quest_name,
                "progress": progress,
                "description": description,
                "reward": reward,
                "mandatory": mandatory
            })

    return dm_text, npcs, quests
