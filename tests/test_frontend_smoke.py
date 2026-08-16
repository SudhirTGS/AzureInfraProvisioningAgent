"""Headless smoke test for the Streamlit frontend.

Doesn't hit a real backend — mirrors the rest of the suite's style of
monkeypatching the network boundary rather than requiring a live server.
Mainly guards against import-time/render-time breakage (bad CSS f-string,
missing asset, etc.) slipping in unnoticed.
"""

import sys
from pathlib import Path

import pytest

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
sys.path.insert(0, str(FRONTEND_DIR))

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from components import api_client  # noqa: E402


def test_app_renders_without_exception(monkeypatch):
    monkeypatch.setattr(api_client, "is_healthy", lambda base_url: True)

    at = AppTest.from_file(str(FRONTEND_DIR / "streamlit_app.py"))
    at.run(timeout=15)

    assert not at.exception
    assert len(at.chat_input) == 1
    assert len(at.button) >= 2  # starter-prompt follow-up chips


def test_clicking_a_followup_sends_it_and_renders_the_reply(monkeypatch):
    monkeypatch.setattr(api_client, "is_healthy", lambda base_url: True)
    monkeypatch.setattr(
        api_client,
        "send_message",
        lambda base_url, session_id, message: api_client.ChatTurn(
            session_id="test-session",
            reply="Sure — which region?",
            suggested_followups=["eastus2", "centralus"],
        ),
    )

    at = AppTest.from_file(str(FRONTEND_DIR / "streamlit_app.py"))
    at.run(timeout=15)
    at.button[0].click().run(timeout=15)

    assert not at.exception
    assert len(at.chat_message) == 2
    assert at.chat_message[1].markdown[0].value == "Sure — which region?"
    assert [b.label for b in at.button if b.label in ("eastus2", "centralus")] == ["eastus2", "centralus"]
