import google.generativeai as genai
from utils.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)


def generate_response(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"⚠️ LLM generation failed: {e}")
        return "The Dungeon Master pauses, gathering their thoughts... Please try again."
