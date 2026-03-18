"""
modules/ai/gemini_client.py — Interfața cu Google Gemini AI.

Funcții mutate din app.py:
  - _cleanup_gfiles()
  - _get_prompt_hash() / _get_or_create_cache() / _invalidate_cache_for_key()
  - run_chat_with_rotation()
  - get_context_for_ai()
  - summarize_conversation()
"""
import hashlib
import time
import streamlit as st
from google import genai
from google.genai import types as genai_types

from config import (
    GEMINI_MODEL,
    _CACHE_MODEL,
    _CACHE_TTL_SECONDS,
    _CACHE_REFRESH_AT,
    SAFETY_SETTINGS as safety_settings,
    SUMMARIZE_AFTER_MESSAGES,
    MESSAGES_KEPT_AFTER_SUMMARY,
    MAX_MESSAGES_TO_SEND_TO_AI,
)
from modules.auth.supabase_auth import _log


# ──────────────────────────────────────────────────────────────────
# Curățare fișiere Google Files API
# ──────────────────────────────────────────────────────────────────

def _cleanup_gfiles() -> None:
    """Șterge toate fișierele uploadate pe Google Files API din sesiunea curentă.
    Apelat la switch sesiune, conversație nouă și explicit de utilizator.
    """
    gfile_keys = [k for k in st.session_state.keys() if k.startswith("_gfile_")]
    if not gfile_keys:
        return
    try:
        _keys = st.session_state.get("_api_keys_list", [])
        _idx  = st.session_state.get("key_index", 0)
        if not _keys:
            return
        _client = genai.Client(api_key=_keys[_idx])
        for k in gfile_keys:
            gf = st.session_state.pop(k, None)
            if gf:
                try:
                    _client.files.delete(gf.name)
                except Exception:
                    pass  # expirat deja sau alt motiv — ignorăm
    except Exception:
        for k in gfile_keys:
            st.session_state.pop(k, None)


def _is_gfile_active(gfile) -> bool:
    """Verifică dacă un fișier Google este activ."""
    state_str  = str(gfile.state)
    state_name = getattr(gfile.state, "name", "")
    return state_str in ("FileState.ACTIVE", "ACTIVE") or state_name == "ACTIVE"


# ──────────────────────────────────────────────────────────────────
# Context Caching helpers
# ──────────────────────────────────────────────────────────────────

def _get_prompt_hash(prompt_text: str, api_key: str) -> str:
    """Generează un hash scurt unic pentru (prompt, cheie)."""
    return hashlib.sha256(f"{api_key}:{prompt_text}".encode()).hexdigest()[:16]


def _get_or_create_cache(client: "genai.Client", prompt_text: str, api_key: str) -> str | None:
    """Returnează numele unui CachedContent valid, sau None dacă caching eșuează.

    1. Verifică dacă avem un cache valid în st.session_state["_prompt_cache_store"]
    2. Dacă nu (sau expirat), creează unul nou via API
    3. La orice eroare → returnează None (fallback fără caching)
    """
    cache_store = st.session_state.setdefault("_prompt_cache_store", {})
    cache_key   = _get_prompt_hash(prompt_text, api_key)
    now         = time.time()

    # Curăță intrările expirate
    st.session_state["_prompt_cache_store"] = {
        k: v for k, v in cache_store.items()
        if v.get("expires_at", 0) > now
    }
    cache_store = st.session_state["_prompt_cache_store"]

    existing = cache_store.get(cache_key)
    if existing and (existing["expires_at"] - now) > (_CACHE_TTL_SECONDS - _CACHE_REFRESH_AT):
        return existing["name"]

    try:
        cached = client.caches.create(
            model=_CACHE_MODEL,
            config=genai_types.CreateCachedContentConfig(
                system_instruction=prompt_text,
                ttl=f"{_CACHE_TTL_SECONDS}s",
            ),
        )
        st.session_state["_prompt_cache_store"][cache_key] = {
            "name":            cached.name,
            "expires_at":      now + _CACHE_TTL_SECONDS,
            "api_key_prefix":  api_key[:8],
        }
        return cached.name
    except Exception as e:
        _log(f"Context caching indisponibil (fallback fără caching): {e}", "silent")
        return None


