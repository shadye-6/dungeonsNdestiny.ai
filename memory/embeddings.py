import os

_sentence_model = None
_gemini_configured = False


def embed_text(text: str) -> list[float]:
    backend = os.getenv("EMBEDDING_BACKEND", "sentence")

    if backend == "gemini":
        import google.generativeai as genai
        from utils.config import GEMINI_API_KEY

        global _gemini_configured
        if not _gemini_configured:
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_configured = True

        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]

    else:
        from sentence_transformers import SentenceTransformer

        global _sentence_model
        if _sentence_model is None:
            _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _sentence_model.encode(text).tolist()
