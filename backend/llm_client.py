"""
GROQ LLM client helper.
"""
import os
from groq import Groq


def get_groq_client():
    """
    Get GROQ client instance.
    Does not accept proxies parameter - just API key.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set. Please set it in your .env file or export it.")
    return Groq(api_key=api_key)

