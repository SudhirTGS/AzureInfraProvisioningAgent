from functools import lru_cache

from openai import OpenAI

from app.config import get_settings
from app.llm.tool_schemas import TOOLS


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)


def create_completion(messages: list[dict]):
    """Call the chat completions API with the fixed tool set. Thin wrapper so the
    orchestrator's loop logic can be unit tested by mocking this one function."""
    settings = get_settings()
    return _client().chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
