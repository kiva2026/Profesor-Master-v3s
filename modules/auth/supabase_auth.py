"""
modules/auth/supabase_auth.py — Toată logica Supabase: client, sesiuni, mesaje.

Funcții mutate din app.py:
  - get_supabase_client()
  - is_supabase_available() / _mark_supabase_offline() / _mark_supabase_online()
  - _get_offline_queue() / _flush_offline_queue()
  - init_db() / cleanup_old_sessions()
  - save_message_to_db() / load_history_from_db() / clear_history_db()
  - trim_db_messages()
  - session_exists_in_db() / register_session() / update_session_activity()
  - get_session_list() / save_message_with_limits()
  - _log()
"""
import time
import streamlit as st
from supabase import create_client, Client

from config import (
    get_app_id,
    MAX_MESSAGES_IN_MEMORY,
    MAX_MESSAGES_IN_DB_PER_SESSION,
    MAX_OFFLINE_QUEUE_SIZE,
    CLEANUP_DAYS_OLD,
)


# ──────────────────────────────────────────────────────────────────
# Logger centralizat
# ──────────────────────────────────────────────────────────────────

def _log(msg: str, level: str = "silent", exc: Exception = None):
    """
    Loghează un mesaj și opțional afișează un toast în interfață.

    level:
        "silent"  — doar print în consolă
        "info"    — toast verde
        "warning" — toast portocaliu
        "error"   — toast roșu
    """
    full_msg = f"{msg}: {exc}" if exc else msg
    print(full_msg)
    icon_map = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}
    if level in icon_map:
        try:
            st.toast(msg, icon=icon_map[level])
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────
# Supabase client
# ──────────────────────────────────────────────────────────────────

@st.cache_resource(ttl=3600)
def get_supabase_client() -> Client | None:
    """Returnează clientul Supabase (conexiunea e lazy, fără query de test)."""
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None


def is_supabase_available() -> bool:
    """Returnează statusul Supabase din cache."""
    return st.session_state.get("_sb_online", True)


def _mark_supabase_offline():
    was_online = st.session_state.get("_sb_online", True)
    st.session_state["_sb_online"] = False
    if was_online:
        st.toast("⚠️ Baza de date offline — modul local activat.", icon="📴")


def _mark_supabase_online():
    was_offline = not st.session_state.get("_sb_online", True)
    st.session_state["_sb_online"] = True
    if was_offline:
        st.toast("✅ Conexiunea restabilită!", icon="🟢")
        _flush_offline_queue()


# ──────────────────────────────────────────────────────────────────
# Coadă offline
# ──────────────────────────────────────────────────────────────────

def _get_offline_queue() -> list:
    queue = st.session_state.setdefault("_offline_queue", [])
    if len(queue) > MAX_OFFLINE_QUEUE_SIZE:
        st.session_state["_offline_queue"] = queue[-MAX_OFFLINE_QUEUE_SIZE:]
    return st.session_state["_offline_queue"]


def _flush_offline_queue():
    """Trimite mesajele din coada offline la Supabase când revine online."""
    MAX_FLUSH_RETRIES = 3
    if st.session_state.get("_flushing_queue", False):
        return
    st.session_state["_flushing_queue"] = True

    queue = _get_offline_queue()
    if not queue:
        st.session_state["_flushing_queue"] = False
        return

    client = get_supabase_client()
    if not client:
        st.session_state["_flushing_queue"] = False
        return

    failed = []
    try:
        retry_counts = st.session_state.setdefault("_offline_retry_counts", {})
        for item in queue:
            item_key = f"{item.get('session_id','')}-{item.get('timestamp','')}"
            retries = retry_counts.get(item_key, 0)
            if retries >= MAX_FLUSH_RETRIES:
                _log(f"Mesaj abandonat după {MAX_FLUSH_RETRIES} încercări", "silent")
                continue
            try:
                client.table("history").insert(item).execute()
                retry_counts.pop(item_key, None)
            except Exception:
                retry_counts[item_key] = retries + 1
                failed.append(item)
        st.session_state["_offline_queue"] = failed
        st.session_state["_offline_retry_counts"] = retry_counts
    finally:
        st.session_state["_flushing_queue"] = False

    successful = len(queue) - len(failed)
    if successful > 0:
        st.toast(f"✅ {successful} mesaje sincronizate.", icon="☁️")


