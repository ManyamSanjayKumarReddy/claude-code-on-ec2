from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_chat_model() -> ChatOpenAI:
    if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
        raise RuntimeError("LLM is not configured (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL)")
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )
