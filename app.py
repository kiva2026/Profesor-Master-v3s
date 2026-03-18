"""
app.py — Entry point al aplicației Profesor Liceu.

Responsabilități:
  1. Configurare pagină Streamlit + CSS
  2. Inițializare sesiune și Supabase
  3. Construire listă chei API + key_index
  4. Routing către modurile de examinare (BAC / Quiz / Temă / Admitere)
  5. Încărcare istoric + restaurare materie detectată
  6. Render sidebar + chat principal

Tot restul logicii se află în modules/.
"""
import random
import streamlit as st


# ══════════════════════════════════════════════════════════════════
# HELPER: CSS injection
# Definit înainte de set_page_config — Streamlit permite funcții
# Python înainte de primul apel st.*
# ══════════════════════════════════════════════════════════════════

def _inject_css():
    """Injectează CSS global: dark mode, SVG container, typing indicator."""
    _dark = st.session_state.get("dark_mode", False)

    if _dark:
        st.markdown("""
<style>
:root { --svg-bg: #1e1e2e; --svg-border: #444; }
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="block-container"],
section.main > div {
    background-color: #0e1117 !important; color: #fafafa !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background-color: #161b22 !important;
}
[data-testid="stSidebar"] * { color: #fafafa !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-testid]),
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { background-color: transparent !important; }
button[kind="secondary"], button[kind="primary"],
.stButton > button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"] {
    background-color: #2a2f3e !important;
    color: #fafafa !important;
    border-color: #555 !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stSelectbox"] * {
    background-color: #1a1f2e !important; color: #fafafa !important;
}
[data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"] *,
.stChatMessage, .stChatMessage * {
    background-color: transparent !important; color: #fafafa !important;
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stBottom"],
[data-testid="stBottom"] > div {
    background-color: #0e1117 !important;
    color: #fafafa !important;
    border-color: #333 !important;
}
[data-testid="stChatInput"] textarea { background-color: #1a1f2e !important; }
p, h1, h2, h3, h4, h5, h6, label, span, li, td, th, div,
.stMarkdown, .stMarkdown * { color: #fafafa !important; }
[data-testid="stExpander"],
[data-testid="stExpander"] > div {
    background-color: #1a1f2e !important; border-color: #444 !important;
}
[data-testid="stExpander"] * { color: #fafafa !important; }
hr { border-color: #444 !important; }
[data-testid="stHeader"] { background-color: #0e1117 !important; }
[data-testid="stCaptionContainer"] * { color: #aaa !important; }
[data-testid="stInfo"], [data-testid="stInfo"] * {
    background-color: #1a2744 !important; color: #90c8ff !important;
}
[data-testid="stSuccess"], [data-testid="stSuccess"] * {
    background-color: #0f2a1a !important; color: #6fcf97 !important;
}
</style>
""", unsafe_allow_html=True)

    _svg_bg     = "#1e1e2e" if _dark else "white"
    _svg_border = "#444"    if _dark else "#ddd"
    _svg_shadow = ("0 2px 8px rgba(0,0,0,0.4)" if _dark
                   else "0 2px 8px rgba(0,0,0,0.1)")

    st.markdown(f"""
<style>
    .stChatMessage {{ font-size: 16px; }}
    footer {{ visibility: hidden; }}
    .svg-container {{
        background-color: {_svg_bg};
        padding: 20px;
        border-radius: 10px;
        border: 1px solid {_svg_border};
        text-align: center;
        margin: 15px 0;
        overflow: auto;
        box-shadow: {_svg_shadow};
        max-width: 100%;
    }}
    .svg-container svg {{ max-width: 100%; height: auto; }}
    .typing-indicator {{
        display: flex; align-items: center; gap: 6px;
        padding: 10px 4px; font-size: 14px; color: #888;
    }}
    .typing-dots {{ display: flex; gap: 4px; }}
    .typing-dots span {{
        width: 7px; height: 7px; border-radius: 50%;
        background: #888;
        animation: typing-bounce 1.2s infinite ease-in-out;
    }}
    .typing-dots span:nth-child(1) {{ animation-delay: 0s; }}
    .typing-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes typing-bounce {{
        0%, 80%, 100% {{ transform: scale(0.7); opacity: 0.4; }}
        40%            {{ transform: scale(1.0); opacity: 1.0; }}
    }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# BOOTSTRAP
# set_page_config TREBUIE să fie primul apel Streamlit din script
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Profesor Liceu",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

_inject_css()

# ── Importuri interne (după set_page_config) ──────────────────────
from config import MATERII, CLEANUP_DAYS_OLD, MAX_MESSAGES_TO_SEND_TO_AI
from modules.auth.supabase_auth import (
    init_db, cleanup_old_sessions, load_history_from_db, update_session_activity,
)
from modules.ai.gemini_client import summarize_conversation
from modules.materii import update_system_prompt_for_subject
from modules.materii.detect import detect_subject_from_text
from modules.ui.sidebar import build_api_keys, render_sidebar, render_api_key_section
from modules.ui.chat import (
    render_chat_history, handle_quick_actions,
    handle_pending_messages, handle_chat_input,
)
from modules.utils.session import get_or_create_session_id, inject_session_js

# ── DB + sesiune ───────────────────────────────────────────────────
init_db()
cleanup_old_sessions(CLEANUP_DAYS_OLD)

session_id = get_or_create_session_id()
st.session_state.session_id = session_id
update_session_activity(session_id)
inject_session_js()

# ── Chei API ───────────────────────────────────────────────────────
keys = build_api_keys()

if not keys:
    st.error("❌ Nicio cheie API validă. Introdu cheia ta Google AI în bara laterală.")
    with st.sidebar:
        render_api_key_section([])
    st.stop()

if "key_index" not in st.session_state:
    st.session_state.key_index = random.randint(0, max(len(keys) - 1, 0))
st.session_state["_api_keys_list"] = keys

# ── Sidebar ────────────────────────────────────────────────────────
keys, media_content = render_sidebar(keys)

# ── Titlu + subtitlu materie ───────────────────────────────────────
st.title("🎓 Profesor Liceu")

if st.session_state.get("pedagogie_mode"):
    st.caption("🧠 **Mod Sfaturi de studiu**")
else:
    _mat_curenta = st.session_state.get("materie_selectata")
    if _mat_curenta:
        _mat_label = next(
            (k for k, v in MATERII.items() if v == _mat_curenta), _mat_curenta
        )
        st.caption(f"Materie selectată: **{_mat_label}**")

# ── Routing moduri de examinare ────────────────────────────────────
if st.session_state.get("homework_mode"):
    from modules.bac.homework_ui import run_homework_ui
    run_homework_ui()
    st.stop()

if st.session_state.get("admitere_mode"):
    from modules.bac.admitere_ui import run_admitere_ui
    run_admitere_ui()
    st.stop()

if st.session_state.get("bac_mode"):
    from modules.bac.bac_ui import run_bac_sim_ui
    run_bac_sim_ui()
    st.stop()

if st.session_state.get("quiz_mode"):
    from modules.bac.quiz_ui import run_quiz_ui
    run_quiz_ui()
    st.stop()

# ── Încărcare istoric conversație ─────────────────────────────────
_current_sid = st.session_state.session_id
if (
    "messages" not in st.session_state
    or st.session_state.get("_messages_for_sid") != _current_sid
):
    _loaded_msgs = load_history_from_db(_current_sid)
    st.session_state.messages      = _loaded_msgs
    st.session_state["_messages_for_sid"] = _current_sid
    st.session_state.pop("_history_may_be_incomplete", None)

    # Restaurare materie din primele mesaje ale sesiunii
    if _loaded_msgs and not st.session_state.get("_detected_subject"):
        _first_user_msgs = [
            m["content"] for m in _loaded_msgs if m.get("role") == "user"
        ][:3]
        _combined = " ".join(_first_user_msgs)
        if _combined:
            _restored = detect_subject_from_text(_combined)
            if _restored and not _restored.startswith("_"):
                st.session_state["_detected_subject"] = _restored
                update_system_prompt_for_subject(_restored)

    # Pre-generare rezumat pentru conversații lungi (revenire din altă zi)
    if len(_loaded_msgs) > MAX_MESSAGES_TO_SEND_TO_AI:
        _sum_key     = "_conversation_summary"
        _sum_sid_key = "_summary_for_sid"
        if (
            not st.session_state.get(_sum_key)
            or st.session_state.get(_sum_sid_key) != _current_sid
        ):
            with st.spinner("📚 Profesorul reîncarcă contextul conversației anterioare..."):
                _auto_summary = summarize_conversation(_loaded_msgs)
            if _auto_summary:
                st.session_state[_sum_key]             = _auto_summary
                st.session_state["_summary_cached_at"] = len(_loaded_msgs)
                st.session_state[_sum_sid_key]         = _current_sid
                st.toast("✅ Contextul conversației anterioare a fost reîncărcat!", icon="🧠")

# ── Banner mod Pas cu Pas ──────────────────────────────────────────
if st.session_state.get("pas_cu_pas"):
    st.markdown(
        '<div style="background:linear-gradient(135deg,#667eea,#764ba2);'
        'color:white;padding:10px 16px;border-radius:10px;margin-bottom:12px;'
        'display:flex;align-items:center;gap:10px;font-size:14px;">'
        '🔢 <strong>Mod Pas cu Pas activ</strong> — '
        'Profesorul îți va explica fiecare problemă detaliat, cu motivația fiecărui pas.'
        '</div>',
        unsafe_allow_html=True
    )

# ── Render chat ────────────────────────────────────────────────────
render_chat_history()
handle_quick_actions()
handle_pending_messages()
handle_chat_input(media_content=media_content)
