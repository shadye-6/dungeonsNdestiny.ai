import os

BACKEND = os.getenv("EMBEDDING_BACKEND", "sentence")

if BACKEND == "gemini":
    import google.generativeai as genai
    from utils.config import GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)

    def embed_text(text: str) -> list[float]:
        response = genai.embeddings.create(model="embed-text-3-large", input=text)
        return response.data[0].embedding
else:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_text(text: str) -> list[float]:
        return model.encode(text).tolist()
