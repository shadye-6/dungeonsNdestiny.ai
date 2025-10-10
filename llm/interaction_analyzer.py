# llm/interaction_analyzer.py
import json
import re
import google.generativeai as genai
from utils.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def analyze_interaction(player_input, dm_response):
    """
    Analyze player and DM interaction to extract NPCs and quests automatically.
    Returns a dict with consistent quest schema:
    - "progress": string ("Started", "In Progress", "Completed")
    - "mandatory": bool (default False)
    """
    prompt = f"""
You are an RPG analyzer. 
Given a player's input and the Dungeon Master's response, extract structured data in JSON format.
Identify:
1. NPCs mentioned by name or role.
2. Quests that are started, updated, or completed.
3. Include a progress_status for each quest: a number from 1 to 10, where 10 means completed.

Return only valid JSON in this format:
{{
  "npcs": ["NPC Name 1", "NPC Name 2"],
  "quests": [
    {{
      "quest_name": "Quest Title",
      "event_type": "started" | "updated" | "completed",
      "description": "Short summary of what happened",
      "progress_status": 1
    }}
  ]
}}

If nothing is found, return:
{{"npcs": [], "quests": []}}

---
Player Input: {player_input}
DM Response: {dm_response}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON safely
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response.")

        data = json.loads(json_match.group(0))
        if "npcs" not in data:
            data["npcs"] = []
        if "quests" not in data:
            data["quests"] = []
        else:
            # Map event_type/progress_status -> canonical "progress" string
            status_map = {
                "started": "Started",
                "updated": "In Progress",
                "completed": "Completed"
            }
            for q in data["quests"]:
                event_type = q.get("event_type", "started").lower()
                q["progress"] = status_map.get(event_type, "Started")
                q["reward"] = q.get("reward", "unknown reward")
                q["description"] = q.get("description", "")
                q["mandatory"] = q.get("mandatory", False)

        return data

    except Exception as e:
        print(f"⚠️ Error parsing LLM output: {e}")
        print("⚠️ Raw response:", response.text if 'response' in locals() else 'No response')
        return {"npcs": [], "quests": []}
