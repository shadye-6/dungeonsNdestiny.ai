# memory/embeddings.py
import google.generativeai as genai
from utils.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def embed_text(text: str) -> list[float]:
    """
    Generate embedding vector for a given text using Gemini Embeddings API.
    Returns a list of floats.
    """
    response = genai.embeddings.create(
        model="embed-text-3-large",
        input=text
    )
    # The vector is in response.data[0].embedding
    return response.data[0].embedding

# memory/embeddings.py
from sentence_transformers import SentenceTransformer

# load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> list[float]:
    """
    Generate embedding vector for a given text using Sentence Transformers.
    """
    return model.encode(text).tolist()
