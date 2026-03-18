"""
modules/utils/session.py — Gestionarea sesiunilor (generare, validare, switch).

Funcții mutate din app.py:
  - generate_unique_session_id()
  - is_valid_session_id()
  - get_or_create_session_id()
  - switch_session()
  - invalidate_session_cache()
  - format_time_ago()
  - inject_session_js()
  - trim_session_messages()
"""
import json
import secrets
import time
import streamlit as st
import streamlit.components.v1 as components

from config import MAX_MESSAGES_IN_MEMORY, SESSION_ID_RE


# ──────────────────────────────────────────────────────────────────
# Generare / validare
# ──────────────────────────────────────────────────────────────────

def generate_unique_session_id() -> str:
    """Generează un session ID criptografic sigur (64 hex lowercase)."""
    return secrets.token_hex(32)


def is_valid_session_id(sid: str) -> bool:
    """Validează session_id: doar hex lowercase, 16-64 caractere."""
    if not sid or not isinstance(sid, str):
        return False
    return bool(SESSION_ID_RE.match(sid))


# ──────────────────────────────────────────────────────────────────
# Obținere / creare sesiune la pornire
# ──────────────────────────────────────────────────────────────────

def get_or_create_session_id() -> str:
    """
    URL-ul ?sid= este SINGURA sursă de adevăr pentru identitatea browserului.

    Flux prima vizită (URL fără ?sid=):
      Python generează UUID → îl pune în ?sid= → URL-ul devine unic per browser

    Flux revenire (bookmark, restart):
      Elevul deschide URL-ul cu ?sid= → Python îl citește → restaurează istoricul
    """
    from modules.auth.supabase_auth import session_exists_in_db, register_session

    sid_from_url = st.query_params.get("sid", "")

    if is_valid_session_id(sid_from_url):
        if not session_exists_in_db(sid_from_url):
            register_session(sid_from_url)
        st.session_state["session_id"] = sid_from_url
        return sid_from_url

    new_id = generate_unique_session_id()
    register_session(new_id)
    try:
        st.query_params["sid"] = new_id
    except Exception:
        pass
    st.session_state["session_id"] = new_id
    return new_id


# ──────────────────────────────────────────────────────────────────
# Switch sesiune
# ──────────────────────────────────────────────────────────────────

def switch_session(new_session_id: str):
    """Comută la o altă sesiune."""
    from modules.ai.gemini_client import _cleanup_gfiles
    _cleanup_gfiles()

    st.session_state.session_id = new_session_id
    st.session_state.messages = []
    invalidate_session_cache()

    # Curățăm contextul sesiunii vechi
    for key in [
        "_conversation_summary", "_summary_cached_at", "_summary_for_sid",
        "_detected_subject", "_pending_user_msg", "system_prompt",
    ]:
        st.session_state.pop(key, None)

    # Curățăm toate cheile _mismatch_warned_*
    for k in [k for k in st.session_state.keys() if k.startswith("_mismatch_warned_")]:
        del st.session_state[k]

    # Actualizează localStorage cu noul SID
    components.html(
        f"<script>localStorage.setItem('profesor_session_id', {json.dumps(new_session_id)});</script>",
        height=0
    )


def invalidate_session_cache():
    """Marchează cache-ul sesiunilor ca expirat."""
    st.session_state["_sess_cache_dirty"] = True
    st.session_state["_sess_list_ts"] = 0


# ──────────────────────────────────────────────────────────────────
# Formatare timp
# ──────────────────────────────────────────────────────────────────

def format_time_ago(timestamp) -> str:
    """Formatează timestamp ca timp relativ (ex: '2 ore în urmă')."""
    if isinstance(timestamp, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.timestamp()
        except Exception:
            return "necunoscut"
    try:
        diff = time.time() - float(timestamp)
    except (TypeError, ValueError):
        return "necunoscut"

    if diff < 60:
        return "acum"
    elif diff < 3600:
        return f"{int(diff / 60)} min în urmă"
    elif diff < 86400:
        return f"{int(diff / 3600)}h în urmă"
    else:
        return f"{int(diff / 86400)} zile în urmă"


# ──────────────────────────────────────────────────────────────────
# JS sync localStorage ↔ URL
# ──────────────────────────────────────────────────────────────────

def inject_session_js():
    """
    JS care sincronizează SID-ul între Python și localStorage al browserului.

    Flux prima vizită:
      Python generează SID nou → pune în ?sid= → JS îl citește din URL → salvează în localStorage

    Flux revenire (restart, tab nou):
      localStorage are SID → JS pune ?sid= în URL → Python îl citește la startup
    """
    current_sid = st.session_state.get("session_id", "")
    components.html(f"""
    <script>
    (function() {{
        const SID_KEY    = 'profesor_session_id';
        const APIKEY_KEY = 'profesor_api_key';
        const params     = new URLSearchParams(window.parent.location.search);
        const sidInUrl   = params.get('sid');
        const pythonSid  = {json.dumps(current_sid)};

        if (sidInUrl && sidInUrl.length >= 16) {{
            localStorage.setItem(SID_KEY, sidInUrl);
            params.delete('sid');
            params.delete('apikey');
            const newUrl = window.parent.location.pathname +
                (params.toString() ? '?' + params.toString() : '');
            window.parent.history.replaceState(null, '', newUrl);
        }}

        if (!sidInUrl && (!pythonSid || pythonSid.length < 16)) {{
            const storedSid = localStorage.getItem(SID_KEY);
            if (storedSid && storedSid.length >= 16) {{
                params.set('sid', storedSid);
                params.delete('apikey');
                const newUrl = window.parent.location.pathname + '?' + params.toString();
                window.parent.history.replaceState(null, '', newUrl);
                window.parent.location.href = newUrl;
            }}
        }}

        const storedKey = localStorage.getItem(APIKEY_KEY);
        if (storedKey && storedKey.startsWith('AIza')) {{
            window.parent.postMessage({{ type: 'profesor_apikey', key: storedKey }}, '*');
        }}
    }})();
    </script>

    <script>
    window._saveApiKeyToStorage = function(key) {{
        if (key && key.startsWith('AIza')) {{
            localStorage.setItem('profesor_api_key', key);
        }}
    }};
    window._clearStoredApiKey = function() {{
        localStorage.removeItem('profesor_api_key');
    }};
    </script>
    """, height=0)


# ──────────────────────────────────────────────────────────────────
# Memory management
# ──────────────────────────────────────────────────────────────────

def trim_session_messages():
    """Limitează mesajele din session_state pentru a preveni memory leak."""
    if "messages" in st.session_state:
        current_count = len(st.session_state.messages)
        if current_count > MAX_MESSAGES_IN_MEMORY:
            excess = current_count - MAX_MESSAGES_IN_MEMORY
            first_msg = st.session_state.messages[0] if st.session_state.messages else None
            st.session_state.messages = st.session_state.messages[excess:]
            if first_msg and (not st.session_state.messages or st.session_state.messages[0] != first_msg):
                st.session_state.messages.insert(0, first_msg)
            st.toast(f"📝 Am arhivat {excess} mesaje vechi pentru performanță.", icon="📦")