def _invalidate_cache_for_key(api_key: str) -> None:
    """Invalidează toate intrările din cache pentru o cheie API dată."""
    cache_store = st.session_state.get("_prompt_cache_store", {})
    prefix = api_key[:8]
    st.session_state["_prompt_cache_store"] = {
        k: v for k, v in cache_store.items()
        if v.get("api_key_prefix") != prefix
    }


# ──────────────────────────────────────────────────────────────────
# run_chat_with_rotation — funcția principală de apel AI
# ──────────────────────────────────────────────────────────────────

def run_chat_with_rotation(history_obj, payload, system_prompt=None):
    """Rulează chat cu rotație automată a cheilor API, fallback modele și context caching.

    Args:
        history_obj:   Lista de mesaje anterioare (format Gemini: [{role, parts}])
        payload:       Lista de conținuturi pentru mesajul curent (text + fișiere)
        system_prompt: Prompt de sistem custom (opțional; altfel citit din session_state)

    Yields:
        Chunks de text din răspunsul AI (streaming)
    """
    from modules.materii.base import SYSTEM_PROMPT as DEFAULT_SYSTEM_PROMPT

    # Cheile API sunt stocate în session_state de app.py
    keys = st.session_state.get("_api_keys_list", [])

    if not keys:
        raise Exception(
            "Nicio cheie API Gemini configurată. "
            "Adaugă cel puțin o cheie în st.secrets['GEMINI_KEYS'] sau introdu-o manual în sidebar."
        )

    MODEL_WITH_CACHE         = _CACHE_MODEL
    MODEL_FALLBACKS_NO_CACHE = [GEMINI_MODEL]

    active_prompt = system_prompt or st.session_state.get("system_prompt") or DEFAULT_SYSTEM_PROMPT
    max_retries   = max(len(keys) * 3, 6)
    _deadline     = time.time() + 45
    _use_cache    = st.session_state.get("_ctx_cache_enabled", True)

    for attempt in range(max_retries):
        if st.session_state.key_index >= len(keys):
            st.session_state.key_index = 0
        current_key = keys[st.session_state.key_index]

        # Selectăm modelul
        if _use_cache and attempt == 0:
            model_name = MODEL_WITH_CACHE
        else:
            fb_idx = min(
                (attempt - 1) // max(len(keys), 1) if not _use_cache else attempt // max(len(keys), 1),
                len(MODEL_FALLBACKS_NO_CACHE) - 1
            )
            model_name = MODEL_FALLBACKS_NO_CACHE[max(fb_idx, 0)]

        try:
            gemini_client = genai.Client(api_key=current_key)

            # --- Context Caching ---
            cached_content_name = None
            if _use_cache and model_name == MODEL_WITH_CACHE:
                cached_content_name = _get_or_create_cache(gemini_client, active_prompt, current_key)

            if cached_content_name:
                gen_config = genai_types.GenerateContentConfig(
                    cached_content=cached_content_name,
                    safety_settings=[
                        genai_types.SafetySetting(category=s["category"], threshold=s["threshold"])
                        for s in safety_settings
                    ],
                )
            else:
                gen_config = genai_types.GenerateContentConfig(
                    system_instruction=active_prompt,
                    safety_settings=[
                        genai_types.SafetySetting(category=s["category"], threshold=s["threshold"])
                        for s in safety_settings
                    ],
                )

            # Construiește history-ul
            history_new = []
            for msg in history_obj:
                parts_list = msg["parts"] if isinstance(msg["parts"], list) else [msg["parts"]]
                history_new.append(
                    genai_types.Content(
                        role=msg["role"],
                        parts=[
                            genai_types.Part(text=p) if isinstance(p, str)
                            else genai_types.Part(file_data=genai_types.FileData(
                                file_uri=p.uri, mime_type=p.mime_type
                            ))
                            for p in parts_list
                        ]
                    )
                )

            # Construiește payload-ul curent
            current_parts = []
            for p in (payload if isinstance(payload, list) else [payload]):
                if isinstance(p, str):
                    current_parts.append(genai_types.Part(text=p))
                elif hasattr(p, "uri"):
                    current_parts.append(genai_types.Part(
                        file_data=genai_types.FileData(file_uri=p.uri, mime_type=p.mime_type)
                    ))
                else:
                    current_parts.append(genai_types.Part(text=str(p)))

            all_contents = history_new + [genai_types.Content(role="user", parts=current_parts)]

            response_stream = gemini_client.models.generate_content_stream(
                model=model_name,
                contents=all_contents,
                config=gen_config,
            )

            # Streaming + token tracking
            chunks = []
            for chunk in response_stream:
                text = ""
                if hasattr(chunk, "candidates") and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate, "content") and candidate.content:
                            for part in candidate.content.parts:
                                if hasattr(part, "text") and part.text:
                                    text += part.text
                elif hasattr(chunk, "text") and chunk.text:
                    text = chunk.text

                if text:
                    chunks.append(text)
                    yield text

                # Token usage tracking
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    _key_id = f"_tokens_key_{st.session_state.key_index}"
                    _usage  = st.session_state.setdefault(_key_id, {"prompt": 0, "output": 0, "calls": 0})
                    _um     = chunk.usage_metadata
                    if hasattr(_um, "prompt_token_count") and _um.prompt_token_count:
                        _usage["prompt"] += _um.prompt_token_count
                    if hasattr(_um, "candidates_token_count") and _um.candidates_token_count:
                        _usage["output"] += _um.candidates_token_count
                    _usage["calls"] += 1

            # Succes — resetăm contorul de rotații
            st.session_state.pop("_quota_rotations", None)
            return

        except Exception as e:
            error_msg = str(e).lower()

            _is_key_error = (
                "api key" in error_msg
                or "invalid api key" in error_msg.lower()
                or "429" in error_msg
                or "quota" in error_msg.lower()
                or "rate_limit" in error_msg.lower()
            )

            if _is_key_error:
                _invalidate_cache_for_key(current_key)
                _quota_key  = "_quota_rotations"
                rotations   = st.session_state.get(_quota_key, 0) + 1
                st.session_state[_quota_key] = rotations
                if len(keys) <= 1 or rotations >= len(keys):
                    st.session_state.pop(_quota_key, None)
                    raise Exception(
                        "Toate cheile API sunt epuizate sau invalide. "
                        "Reîncearcă mai târziu sau adaugă o cheie personală în sidebar. 🔑"
                    )
                st.session_state.key_index = (st.session_state.key_index + 1) % len(keys)
                st.toast(f"⚠️ Cheie invalidă/epuizată — schimb la cheia {st.session_state.key_index + 1}...", icon="🔄")
                time.sleep(0.5)
                continue

            elif "400" in error_msg:
                raise Exception(f"❌ Cerere invalidă (400): {error_msg}") from e

            elif "503" in error_msg or "overloaded" in error_msg.lower() or "resource_exhausted" in error_msg.lower():
                if time.time() >= _deadline:
                    raise Exception("Serviciul AI este supraîncărcat. Încearcă din nou în câteva secunde. 🐢") from e
                wait = min(0.5 * (2 ** attempt), 5)
                st.toast("🐢 Server ocupat, reîncerc...", icon="⏳")
                time.sleep(wait)
                continue

            else:
                raise e

    st.session_state.pop("_quota_rotations", None)
    raise Exception(
        "Ne pare rău, serviciul AI este momentan supraîncărcat. "
        "Încearcă din nou în câteva secunde. Dacă problema persistă, verifică cheia API. 🙏"
    )


