"""modules/ai — Interfața cu Google Gemini AI."""
from .gemini_client import (
    run_chat_with_rotation,
    get_context_for_ai,
    summarize_conversation,
    _cleanup_gfiles,
    _is_gfile_active,
)

__all__ = [
    "run_chat_with_rotation",
    "get_context_for_ai",
    "summarize_conversation",
    "_cleanup_gfiles",
    "_is_gfile_active",
]
