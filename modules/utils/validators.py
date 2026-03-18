"""
modules/utils/validators.py — Funcții de validare a inputurilor.
"""
import re

# Validare API key Google AI
def is_valid_google_api_key(key: str) -> bool:
    """Verifică dacă cheia arată ca o cheie Google AI validă."""
    if not key or not isinstance(key, str):
        return False
    clean = key.strip().strip('"').strip("'")
    return clean.startswith("AIza") and len(clean) > 20


def clean_api_key(key: str) -> str:
    """Curăță o cheie API de spații și ghilimele."""
    return key.strip().strip('"').strip("'")
