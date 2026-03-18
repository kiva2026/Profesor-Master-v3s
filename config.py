"""
config.py — Singura sursă de adevăr pentru constante și configurații globale.

Toate constantele din app.py originale sunt centralizate aici.
Importă din acest modul oriunde ai nevoie de configurații.
"""
import re
import streamlit as st

# ══════════════════════════════════════════════════════════════════
# APP INSTANCE ID
# ══════════════════════════════════════════════════════════════════
_APP_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')

@st.cache_data(ttl=3600)
def get_app_id() -> str:
    """Returnează ID-ul aplicației. Validat anti-injection.
    Cache-uit cu st.cache_data — st.secrets accesează discul la fiecare apel.
    """
    try:
        raw = str(st.secrets.get("APP_INSTANCE_ID", "default")).strip() or "default"
    except Exception:
        raw = "default"
    return raw if _APP_ID_PATTERN.match(raw) else "default"


# ══════════════════════════════════════════════════════════════════
# LIMITE MEMORIE & DB
# ══════════════════════════════════════════════════════════════════
MAX_MESSAGES_IN_MEMORY      = 100
MAX_MESSAGES_TO_SEND_TO_AI  = 20
MAX_MESSAGES_IN_DB_PER_SESSION = 500
CLEANUP_DAYS_OLD            = 90   # Păstrăm istoricul 90 de zile

# ══════════════════════════════════════════════════════════════════
# GEMINI MODEL
# ══════════════════════════════════════════════════════════════════
GEMINI_MODEL              = "gemini-2.5-flash"
SUMMARIZE_AFTER_MESSAGES  = 30    # Rezumăm când depășim acest număr
MESSAGES_KEPT_AFTER_SUMMARY = 10  # Mesaje recente păstrate după rezumare

# Context caching
_CACHE_MODEL          = "gemini-2.5-flash"
_CACHE_TTL_SECONDS    = 600   # 10 minute
_CACHE_REFRESH_AT     = 60    # Reîmprospătează cu 60s înainte de expirare

# ══════════════════════════════════════════════════════════════════
# OFFLINE QUEUE
# ══════════════════════════════════════════════════════════════════
MAX_OFFLINE_QUEUE_SIZE = 50   # Previne memory leak când Supabase e offline

# ══════════════════════════════════════════════════════════════════
# SESSION ID
# ══════════════════════════════════════════════════════════════════
# Regex precompilat: doar hex lowercase, 16-64 caractere
SESSION_ID_RE = re.compile(r'^[a-f0-9]{16,64}$')

# ══════════════════════════════════════════════════════════════════
# MATERII
# ══════════════════════════════════════════════════════════════════
MATERII: dict[str, str | None] = {
    "🤖 Automat":            None,
    "📐 Matematică":         "matematică",
    "⚡ Fizică Real":         "fizică_real",
    "⚡ Fizică Tehnologic":   "fizică_tehnologic",
    "🧪 Chimie":             "chimie",
    "📖 Română":             "limba și literatura română",
    "🇫🇷 Franceză":          "limba franceză",
    "🇬🇧 Engleză":           "limba engleză",
    "🇩🇪 Germană":           "limba germană",
    "🌍 Geografie":          "geografie",
    "🏛️ Istorie":            "istorie",
    "💻 Informatică":        "informatică",
    "🧬 Biologie":           "biologie",
}

AUTOMAT_LABEL = "🤖 Automat"

# Mapare inversă: cod → label (pentru toast-uri și afișări)
MATERII_LABEL: dict[str, str] = {v: k for k, v in MATERII.items() if v is not None}

# ══════════════════════════════════════════════════════════════════
# SAFETY SETTINGS (Gemini)
# ══════════════════════════════════════════════════════════════════
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# ══════════════════════════════════════════════════════════════════
# TYPING HTML INDICATOR
# ══════════════════════════════════════════════════════════════════
TYPING_HTML = """
<div class="typing-indicator">
    <div class="typing-dots"><span></span><span></span><span></span></div>
    <span>Domnul Profesor scrie...</span>
</div>
"""
