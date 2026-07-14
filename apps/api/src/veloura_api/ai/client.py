from functools import lru_cache

from openai import OpenAI

from veloura_api.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI | None:
    settings = get_settings()
    if not settings.is_ai_enabled:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def get_embedding(text: str) -> list[float] | None:
    client = get_openai_client()
    if client is None:
        return None
    settings = get_settings()
    response = client.embeddings.create(model=settings.openai_embedding_model, input=text)
    return response.data[0].embedding
