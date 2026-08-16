"""In-memory conversation state, keyed by session_id.

Matches the design doc's spec exactly: a plain dict, no external store. Each
session's message list is seeded with the system prompt so the orchestrator
never has to special-case "first turn".
"""

import time
import uuid
from dataclasses import dataclass, field

from app.config import get_settings
from app.llm.system_prompt import SYSTEM_PROMPT


@dataclass
class Session:
    messages: list[dict] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(messages=[{"role": "system", "content": SYSTEM_PROMPT}])
        return session_id

    def get(self, session_id: str) -> Session | None:
        self._sweep_expired()
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> tuple[str, Session]:
        if session_id is not None:
            session = self.get(session_id)
            if session is not None:
                return session_id, session
        new_id = self.create()
        return new_id, self._sessions[new_id]

    def save(self, session_id: str, messages: list[dict]) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.messages = messages
        session.last_active = time.time()

    def _sweep_expired(self) -> None:
        ttl_seconds = get_settings().session_ttl_minutes * 60
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s.last_active > ttl_seconds]
        for sid in expired:
            del self._sessions[sid]


session_store = SessionStore()
