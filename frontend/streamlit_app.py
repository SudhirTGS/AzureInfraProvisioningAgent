"""Chat UI for the Azure Infra Provisioning Agent.

Thin client only: every reply and every follow-up suggestion comes from the
FastAPI backend's `/chat` endpoint (see `app/main.py`). This app owns
presentation, nothing else.

Run with: streamlit run frontend/streamlit_app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from components import branding
from components.api_client import BackendError, is_healthy, send_message

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"

STARTER_PROMPTS = [
    "I need a new Azure SQL database for a dev environment",
    "What information do you need to provision a SQL database?",
]

st.set_page_config(
    page_title="Azure Infra Provisioning Agent",
    page_icon="\U0001F4D0",  # triangular ruler
    layout="centered",
)
branding.inject_theme()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "followups" not in st.session_state:
    st.session_state.followups = STARTER_PROMPTS
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL

with st.sidebar:
    st.markdown("**Backend**")
    st.session_state.backend_url = st.text_input("URL", value=st.session_state.backend_url)
    healthy = is_healthy(st.session_state.backend_url)
    st.markdown(f"Status: {'🟢 online' if healthy else '🔴 unreachable'}")
    st.divider()
    if st.button("New session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.followups = STARTER_PROMPTS
        st.rerun()

session_label = st.session_state.session_id[:8] if st.session_state.session_id else "not started"
branding.render_title_block(session_label=session_label, mode_label="chat")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def _submit(text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": text})
    try:
        turn = send_message(st.session_state.backend_url, st.session_state.session_id, text)
    except BackendError as exc:
        st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {exc}"})
        st.session_state.followups = []
        return
    st.session_state.session_id = turn.session_id
    st.session_state.messages.append({"role": "assistant", "content": turn.reply})
    st.session_state.followups = turn.suggested_followups


if st.session_state.followups:
    st.markdown('<div class="aia-followups">', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.followups))
    for col, suggestion in zip(cols, st.session_state.followups):
        with col:
            if st.button(suggestion, key=f"followup-{len(st.session_state.messages)}-{suggestion}"):
                _submit(suggestion)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

typed = st.chat_input("Describe the Azure resource you need...")
if typed:
    _submit(typed)
    st.rerun()