# ──────────────────────────────────────────────────────────────────
# Context management pentru AI
# ──────────────────────────────────────────────────────────────────

def summarize_conversation(messages: list) -> str | None:
    """Cere AI-ului să rezume conversația. Returnează textul sau None dacă eșuează."""
    if not messages or len(messages) < 6:
        return None
    try:
        msgs_to_summarize = messages[:-MESSAGES_KEPT_AFTER_SUMMARY]
        if len(msgs_to_summarize) < 4:
            return None

        history_for_summary = []
        for msg in msgs_to_summarize:
            role = "model" if msg["role"] == "assistant" else "user"
            history_for_summary.append({"role": role, "parts": [msg["content"][:500]]})

        summary_prompt = (
            "Fă un rezumat SCURT (maxim 200 cuvinte) al conversației de mai sus. "
            "Include: subiectele discutate, conceptele explicate, exercițiile rezolvate "
            "și orice context important despre nivelul și înțelegerea elevului. "
            "Scrie la persoana a 3-a: 'Elevul a întrebat despre... Am explicat...'"
        )
        chunks  = list(run_chat_with_rotation(history_for_summary, [summary_prompt]))
        summary = "".join(chunks).strip()
        return summary if len(summary) > 20 else None
    except Exception:
        return None


def get_context_for_ai(messages: list) -> list:
    """Pregătește contextul pentru AI cu limită de mesaje și rezumare inteligentă.

    Strategie:
      1. Există rezumat pre-generat → rezumat + ultimele N mesaje recente
      2. Conversație scurtă → trimite totul
      3. Conversație lungă fără rezumat → generează rezumat acum
      4. Fallback → primul mesaj + ultimele MAX_MESSAGES_TO_SEND_TO_AI
    """
    cached_summary = st.session_state.get("_conversation_summary")
    cached_at      = st.session_state.get("_summary_cached_at", 0)

    if cached_summary:
        # Regenerează la fiecare 10 mesaje noi
        if (len(messages) - cached_at) >= 10:
            new_summary = summarize_conversation(messages)
            if new_summary:
                cached_summary = new_summary
                st.session_state["_conversation_summary"] = new_summary
                st.session_state["_summary_cached_at"]    = len(messages)

        summary_msg = {
            "role": "user",
            "content": (
                "[CONTEXT CONVERSAȚIE ANTERIOARĂ — citește înainte de a răspunde]\n"
                f"{cached_summary}\n"
                "[MESAJE RECENTE — continuare directă]"
            )
        }
        summary_ack = {
            "role": "assistant",
            "content": "Am înțeles contextul. Continuăm de unde am rămas."
        }
        return [summary_msg, summary_ack] + messages[-MESSAGES_KEPT_AFTER_SUMMARY:]

    if len(messages) <= MAX_MESSAGES_TO_SEND_TO_AI:
        return messages

    if len(messages) >= SUMMARIZE_AFTER_MESSAGES:
        summary = summarize_conversation(messages)
        if summary:
            st.session_state["_conversation_summary"] = summary
            st.session_state["_summary_cached_at"]    = len(messages)
            summary_msg = {
                "role": "user",
                "content": (
                    "[CONTEXT CONVERSAȚIE ANTERIOARĂ — citește înainte de a răspunde]\n"
                    f"{summary}\n"
                    "[MESAJE RECENTE — continuare directă]"
                )
            }
            summary_ack = {
                "role": "assistant",
                "content": "Am înțeles contextul. Continuăm de unde am rămas."
            }
            return [summary_msg, summary_ack] + messages[-MESSAGES_KEPT_AFTER_SUMMARY:]

    # Fallback
    first_message   = messages[0] if messages else None
    recent_messages = messages[-MAX_MESSAGES_TO_SEND_TO_AI:]
    if first_message and first_message not in recent_messages:
        return [first_message] + recent_messages
    return recent_messages
