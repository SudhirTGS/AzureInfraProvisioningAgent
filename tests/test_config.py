import pytest
from pydantic import ValidationError

from app.config import Settings


def test_openai_key_selects_openai_provider():
    settings = Settings(openai_api_key="sk-test", xai_api_key="xai-test")
    assert settings.llm_provider == "openai"
    assert settings.llm_model == settings.openai_model


def test_falls_back_to_xai_when_openai_key_absent():
    settings = Settings(openai_api_key=None, xai_api_key="xai-test", xai_model="grok-4")
    assert settings.llm_provider == "xai"
    assert settings.llm_model == "grok-4"


def test_requires_at_least_one_provider_key():
    with pytest.raises(ValidationError):
        Settings(openai_api_key=None, xai_api_key=None)
