"""Visual identity for the Streamlit frontend.

Deliberately matches the "blueprint" language used in the accelerator pitch
deck: a title block header, a fine technical grid, Big Shoulders Display /
IBM Plex Sans / IBM Plex Mono, and a cyan accent. The mark in `assets/mark.svg`
is a custom icon, not Microsoft's trademarked Azure logo — swap it for an
official Azure Architecture Icon if/when co-branding approval is in place.
"""

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

ACCENT = "#0E6B99"
WARM = "#9C630A"


@lru_cache(maxsize=None)
def _font_b64(filename: str) -> str:
    return base64.b64encode((ASSETS_DIR / "fonts" / filename).read_bytes()).decode("ascii")


@lru_cache(maxsize=None)
def _mark_svg() -> str:
    return (ASSETS_DIR / "mark.svg").read_text(encoding="utf-8")


def inject_theme() -> None:
    """Injects fonts, the blueprint grid, and component styling.

    Streamlit's own light/dark toggle controls its native chrome; these rules
    additionally respond to the OS-level `prefers-color-scheme` so the custom
    header, chips, and chat bubbles stay legible in both.
    """
    big_shoulders = _font_b64("big-shoulders-display.woff2")
    mono_400 = _font_b64("ibm-plex-mono-400.woff2")
    mono_500 = _font_b64("ibm-plex-mono-500.woff2")
    mono_600 = _font_b64("ibm-plex-mono-600.woff2")
    plex_sans = _font_b64("ibm-plex-sans.woff2")

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'Big Shoulders';
            font-weight: 500 900;
            font-display: swap;
            src: url(data:font/woff2;base64,{big_shoulders}) format('woff2');
        }}
        @font-face {{
            font-family: 'Plex Mono';
            font-weight: 400;
            font-display: swap;
            src: url(data:font/woff2;base64,{mono_400}) format('woff2');
        }}
        @font-face {{
            font-family: 'Plex Mono';
            font-weight: 500;
            font-display: swap;
            src: url(data:font/woff2;base64,{mono_500}) format('woff2');
        }}
        @font-face {{
            font-family: 'Plex Mono';
            font-weight: 600;
            font-display: swap;
            src: url(data:font/woff2;base64,{mono_600}) format('woff2');
        }}
        @font-face {{
            font-family: 'Plex Sans';
            font-weight: 400 700;
            font-display: swap;
            src: url(data:font/woff2;base64,{plex_sans}) format('woff2');
        }}

        :root {{
            --aia-bg: #F4F6F8;
            --aia-surface: #FFFFFF;
            --aia-ink: #16232E;
            --aia-ink-soft: #51606D;
            --aia-line: rgba(22,35,46,0.16);
            --aia-line-strong: rgba(22,35,46,0.32);
            --aia-accent: {ACCENT};
            --aia-accent-soft: rgba(14,107,153,0.10);
            --aia-warm: {WARM};
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --aia-bg: #0E141B;
                --aia-surface: #141C25;
                --aia-ink: #E7EDF2;
                --aia-ink-soft: #93A4B3;
                --aia-line: rgba(255,255,255,0.13);
                --aia-line-strong: rgba(255,255,255,0.26);
                --aia-accent: #4FD7EC;
                --aia-accent-soft: rgba(79,215,236,0.12);
                --aia-warm: #E8A23F;
            }}
        }}

        .stApp {{
            background-image:
                linear-gradient(var(--aia-line) 1px, transparent 1px),
                linear-gradient(90deg, var(--aia-line) 1px, transparent 1px);
            background-size: 28px 28px;
        }}

        .block-container {{
            max-width: 880px;
            padding-top: 4.75rem;
        }}

        body, .stMarkdown, .stChatMessage, .stMarkdown p, .stMarkdown li,
        .stButton button, .stTextInput input, div[data-testid="stChatInput"] textarea {{
            font-family: 'Plex Sans', -apple-system, 'Segoe UI', sans-serif;
        }}

        div[data-testid="stChatMessage"], .stButton button, div[data-testid="stChatInput"] {{
            border-radius: 2px;
        }}

        .aia-titleblock {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            border: 1px solid var(--aia-line-strong);
            background: var(--aia-surface);
            padding: 14px 20px;
            margin-bottom: 22px;
            flex-wrap: wrap;
        }}
        .aia-brand {{ display: flex; align-items: center; gap: 12px; }}
        .aia-mark {{ color: var(--aia-accent); flex: none; }}
        .aia-mark svg {{ display: block; width: 30px; height: 30px; }}
        .aia-wordmark {{
            font-family: 'Plex Mono', monospace;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.03em;
            color: var(--aia-ink);
            line-height: 1.35;
        }}
        .aia-wordmark .sub {{
            display: block;
            color: var(--aia-ink-soft);
            font-weight: 400;
            font-size: 10.5px;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }}
        .aia-meta {{
            font-family: 'Plex Mono', monospace;
            font-size: 11px;
            color: var(--aia-ink-soft);
            display: flex;
            gap: 16px;
        }}
        .aia-meta b {{ color: var(--aia-accent); font-weight: 600; }}

        h1, h2, h3 {{ font-family: 'Big Shoulders', sans-serif; letter-spacing: 0.01em; }}

        div[data-testid="stChatMessage"] {{
            border: 1px solid var(--aia-line);
            background: var(--aia-surface);
        }}

        .aia-followups {{ margin-top: -6px; margin-bottom: 18px; }}
        .aia-followups .stButton button {{
            font-family: 'Plex Mono', monospace;
            font-size: 12.5px;
            border: 1px solid var(--aia-line-strong);
            background: var(--aia-accent-soft);
            color: var(--aia-accent);
            border-radius: 999px;
            padding: 4px 14px;
        }}
        .aia-followups .stButton button:hover {{
            border-color: var(--aia-accent);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_title_block(session_label: str, mode_label: str) -> None:
    st.markdown(
        f"""
        <div class="aia-titleblock">
          <div class="aia-brand">
            <span class="aia-mark">{_mark_svg()}</span>
            <div class="aia-wordmark">
              AZURE INFRA PROVISIONING AGENT
              <span class="sub">TGS Azure Accelerator</span>
            </div>
          </div>
          <div class="aia-meta">
            <span>SESSION <b>{session_label}</b></span>
            <span>MODE <b>{mode_label}</b></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
