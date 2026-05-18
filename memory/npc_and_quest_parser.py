import json
import re


def parse_llm_output(llm_text: str):
    """
    Parses LLM output into:
    - dm_text: narrative for the player
    - npcs: list of dicts {npc_name, interaction, context}
    - quests: list of dicts {quest_name, progress, description, reward, mandatory}
    - world_events: list of dicts {type, name, detail}
    """
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_text, flags=re.DOTALL)
    if not json_match:
        json_match = re.search(r'(\{.*\})\s*$', llm_text, flags=re.DOTALL)

    if not json_match:
        return llm_text.strip(), [], [], []

    json_text = json_match.group(1)
    dm_text = llm_text[:json_match.start()].strip()

    # LLMs sometimes output Python literals instead of valid JSON
    json_text = re.sub(r'\bTrue\b', 'true', json_text)
    json_text = re.sub(r'\bFalse\b', 'false', json_text)
    json_text = re.sub(r'\bNone\b', 'null', json_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode failed: {e}")
        return dm_text, [], [], []

    npcs = data.get("npcs", [])

    quests_raw = data.get("quests", [])
    quests = []
    for q in quests_raw:
        quest_name = q.get("quest_name", "Unnamed Quest")
        progress = q.get("progress", "Started")
        description = q.get("description", "")
        reward = q.get("reward", "unknown reward")
        mandatory = bool(q.get("mandatory", False))

        if mandatory or progress.lower() in ["started", "in progress", "completed"]:
            quests.append({
                "quest_name": quest_name,
                "progress": progress,
                "description": description,
                "reward": reward,
                "mandatory": mandatory,
            })

    world_events_raw = data.get("world_events", [])
    world_events = []
    for e in world_events_raw:
        event_type = e.get("type", "")
        detail = e.get("detail", "")
        if event_type and detail:
            world_events.append({
                "type": event_type,
                "name": e.get("name", ""),
                "detail": detail,
            })

    return dm_text, npcs, quests, world_events