# ──────────────────────────────────────────────────────────────────
# DB init & cleanup
# ──────────────────────────────────────────────────────────────────

def init_db():
    """Verifică conexiunea la Supabase. Dacă e offline, activează modul local."""
    online = is_supabase_available()
    if not online:
        st.warning(
            "📴 **Modul offline activ** — conversația se păstrează în memorie. "
            "Istoricul va fi sincronizat automat când conexiunea revine.",
            icon="⚠️"
        )


def cleanup_old_sessions(days_old: int = CLEANUP_DAYS_OLD):
    """Șterge sesiunile vechi — rulează cel mult o dată pe zi."""
    if time.time() - st.session_state.get("_last_cleanup", 0) < 86400:
        return
    st.session_state["_last_cleanup"] = time.time()
    try:
        supabase = get_supabase_client()
        if not supabase:
            return
        cutoff = time.time() - (days_old * 24 * 60 * 60)
        supabase.table("history").delete().lt("timestamp", cutoff).eq("app_id", get_app_id()).execute()
        supabase.table("sessions").delete().lt("last_active", cutoff).eq("app_id", get_app_id()).execute()
    except Exception as e:
        _log("Eroare la curățarea sesiunilor vechi", "silent", e)


# ──────────────────────────────────────────────────────────────────
# Mesaje
# ──────────────────────────────────────────────────────────────────

def save_message_to_db(session_id: str, role: str, content: str):
    """Salvează un mesaj în Supabase. Dacă e offline, pune în coada locală."""
    record = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": time.time(),
        "app_id": get_app_id(),
    }
    if not is_supabase_available():
        q = _get_offline_queue()
        if len(q) < MAX_OFFLINE_QUEUE_SIZE:
            q.append(record)
        return
    try:
        client = get_supabase_client()
        client.table("history").insert(record).execute()
        _mark_supabase_online()
    except Exception as e:
        _log("Mesajul nu a putut fi salvat", "warning", e)
        _mark_supabase_offline()
        q = _get_offline_queue()
        if len(q) < MAX_OFFLINE_QUEUE_SIZE:
            q.append(record)


def load_history_from_db(session_id: str, limit: int = MAX_MESSAGES_IN_MEMORY) -> list:
    """Încarcă istoricul din Supabase. Fallback: returnează ce e în session_state."""
    if not is_supabase_available():
        st.session_state["_history_may_be_incomplete"] = True
        return st.session_state.get("messages", [])
    try:
        client = get_supabase_client()
        response = (
            client.table("history")
            .select("role, content, timestamp")
            .eq("session_id", session_id)
            .eq("app_id", get_app_id())
            .order("timestamp", desc=False)
            .limit(limit)
            .execute()
        )
        return [{"role": row["role"], "content": row["content"]} for row in response.data]
    except Exception as e:
        _log("Eroare la încărcarea istoricului", "silent", e)
        return st.session_state.get("messages", [])[-limit:]


def clear_history_db(session_id: str):
    """Șterge istoricul pentru o sesiune din Supabase."""
    from modules.utils.session import invalidate_session_cache, is_valid_session_id
    if not is_valid_session_id(session_id):
        _log(f"clear_history_db: session_id invalid: {str(session_id)[:20]}", "warning")
        return
    try:
        supabase = get_supabase_client()
        supabase.table("history").delete().eq("session_id", session_id).eq("app_id", get_app_id()).execute()
        invalidate_session_cache()
        for key in ["_conversation_summary", "_summary_cached_at", "_summary_for_sid", "_mismatch_warned"]:
            st.session_state.pop(key, None)
    except Exception as e:
        _log("Istoricul nu a putut fi șters", "warning", e)


