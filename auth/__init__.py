"""modules/auth — Autentificare și baza de date Supabase."""
from .supabase_auth import (
    get_supabase_client,
    is_supabase_available,
    init_db,
    cleanup_old_sessions,
    save_message_to_db,
    load_history_from_db,
    clear_history_db,
    trim_db_messages,
    save_message_with_limits,
    session_exists_in_db,
    register_session,
    update_session_activity,
    get_session_list,
    _log,
)

__all__ = [
    "get_supabase_client", "is_supabase_available", "init_db",
    "cleanup_old_sessions", "save_message_to_db", "load_history_from_db",
    "clear_history_db", "trim_db_messages", "save_message_with_limits",
    "session_exists_in_db", "register_session", "update_session_activity",
    "get_session_list", "_log",
]
