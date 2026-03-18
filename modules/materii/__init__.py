"""modules/materii — Sistem modular de prompt-uri per materie."""
from .base import get_system_prompt, update_system_prompt_for_subject, SYSTEM_PROMPT
from .detect import detect_subject_from_text

__all__ = [
    "get_system_prompt",
    "update_system_prompt_for_subject",
    "SYSTEM_PROMPT",
    "detect_subject_from_text",
]
