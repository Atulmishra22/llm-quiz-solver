"""
Google Gemini client helper for multimodal tasks (audio, vision, etc.).
Uses GOOGLE_API_KEY from environment.
"""
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def get_gemini_client() -> genai.Client:
    """Return a Google GenAI client for multimodal tasks.
    
    Returns:
        genai.Client: Configured Gemini client.
    
    Raises:
        RuntimeError: If GOOGLE_API_KEY is not set.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Set it in your environment or .env file. "
            "Required for multimodal tasks (audio/vision)."
        )
    return genai.Client(api_key=GOOGLE_API_KEY)
