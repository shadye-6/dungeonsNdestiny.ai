import google.generativeai as genai
from utils.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def generate_response(prompt, model="gemini-2.5-flash"):
    model = genai.GenerativeModel(model)
    response = model.generate_content(prompt)
    return response.text
