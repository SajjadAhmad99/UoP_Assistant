"""
UoP AI Assistant - Streamlit Frontend
Interactive web interface for the University of Peshawar information assistant.

Changes vs original:
- Injects static/style.css (dark-mode glassmorphism aesthetic)
- Adds _render_response() to parse structured JSON from department_tools
  and render rich components (confidence badge, gallery, lists, tables)
- Removes unused io import
"""
import os
import sys
import json

# Add parent relative path to PYTHONPATH to allow finding multi_agent package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import time
from typing import Dict, Any

# Fix UTF-8 encoding for console output if possible (safer for Streamlit)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

from multi_agent import ask_uop

# ── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="UOP Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS Injection ─────────────────────────────────────────────────────────────
_CSS_PATH = os.path.join(os.path.dirname(__file__), "static", "style.css")
if os.path.exists(_CSS_PATH):
    with open(_CSS_PATH, "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ── Session State Initialization ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "user_" + str(int(time.time()))

if "thinking" not in st.session_state:
    st.session_state.thinking = False


# ── Structured Response Renderer ─────────────────────────────────────────────
def _confidence_badge(score: int) -> str:
    """Return a colour-coded emoji badge for a confidence score 0-100."""
    if score >= 85:
        return f"🟢 **Confidence:** {score}/100"
    if score >= 60:
        return f"🟡 **Confidence:** {score}/100"
    return f"🔴 **Confidence:** {score}/100"


def _render_response(raw: str):
    """
    Try to parse `raw` as the structured JSON dict returned by
    UOPDepartmentScraperTool.  If parsing succeeds, render rich Streamlit
    components; otherwise fall back to plain markdown.
    """
    # Attempt JSON parse — the dept tool wraps its output in a dict
    data = None
    try:
        # Sometimes the LLM wraps the JSON in triple backticks
        cleaned = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # ── Structured department tool output ────────────────────────────────────
    if isinstance(data, dict) and "query_intent" in data:
        dept       = data.get("department", "")
        intent     = data.get("query_intent", "")
        source_url = data.get("source_url", "")
        sub_sec    = data.get("sub_section_used", "")
        confidence = data.get("confidence_score", 0)
        timestamp  = data.get("timestamp", "")
        extracted  = data.get("extracted_data", {})

        # Header
        if dept and dept not in ("DEPARTMENT_NOT_FOUND", "All Faculties", ""):
            st.markdown(f"### 🏫 {dept}")
        if intent:
            st.markdown(f"*Intent: **{intent}***")
        st.markdown(_confidence_badge(int(confidence)))
        if source_url:
            st.markdown(f"🔗 [Source]({source_url}) — `{sub_sec}`")
        if timestamp:
            st.caption(f"Retrieved: {timestamp}")
        st.divider()

        # ── Gallery ──────────────────────────────────────────────────────────
        if intent == "gallery" and isinstance(extracted, dict):
            images = extracted.get("images", [])
            if images:
                st.markdown("#### 🖼️ Gallery")
                cols = st.columns(min(3, len(images)))
                for i, img in enumerate(images[:9]):
                    url = img.get("url", "")
                    caption = img.get("caption") or img.get("alt_text", "")
                    if url:
                        with cols[i % 3]:
                            st.image(url, caption=caption or url.split("/")[-1])
            else:
                st.info("No images found for this department's gallery.")
            parent = extracted.get("parent_faculty", "")
            if parent:
                st.caption(f"Faculty: {parent}")
            return

        # ── Global hierarchy ─────────────────────────────────────────────────
        if isinstance(extracted, dict) and "faculties" in extracted:
            st.markdown(
                f"**{extracted.get('total_faculties', 0)} Faculties** | "
                f"**{extracted.get('total_departments', 0)} Departments**"
            )
            for fac_name, fac_data in extracted["faculties"].items():
                with st.expander(f"🏛️ {fac_name}"):
                    dean = fac_data.get("dean", "")
                    if dean:
                        st.markdown(f"*{dean[:200]}*")
                    depts = fac_data.get("departments", [])
                    if depts:
                        for d in depts:
                            st.markdown(f"  - {d}")
            return

        # ── Faculty detail / specific dept ───────────────────────────────────
        if isinstance(extracted, dict):
            content = extracted.get("content", [])
            parent  = extracted.get("parent_faculty", "")
            dean    = extracted.get("faculty_dean_info", "")

            if parent:
                st.markdown(f"**Faculty:** {parent}")
            if dean:
                with st.expander("Dean / Faculty Info"):
                    st.markdown(dean[:400])

            if isinstance(content, list) and content:
                for item in content:
                    if "SITE_UNAVAILABLE" in str(item) or "NO_DATA_FOUND" in str(item):
                        st.warning(str(item))
                    else:
                        st.markdown(f"- {item}")
            elif isinstance(content, str) and content:
                if "SITE_UNAVAILABLE" in content or "NO_DATA_FOUND" in content:
                    st.warning(content)
                else:
                    st.markdown(content)
            return

        # ── Error/not-found ──────────────────────────────────────────────────
        if "error" in data:
            st.warning(data["error"])
            return

        # Generic dict fallback
        st.markdown(raw)
        return

    # ── Plain text / direct answer output ────────────────────────────────────
    # Legacy format support: extract [Final Verified Answer] if still present
    if "[Final Verified Answer]" in raw or "[Final Retrieved Answer]" in raw:
        import re
        pattern = r"\[Final (?:Verified|Retrieved) Answer\]\n(.*?)(?=\n\[|$)"
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            clean_ans = match.group(1).strip()
            st.markdown(clean_ans)
            return

    # Direct text output (new hybrid approach — no format blocks)
    st.markdown(raw)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("University of Peshawar")
    st.markdown("**Official Information Assistant**")
    st.markdown("---")

    debug_mode = st.checkbox("Show thinking steps & tool usage", value=False)

    if st.button("Start New Conversation", type="primary"):
        st.session_state.messages = []
        st.session_state.thread_id = "user_" + str(int(time.time()))
        st.rerun()

    st.markdown(f"**Thread ID:** {st.session_state.thread_id[:12]}...")
    st.markdown("---")
    st.markdown(
        "**What I can help with:**\n"
        "• Departments & programs\n"
        "• Admissions & fees\n"
        "• Latest news & announcements\n"
        "• Campus life & scholarships"
    )


# ── Main Content ──────────────────────────────────────────────────────────────
st.title("🎓 UOP Information Assistant")
st.caption("Ask anything about University of Peshawar — departments, news, admissions, programs...")

if len(st.session_state.messages) == 0:
    st.info(
        "Hello! I'm here to help with **University of Peshawar** related questions.\n\n"
        "You can ask about:\n"
        "• Departments & programs\n"
        "• Admissions & fees\n"
        "• Latest news & announcements\n"
        "• Campus life, scholarships, etc.\n\n"
        "How can I assist you today?"
    )


# ── Display Chat History ──────────────────────────────────────────────────────
for message in st.session_state.messages:
    role   = "user" if message["role"] == "user" else "assistant"
    avatar = "🧑‍🎓" if role == "user" else "🤖"

    with st.chat_message(role, avatar=avatar):
        if debug_mode and message.get("debug"):
            with st.expander("🛠️ System Debug & Evaluation Panel", expanded=True):
                st.markdown(message["debug"])
        _render_response(message["content"])


# ── Handle User Input ─────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about UOP..."):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🤔 Thinking...")
        st.session_state.thinking = True

        try:
            response, metrics = ask_uop(
                prompt=prompt,
                thread_id=st.session_state.thread_id,
            )

            if metrics:
                debug_info = (
                    f"{metrics.get('debug_output', '')}\n\n"
                    f"### 💻 Developer Testing Metrics\n"
                    f"```json\n{metrics.get('developer_metrics', '{}')}```"
                )
            else:
                debug_info = (
                    f"**Query:** {prompt}\n\n"
                    "**Note:** Direct conversational route triggered. No external retrievals performed."
                )

            thinking_placeholder.empty()
            _render_response(response)

            st.session_state.messages.append({
                "role":    "assistant",
                "content": response,
                "debug":   debug_info if debug_mode else None,
            })

        except Exception as e:
            error_msg = f"Sorry, something went wrong: {str(e)}"
            thinking_placeholder.error(error_msg)
            st.session_state.messages.append({
                "role":    "assistant",
                "content": error_msg,
            })

        finally:
            st.session_state.thinking = False
