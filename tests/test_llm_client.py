from types import SimpleNamespace

from app.llm import client as client_module


def _fake_settings(**overrides) -> SimpleNamespace:
    defaults = dict(
        llm_provider="openai",
        llm_model="gpt-4o",
        openai_api_key="sk-test",
        xai_api_key=None,
        xai_base_url="https://api.x.ai/v1",
    )
    return SimpleNamespace(**{**defaults, **overrides})


def test_client_uses_openai_key_when_openai_is_the_provider(monkeypatch):
    captured = {}
    monkeypatch.setattr(client_module, "OpenAI", lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(client_module, "get_settings", lambda: _fake_settings())
    client_module._client.cache_clear()

    client_module._client()

    assert captured == {"api_key": "sk-test"}
    client_module._client.cache_clear()


def test_client_falls_back_to_xai_base_url_when_xai_is_the_provider(monkeypatch):
    captured = {}
    monkeypatch.setattr(client_module, "OpenAI", lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(
        client_module,
        "get_settings",
        lambda: _fake_settings(llm_provider="xai", llm_model="grok-4", xai_api_key="xai-test"),
    )
    client_module._client.cache_clear()

    client_module._client()

    assert captured == {"api_key": "xai-test", "base_url": "https://api.x.ai/v1"}
    client_module._client.cache_clear()
