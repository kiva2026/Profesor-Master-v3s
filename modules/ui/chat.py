"""
modules/ui/chat.py — Gestionarea chat-ului principal.

Funcții:
  - render_chat_history()     — afișează mesajele + butoanele quick actions
  - handle_quick_actions()    — procesează acțiunile rapide (reexplain, similar, strategy)
  - handle_chat_input()       — procesează inputul utilizatorului
  - handle_pending_messages() — mesaje în așteptare (materie nedetectată, retry)
"""
import re
import time
import streamlit as st

from config import MATERII, MATERII_LABEL, TYPING_HTML
from modules.ai.gemini_client import run_chat_with_rotation, get_context_for_ai
from modules.auth.supabase_auth import save_message_with_limits
from modules.materii import get_system_prompt, update_system_prompt_for_subject
from modules.materii.detect import detect_subject_from_text
from modules.ui.svg_renderer import render_message_with_svg


# ──────────────────────────────────────────────────────────────────
# Randare istoric chat
# ──────────────────────────────────────────────────────────────────

def render_chat_history():
    """Afișează toate mesajele din session_state + quick action buttons sub ultimul."""
    messages = st.session_state.get("messages", [])

    for i, msg in enumerate(messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_message_with_svg(msg["content"])
            else:
                st.markdown(msg["content"])

        # Butoanele apar DOAR sub ultimul mesaj al profesorului
        if msg["role"] == "assistant" and i == len(messages) - 1:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Nu am înțeles", key="qa_reexplain",
                             use_container_width=True,
                             help="Explică altfel, cu o altă analogie"):
                    st.session_state["_quick_action"] = "reexplain"
                    st.rerun()
            with col2:
                if st.button("✏️ Exercițiu similar", key="qa_similar",
                             use_container_width=True,
                             help="Generează un exercițiu similar pentru practică"):
                    st.session_state["_quick_action"] = "similar"
                    st.rerun()
            with col3:
                if st.button("🧠 Explică strategia", key="qa_strategy",
                             use_container_width=True,
                             help="Cum să gândești acest tip de problemă"):
                    st.session_state["_quick_action"] = "strategy"
                    st.rerun()


# ──────────────────────────────────────────────────────────────────
# Quick Actions handler
# ──────────────────────────────────────────────────────────────────

