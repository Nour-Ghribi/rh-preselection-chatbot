"""
Configuration OpenRouter pour l'acces aux LLM.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "nlpcvfinal")
OPENROUTER_APP_URL = os.getenv("OPENROUTER_APP_URL", "http://localhost")

LLM_CONFIG = {
    "model": OPENROUTER_MODEL,
    "temperature": 0.3,
    "max_tokens": 900,
    "top_p": 0.9,
}

INTERVIEW_CONFIG = {
    "max_questions": 8,
    "max_followups_per_axis": 1,
    "timeout_seconds": 300,
    "langgraph_recursion_limit": 100,
    "critical_stop_confidence_threshold": 0.75,
    "score_weights": {
        "critique": 0.18,
        "important": 0.10,
        "secondaire": 0.05,
    },
}


def validate_config():
    """Valide que la configuration minimale est presente."""
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY non definie. Cree un fichier .env avec "
            "OPENROUTER_API_KEY=<ta_cle>."
        )


def create_llm_client(max_tokens: int | None = None) -> ChatOpenAI:
    """
    Cree un client LangChain configure pour OpenRouter.

    Le LLM reste utilise pour le langage, mais la logique metier
    reste controlee cote Python/LangGraph.
    """
    validate_config()
    token_limit = max_tokens if max_tokens is not None else LLM_CONFIG["max_tokens"]
    return ChatOpenAI(
        model_name=LLM_CONFIG["model"],
        temperature=LLM_CONFIG["temperature"],
        max_tokens=token_limit,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_APP_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
    )
