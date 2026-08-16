import logging

from fastapi import FastAPI, HTTPException

from app.llm.orchestrator import run_turn
from app.models.schemas import ChatRequest, ChatResponse
from app.session_store import session_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Azure Infra Provisioning Agent",
    description="Conversational collection of Azure resource provisioning requirements.",
)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id, session = session_store.get_or_create(request.session_id)

    try:
        reply, updated_messages, followups = run_turn(session.messages, request.message)
    except Exception:
        logger.exception("chat turn failed for session_id=%s", session_id)
        raise HTTPException(status_code=502, detail="The assistant hit an error processing that message.")

    session_store.save(session_id, updated_messages)
    return ChatResponse(session_id=session_id, reply=reply, suggested_followups=followups)