def handle_quick_actions():
    """Procesează acțiunile rapide (reexplain, similar, strategy)."""
    if not st.session_state.get("_quick_action"):
        return

    action = st.session_state.pop("_quick_action")

    # Găsim ultimul mesaj al asistentului și utilizatorului
    last_assistant_msg = ""
    last_user_msg      = ""
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and not last_assistant_msg:
            last_assistant_msg = msg["content"]
        if msg["role"] == "user" and not last_user_msg:
            last_user_msg = msg["content"]
        if last_assistant_msg and last_user_msg:
            break

    _clean  = lambda t: re.sub(r'\$\$[\s\S]*?\$\$|\$[^\$\n]*?\$|[*`#\\]', '', t).strip()
    _clean2 = lambda t: re.sub(r'\s+', ' ', _clean(t))

    if last_assistant_msg:
        _c = _clean2(last_assistant_msg)
        prev_topic = (_c[:120].rsplit(' ', 1)[0].rstrip('.,;:') + "...") if len(_c) > 120 else (_c or "subiectul anterior")
    else:
        prev_topic = "subiectul anterior"

    if last_user_msg:
        _cq = _clean2(last_user_msg)
        prev_question = (_cq[:100] if len(_cq) > 100 else _cq) or "întrebarea anterioară"
    else:
        prev_question = "întrebarea anterioară"

    _is_foreign_lang = st.session_state.get("materie_selectata") in ("limba engleză", "limba franceză", "limba germană")

    action_prompts = {
        "reexplain": (
            f"Nu am înțeles explicația ta despre: '{prev_topic}'. "
            f"Te rog să explici din nou, dar complet diferit — "
            f"altă analogie, altă ordine a pașilor, exemple mai simple din viața reală. "
            f"Evită exact aceleași cuvinte și structura anterioară."
        ),
        "similar": (
            f"Generează un exercițiu similar cu '{prev_question}', "
            + ("folosind alt cuvânt sau altă situație de comunicare, cu dificultate puțin mai mare. "
               if _is_foreign_lang else
               "cu date numerice diferite și dificultate puțin mai mare. ")
            + "Enunță exercițiul ÎNTÂI, apoi rezolvă-l complet pas cu pas."
        ),
        "strategy": (
            f"Explică-mi STRATEGIA de gândire pentru '{prev_question}': "
            f"cum recunosc că e acest tip, ce fac primul pas în minte, ce capcane să evit. "
            f"Fără calcule — vreau doar logica și gândirea din spate."
        ),
    }

    injected = action_prompts.get(action, "")
    if not injected:
        return

    with st.chat_message("user"):
        st.markdown(injected)
    st.session_state.messages.append({"role": "user", "content": injected})
    save_message_with_limits(st.session_state.session_id, "user", injected)

    context_messages = get_context_for_ai(st.session_state.messages)
    history_obj = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
        for m in context_messages
    ]

    st.session_state["_retry_history"] = history_obj
    st.session_state["_retry_payload"] = [injected]

    with st.chat_message("assistant"):
        placeholder  = st.empty()
        full_response = ""
        placeholder.markdown(TYPING_HTML, unsafe_allow_html=True)
        try:
            for chunk in run_chat_with_rotation(history_obj, [injected]):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.empty()
            render_message_with_svg(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message_with_limits(st.session_state.session_id, "assistant", full_response)
            st.session_state.pop("_retry_history", None)
            st.session_state.pop("_retry_payload", None)
        except Exception as e:
            placeholder.empty()
            _handle_stream_error(e)

    st.stop()


# ──────────────────────────────────────────────────────────────────
# Mesaje în așteptare
# ──────────────────────────────────────────────────────────────────

def handle_pending_messages():
    """Procesează mesaje în așteptare (materie nedetectată, fizică ambiguă, retry)."""
    # ── Retry după eroare cheie API ──
    if st.session_state.get("_pending_retry"):
        st.session_state.pop("_pending_retry", None)
        _retry_history = st.session_state.get("_retry_history", [])
        _retry_payload = st.session_state.get("_retry_payload", [])
        if _retry_history or _retry_payload:
            with st.chat_message("assistant"):
                _rph = st.empty()
                _rfull = ""
                try:
                    for _chunk in run_chat_with_rotation(_retry_history, _retry_payload):
                        _rfull += _chunk
                        if "<svg" in _rfull or ("<path" in _rfull and "stroke=" in _rfull):
                            _rph.markdown(_rfull.split("<path")[0] + "\n\n*🎨 Domnul Profesor desenează...*\n\n▌")
                        else:
                            _rph.markdown(_rfull + "▌")
                    _rph.empty()
                    render_message_with_svg(_rfull)
                    st.session_state.messages.append({"role": "assistant", "content": _rfull})
                    save_message_with_limits(st.session_state.session_id, "assistant", _rfull)
                    st.session_state.pop("_retry_history", None)
                    st.session_state.pop("_retry_payload", None)
                except Exception as _re:
                    _rph.empty()
                    st.error(f"❌ Eroare și la reîncercare: {_re}")
        st.stop()

    # ── Fizică ambiguă ──
    if st.session_state.get("_pending_user_msg") and st.session_state.get("_pending_fizica_ambigua"):
        _pending_msg = st.session_state["_pending_user_msg"]
        with st.chat_message("assistant"):
            st.markdown(
                "**Am detectat că întrebarea e despre Fizică!** 🔬\n\n"
                "Pentru a-ți răspunde corect conform programei, spune-mi la ce profil ești:"
            )
            col_r, col_t = st.columns(2)
            with col_r:
                if st.button("📐 Fizică Real\n*(Matematică-Informatică, Științe ale naturii)*",
                             key="_pick_fizica_real", use_container_width=True, type="primary"):
                    update_system_prompt_for_subject("fizică_real")
                    st.session_state["_detected_subject"] = "fizică_real"
                    st.session_state.pop("_pending_user_msg", None)
                    st.session_state.pop("_pending_fizica_ambigua", None)
                    st.session_state["_suggested_question"] = _pending_msg
                    st.rerun()
            with col_t:
                if st.button("🔧 Fizică Tehnologic\n*(Filiera tehnologică)*",
                             key="_pick_fizica_tehnolog", use_container_width=True):
                    update_system_prompt_for_subject("fizică_tehnolog")
                    st.session_state["_detected_subject"] = "fizică_tehnolog"
                    st.session_state.pop("_pending_user_msg", None)
                    st.session_state.pop("_pending_fizica_ambigua", None)
                    st.session_state["_suggested_question"] = _pending_msg
                    st.rerun()
        st.stop()

    # ── Materie nedetectată — întreabă elevul ──
    if st.session_state.get("_pending_user_msg") and st.session_state.get("materie_selectata") is None:
        _pending_msg = st.session_state["_pending_user_msg"]
        with st.chat_message("assistant"):
            st.markdown(
                "**Nu am reușit să detectez automat materia** din mesajul tău. 🤔\n\n"
                "Alege materia din sidebar sau spune-mi direct care e:"
            )
            materii_disponibile = [k for k, v in MATERII.items() if v is not None]
            for i in range(0, len(materii_disponibile), 3):
                cols = st.columns(3)
                for j, m_label in enumerate(materii_disponibile[i:i+3]):
                    with cols[j]:
                        if st.button(m_label, key=f"_pick_mat_{m_label}", use_container_width=True):
                            materie_cod = MATERII[m_label]
                            update_system_prompt_for_subject(materie_cod)
                            st.session_state["materie_selectata"] = materie_cod
                            st.session_state.pop("_pending_user_msg", None)
                            st.session_state["_suggested_question"] = _pending_msg
                            st.rerun()
        st.stop()


# ──────────────────────────────────────────────────────────────────
# Chat input principal
# ──────────────────────────────────────────────────────────────────

def handle_chat_input(media_content=None):
    """Procesează inputul din câmpul de chat."""
    user_input = st.chat_input("Întreabă profesorul...")
    if not user_input:
        return

    # Debounce
    now_ts   = time.time()
    last_msg = st.session_state.get("_last_user_msg", "")
    last_ts  = st.session_state.get("_last_msg_ts", 0)
    if user_input.strip() == last_msg.strip() and (now_ts - last_ts) < 2.5:
        st.toast("⏳ Mesaj duplicat ignorat.", icon="🔁")
        st.stop()
    st.session_state["_last_user_msg"] = user_input
    st.session_state["_last_msg_ts"]   = now_ts

    # Afișează și salvează mesajul utilizatorului
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message_with_limits(st.session_state.session_id, "user", user_input)

    # ── Routing materie ──
    _materie_manuala = st.session_state.get("materie_selectata")
    _mod_automat     = (_materie_manuala is None)

    if not _mod_automat:
        if st.session_state.get("_detected_subject") != _materie_manuala:
            update_system_prompt_for_subject(_materie_manuala)
        # Avertizare mismatch (non-blocantă)
        _det_in_msg = detect_subject_from_text(user_input)
        if (
            _det_in_msg and _det_in_msg != _materie_manuala
            and _det_in_msg != "pedagogie"
            and not st.session_state.get(f"_mismatch_warned_{st.session_state.session_id}")
        ):
            _sel_label = MATERII_LABEL.get(_materie_manuala, _materie_manuala or "materia selectată")
            _det_label = MATERII_LABEL.get(_det_in_msg, _det_in_msg.capitalize())
            st.toast(
                f"💡 Mesajul pare să fie despre {_det_label}, dar ești pe {_sel_label}. "
                f"Schimbă materia din sidebar dacă vrei răspuns specializat.",
                icon="⚠️"
            )
            st.session_state[f"_mismatch_warned_{st.session_state.session_id}"] = True
    else:
        _prev_detected = st.session_state.get("_detected_subject")
        _conv_started  = bool(_prev_detected)

        if _conv_started:
            if st.session_state.get("system_prompt") is None:
                update_system_prompt_for_subject(_prev_detected)
        else:
            _detected = detect_subject_from_text(user_input)
            if _detected == "_fizica_ambigua":
                st.session_state["_pending_user_msg"]      = user_input
                st.session_state["_pending_fizica_ambigua"] = True
                st.rerun()
            elif _detected:
                update_system_prompt_for_subject(_detected)
                _det_label = MATERII_LABEL.get(_detected, _detected.capitalize())
                st.toast(f"📚 {_det_label}", icon="🎯")
                for _k in [k for k in st.session_state.keys() if k.startswith("_mismatch_warned_")]:
                    del st.session_state[_k]
            else:
                st.session_state["_pending_user_msg"] = user_input
                st.rerun()

    # ── Construiește contextul pentru AI ──
    context_messages = get_context_for_ai(st.session_state.messages)
    history_obj = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
        for m in context_messages
    ]

    final_payload = []
    if media_content:
        _uf   = st.session_state.get("_current_uploaded_file_meta", {})
        fname = _uf.get("name", "")
        ftype = _uf.get("type", "") or ""
        if ftype.startswith("image/"):
            final_payload.append(
                "Elevul ți-a trimis o imagine. Analizează-o vizual complet: "
                "descrie ce vezi (obiecte, persoane, text, culori, forme, diagrame, exerciții) "
                "și răspunde la întrebarea elevului ținând cont de tot conținutul vizual."
            )
        else:
            final_payload.append(
                f"Elevul ți-a trimis documentul '{fname}'. "
                "Citește și analizează tot conținutul înainte de a răspunde."
            )
        final_payload.append(media_content)
    final_payload.append(user_input)

    # Salvăm pentru retry
    st.session_state["_retry_history"] = history_obj
    st.session_state["_retry_payload"] = final_payload

    # ── Streaming răspuns AI ──
    with st.chat_message("assistant"):
        placeholder   = st.empty()
        full_response = ""
        placeholder.markdown(TYPING_HTML, unsafe_allow_html=True)

        try:
            stream = run_chat_with_rotation(history_obj, final_payload)
            first_chunk = True
            for chunk in stream:
                full_response += chunk
                if first_chunk:
                    first_chunk = False
                if "<svg" in full_response or ("<path" in full_response and "stroke=" in full_response):
                    placeholder.markdown(
                        full_response.split("<path")[0] + "\n\n*🎨 Domnul Profesor desenează...*\n\n▌"
                    )
                else:
                    placeholder.markdown(full_response + "▌")

            placeholder.empty()
            render_message_with_svg(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message_with_limits(st.session_state.session_id, "assistant", full_response)
            st.session_state.pop("_retry_history", None)
            st.session_state.pop("_retry_payload", None)

        except Exception as e:
            placeholder.empty()
            _handle_stream_error(e)


# ──────────────────────────────────────────────────────────────────
# Error handler streaming
# ──────────────────────────────────────────────────────────────────

def _handle_stream_error(e: Exception):
    err_str   = str(e)
    is_key_err = any(x in err_str for x in ["epuizat", "invalide", "quota", "429", "API key"])
    if is_key_err:
        st.warning(
            "⚠️ Cheia API s-a epuizat în timpul răspunsului. "
            "Cheia a fost schimbată automat — apasă **Reîncercați** pentru a primi răspunsul.",
            icon="🔑"
        )
        if st.button("🔄 Reîncercați răspunsul", key="_retry_after_key_error", type="primary"):
            st.session_state["_pending_retry"] = True
            st.rerun()
    else:
        st.error(f"❌ Eroare: {e}")
