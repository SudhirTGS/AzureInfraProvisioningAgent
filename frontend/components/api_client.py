"""Thin HTTP client for the FastAPI backend. No business logic lives here —
the frontend only ever collects/displays what `/chat` returns."""

from dataclasses import dataclass

import httpx


@dataclass
class ChatTurn:
    session_id: str
    reply: str
    suggested_followups: list[str]


class BackendError(RuntimeError):
    pass


def send_message(base_url: str, session_id: str | None, message: str) -> ChatTurn:
    try:
        response = httpx.post(
            f"{base_url}/chat",
            json={"session_id": session_id, "message": message},
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise BackendError(f"Couldn't reach the agent backend at {base_url}: {exc}") from exc

    data = response.json()
    return ChatTurn(
        session_id=data["session_id"],
        reply=data["reply"],
        suggested_followups=data.get("suggested_followups", []),
    )


def is_healthy(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url}/healthz", timeout=5.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False
