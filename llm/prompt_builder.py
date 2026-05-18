def build_prompt(
    working_context: str,
    retrieved_context: str,
    player_input: str,
    reward_context: str = "",
    world_state_context: str = "",
) -> str:
    """
    Builds the full DM prompt, combining:
    - Long-term semantic memories (RAG)
    - Short-term recent turns (working memory)
    - World state: locations, items, decisions
    - Active quests and collected rewards
    - The main storyline brief
    - Player input
    """

    main_storyline = """
Title: The Shattered Crown

Premise:
The kingdom of Eryndor has been united for centuries under the benevolent rule of the royal family.
The sudden disappearance of King Alaric leaves the throne vacant, and the magical artifact that
protects the realm — the Crown of Concord — shatters into pieces, scattering across dangerous lands.
Darkness seeps into Eryndor as rival factions vie for power and ancient monsters awaken.

Main Conflict:
The players must recover the Crown fragments, restore balance to Eryndor, and uncover the mystery
of King Alaric's disappearance. Choices determine the political, social, and magical future of the kingdom.

Key Plot Threads:
- The Crown Fragments: Each piece has a guardian and unique magical properties.
- Factions & Alliances: Nobles, rebel leaders, secret cults react dynamically to player decisions.
- The Vanished King: Clues about King Alaric's fate appear gradually.
- Evolving World Events: Towns may fall under siege, forests may be corrupted.
- Moral Dilemmas: Choosing between personal gain, loyalty, and the kingdom's welfare.

Story Arcs:
1. Gathering Allies — form alliances and quest for the first Crown fragment.
2. The Dark Rising — shards influence the world; conflicts escalate.
3. Secrets Revealed — hidden truths about King Alaric and a shadowy enemy emerge.
4. The Final Confrontation — prior choices determine the ending.
"""

    return f"""You are a Dungeon Master running a text-based tabletop RPG. Follow these rules strictly:

- Maintain continuity with all events in Persistent Memory and World State.
- Follow the main storyline "The Shattered Crown" and advance it consistently.
- Introduce mandatory main-story quests automatically; introduce optional side quests occasionally.
- Describe scenes vividly and concisely (2-4 sentences per turn).
- Include at least one NPC interaction per turn when possible.
- If the player gives unusual input, respond gracefully and steer the narrative forward.
- After the narrative, output a single JSON block containing NPC interactions, quest updates, and world events.

### Persistent Memory (semantic recall):
{retrieved_context if retrieved_context else "No prior memories retrieved."}

### Recent Turns (working memory):
{working_context if working_context else "This is the start of the adventure."}

### World State:
{world_state_context if world_state_context else "No world events recorded yet."}

### Main Storyline:
{main_storyline}

### Player Rewards and Items:
{reward_context if reward_context else "None yet."}

### Player Input:
Player: {player_input}

### Output Format:
First write the narrative for the player (2-4 sentences).
Then output exactly one JSON block — no extra text before or after it:

```json
{{
    "npcs": [
        {{"npc_name": "Elder Mira", "interaction": "spoke to", "context": "Warned the player about the spreading darkness in the eastern woods."}}
    ],
    "quests": [
        {{"quest_name": "Find the Crown Fragment", "progress": "Started", "description": "Recover the first Crown fragment from the Haunted Ruins.", "reward": "Shard of Concord", "mandatory": true}},
        {{"quest_name": "Deliver the Herbalist's Package", "progress": "Started", "description": "Bring medicine to the village elder.", "reward": "Gold pouch", "mandatory": false}}
    ],
    "world_events": [
        {{"type": "location", "name": "Haunted Ruins", "detail": "Player entered the Haunted Ruins for the first time."}},
        {{"type": "item", "name": "Rusty Key", "detail": "Player found a rusty key near the old gate."}},
        {{"type": "decision", "name": "", "detail": "Player chose to spare the captured bandit."}}
    ]
}}
```

Rules for the JSON:
- "mandatory": true for main story quests, false for optional side quests.
- "world_events" types: "location", "item", "decision", "enemy_defeated".
- Only include events that actually happened this turn.
- Use valid JSON (lowercase true/false, double-quoted strings).
"""