def trim_db_messages(session_id: str):
    """Limitează mesajele din DB pentru o sesiune (previne memory leak)."""
    try:
        supabase = get_supabase_client()
        count_resp = (
            supabase.table("history")
            .select("id", count="exact")
            .eq("session_id", session_id)
            .eq("app_id", get_app_id())
            .execute()
        )
        count = count_resp.count or 0
        if count > MAX_MESSAGES_IN_DB_PER_SESSION:
            to_delete = count - MAX_MESSAGES_IN_DB_PER_SESSION
            old_resp = (
                supabase.table("history")
                .select("id")
                .eq("session_id", session_id)
                .eq("app_id", get_app_id())
                .order("timestamp", desc=False)
                .limit(to_delete)
                .execute()
            )
            ids_to_delete = [row["id"] for row in old_resp.data]
            if ids_to_delete:
                supabase.table("history").delete().in_("id", ids_to_delete).execute()
    except Exception as e:
        _log("Eroare la curățarea DB", "silent", e)


def save_message_with_limits(session_id: str, role: str, content: str):
    """Salvează mesaj și verifică limitele de memorie."""
    from modules.utils.session import invalidate_session_cache, trim_session_messages
    save_message_to_db(session_id, role, content)
    invalidate_session_cache()
    if len(st.session_state.get("messages", [])) % 50 == 0:
        trim_db_messages(session_id)
    trim_session_messages()


# ──────────────────────────────────────────────────────────────────
# Sesiuni Supabase
# ──────────────────────────────────────────────────────────────────

def session_exists_in_db(session_id: str) -> bool:
    """Verifică dacă un session_id există deja în Supabase."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("sessions")
            .select("session_id")
            .eq("session_id", session_id)
            .eq("app_id", get_app_id())
            .limit(1)
            .execute()
        )
        return len(response.data) > 0
    except Exception:
        return False


def register_session(session_id: str):
    """Înregistrează o sesiune nouă în Supabase."""
    if not is_supabase_available():
        return
    try:
        client = get_supabase_client()
        now = time.time()
        client.table("sessions").upsert({
            "session_id": session_id,
            "created_at": now,
            "last_active": now,
            "app_id": get_app_id(),
        }).execute()
    except Exception as e:
        _log("Eroare la înregistrarea sesiunii", "silent", e)


def update_session_activity(session_id: str):
    """Actualizează timestamp-ul activității — cel mult o dată la 5 minute."""
    last = st.session_state.get("_last_activity_update", 0)
    if time.time() - last < 300:
        return
    st.session_state["_last_activity_update"] = time.time()
    if not is_supabase_available():
        return
    try:
        client = get_supabase_client()
        client.table("sessions").update({"last_active": time.time()}).eq("session_id", session_id).execute()
    except Exception as e:
        _log("Eroare la actualizarea sesiunii", "silent", e)


def get_session_list(limit: int = 20) -> list[dict]:
    """Returnează lista sesiunilor folosind view-ul session_previews din Supabase."""
    cache_ts   = st.session_state.get("_sess_list_ts", 0)
    cache_val  = st.session_state.get("_sess_list_cache", None)
    force      = st.session_state.get("_sess_cache_dirty", False)
    if force:
        st.session_state["_sess_cache_dirty"] = False

    if not force and cache_val is not None and (time.time() - cache_ts) < 5:
        return cache_val

    try:
        supabase = get_supabase_client()
        resp = (
            supabase.table("session_previews")
            .select("session_id, last_active, msg_count, preview")
            .eq("app_id", get_app_id())
            .gt("msg_count", 0)
            .order("last_active", desc=True)
            .limit(limit)
            .execute()
        )
        result = resp.data or []
        st.session_state["_sess_list_cache"] = result
        st.session_state["_sess_list_ts"]    = time.time()
        return result
    except Exception as e:
        _log("Eroare la încărcarea sesiunilor", "silent", e)
        return cache_val or []
