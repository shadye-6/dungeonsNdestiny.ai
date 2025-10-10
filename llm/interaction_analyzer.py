# llm/interaction_analyzer.py
import json
import re
import google.generativeai as genai
from utils.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def analyze_interaction(player_input, dm_response):
    """
    Analyze player and DM interaction to extract NPCs and quests automatically.
    Uses Gemini to infer names, quest events, and progress status.
    Returns a dict: {"npcs": [...], "quests": [...]}
    """
    prompt = f"""
You are an RPG analyzer. 
Given a player's input and the Dungeon Master's response, extract structured data in JSON format.
Identify:
1. NPCs mentioned by name or role.
2. Quests that are started, updated, or completed.
3. Include a progress_status for each quest: a number from 1 to 3, where 3 means completed.

Return only valid JSON in this exact format:
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
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # 🧹 Try to extract JSON safely using regex
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response.")

        json_str = json_match.group(0)
        data = json.loads(json_str)

        # ✅ Ensure keys exist and add default progress_status
        if "npcs" not in data:
            data["npcs"] = []
        if "quests" not in data:
            data["quests"] = []
        else:
            for q in data["quests"]:
                if "progress_status" not in q:
                    q["progress_status"] = 1  # default starting status

        return data

    except Exception as e:
        print(f"⚠️ Error parsing LLM output: {e}")
        print("⚠️ Raw response:", response.text if 'response' in locals() else 'No response')
        return {"npcs": [], "quests": []}
