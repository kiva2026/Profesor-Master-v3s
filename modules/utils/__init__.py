"""modules/utils — Utilitare generale."""
from .session import (
    generate_unique_session_id,
    is_valid_session_id,
    get_or_create_session_id,
    switch_session,
    invalidate_session_cache,
    format_time_ago,
    inject_session_js,
    trim_session_messages,
)
from .validators import is_valid_google_api_key, clean_api_key

__all__ = [
    "generate_unique_session_id",
    "is_valid_session_id",
    "get_or_create_session_id",
    "switch_session",
    "invalidate_session_cache",
    "format_time_ago",
    "inject_session_js",
    "trim_session_messages",
    "is_valid_google_api_key",
    "clean_api_key",
]
