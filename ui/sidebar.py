"""
modules/ui/sidebar.py — Sidebar-ul complet al aplicației.

Funcții:
  - render_api_key_section()   — secțiunea cu cheia API Google AI
  - render_sidebar()           — sidebar complet (materie, toggleuri, fișier, moduri, istoric)

Returnează: (keys, media_content) — lista de chei API și fișierul Google upload (dacă există)
"""
import json
import os
import random
import tempfile
import time
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types as genai_types

from config import MATERII, MATERII_LABEL, AUTOMAT_LABEL
from modules.auth.supabase_auth import (
    clear_history_db, get_session_list,
    register_session, is_supabase_available,
)
from modules.ai.gemini_client import _cleanup_gfiles, _is_gfile_active
from modules.materii import get_system_prompt, update_system_prompt_for_subject
from modules.utils.session import (
    generate_unique_session_id, switch_session, format_time_ago, invalidate_session_cache,
)
from modules.utils.validators import is_valid_google_api_key, clean_api_key


# ──────────────────────────────────────────────────────────────────
# API Keys
# ──────────────────────────────────────────────────────────────────

def build_api_keys() -> list[str]:
    """Construiește lista de chei API din secrets + cheia manuală a elevului."""
    saved_manual_key = st.session_state.get("_manual_api_key", "")

    raw_keys = None
    if "GOOGLE_API_KEYS" in st.secrets:
        raw_keys = st.secrets["GOOGLE_API_KEYS"]
    elif "GOOGLE_API_KEY" in st.secrets:
        raw_keys = [st.secrets["GOOGLE_API_KEY"]]

    keys = []
    if raw_keys:
        import json as _json
        if isinstance(raw_keys, str):
            try:
                parsed = _json.loads(raw_keys)
                raw_keys = parsed if isinstance(parsed, list) else [raw_keys]
            except (_json.JSONDecodeError, ValueError):
                raw_keys = [k.strip().strip('"').strip("'") for k in raw_keys.split(",") if k.strip()]
        for k in (raw_keys if isinstance(raw_keys, list) else []):
            if k and isinstance(k, str):
                ck = clean_api_key(k)
                if ck:
                    keys.append(ck)

    if saved_manual_key and saved_manual_key not in keys:
        keys.append(saved_manual_key)

    return keys


def render_api_key_section(keys: list[str]):
    """Afișează secțiunea cheie API — doar dacă nu există chei în secrets."""
    saved_manual_key = st.session_state.get("_manual_api_key", "")
    has_secret_keys  = len([k for k in keys if k != saved_manual_key]) > 0

    if has_secret_keys:
        return  # Cheile sunt configurate în secrets — nu afișăm secțiunea

    st.divider()
    st.subheader("🔑 Cheie API Google AI")

    if not saved_manual_key:
        with st.expander("❓ Cum obțin o cheie? (gratuit)", expanded=False):
            st.markdown("**Ai nevoie de un cont Google** (Gmail). Este complet gratuit.")
            st.link_button("🌐 Mergi la aistudio.google.com", "https://aistudio.google.com/apikey", use_container_width=True)
            st.markdown("""
**Pasul 1** — Autentifică-te cu contul Google.

**Pasul 2** — Apasă **"Create API key"** (buton albastru).

**Pasul 3** — Copiază cheia afișată (`AIzaSy...` — 39 caractere).

**Pasul 4** — Lipește cheia mai jos și apasă **Salvează**.

---
💡 **Limită gratuită:** 15 cereri/minut, 1 milion tokeni/zi.
            """)

        st.caption("Cheia se salvează în browserul tău și rămâne activă după refresh.")
        new_key = st.text_input(
            "Cheie API Google AI:",
            type="password",
            placeholder="AIzaSy...",
            label_visibility="collapsed",
        )
        if st.button("✅ Salvează cheia", use_container_width=True, type="primary", key="save_api_key"):
            ck = clean_api_key(new_key)
            if is_valid_google_api_key(ck):
                st.session_state["_manual_api_key"] = ck
                components.html(
                    f"<script>window.parent._saveApiKeyToStorage && "
                    f"window.parent._saveApiKeyToStorage({json.dumps(ck)});</script>",
                    height=0
                )
                st.toast("✅ Cheie salvată în browser!", icon="🔑")
                st.rerun()
            else:
                st.error("❌ Cheie invalidă. Trebuie să înceapă cu 'AIza' și să aibă minim 20 caractere.")
    else:
        st.success("🔑 Cheie personală activă.")
        st.caption("Salvată în browserul tău — rămâne după refresh.")
        if st.button("🗑️ Șterge cheia", use_container_width=True, key="del_api_key"):
            st.session_state.pop("_manual_api_key", None)
            st.query_params.pop("apikey", None)
            components.html("<script>localStorage.removeItem('profesor_api_key');</script>", height=0)
            st.rerun()


# ──────────────────────────────────────────────────────────────────
# Sidebar principal
# ──────────────────────────────────────────────────────────────────

def render_sidebar(keys: list[str]) -> "tuple[list[str], object|None]":
    """
    Randează sidebar-ul complet.

    Returns:
        (keys, media_content) — keys poate fi modificat (cheie nouă adăugată),
        media_content = obiect Google File sau None
    """
    media_content = None

    with st.sidebar:
        st.header("⚙️ Opțiuni")

        # ── Selector materie ──
        st.subheader("📚 Materie")
        _materii_keys = list(MATERII.keys())
        _mat_saved    = st.session_state.get("materie_selectata")
        _mat_default  = next((i for i, k in enumerate(_materii_keys) if MATERII[k] == _mat_saved), 0)

        materie_label = st.selectbox(
            "Alege materia:",
            options=_materii_keys,
            index=_mat_default,
            label_visibility="collapsed"
        )
        materie_selectata = MATERII[materie_label]
        _mod_automat = (materie_selectata is None)

        if st.session_state.get("materie_selectata") != materie_selectata:
            st.session_state.materie_selectata = materie_selectata
            if _mod_automat:
                st.session_state.pop("_detected_subject", None)
                st.session_state.pop("_pending_user_msg", None)
                st.session_state.system_prompt = get_system_prompt(
                    materie=None,
                    pas_cu_pas=st.session_state.get("pas_cu_pas", False),
                    mod_avansat=st.session_state.get("mod_avansat", False),
                    mod_strategie=st.session_state.get("mod_strategie", False),
                    mod_bac_intensiv=st.session_state.get("mod_bac_intensiv", False),
                )
            else:
                st.session_state["_detected_subject"] = materie_selectata
                st.session_state.pop("_pending_user_msg", None)
                st.session_state.system_prompt = get_system_prompt(
                    materie_selectata,
                    pas_cu_pas=st.session_state.get("pas_cu_pas", False),
                    mod_avansat=st.session_state.get("mod_avansat", False),
                    mod_strategie=st.session_state.get("mod_strategie", False),
                    mod_bac_intensiv=st.session_state.get("mod_bac_intensiv", False),
                )
            st.rerun()

        # Info materie curentă
        if _mod_automat:
            _det = st.session_state.get("_detected_subject")
            if _det and _det != "pedagogie":
                st.caption(f"🔍 Detectat: **{MATERII_LABEL.get(_det, _det.capitalize())}**")
            elif not _det:
                st.caption("🔍 Materia se detectează automat din mesaj")
        else:
            st.info(f"Focusat pe: **{materie_label}**")

        # ── Toggle Sfaturi de studiu ──
        _ped_active = st.session_state.get("pedagogie_mode", False)
        _ped_toggle = st.toggle(
            "🧠 Sfaturi de studiu",
            value=_ped_active,
            help="Activează pentru sfaturi de studiu. Dezactivează pentru a reveni la profesor."
        )
        if _ped_toggle != _ped_active:
            _handle_pedagogie_toggle(_ped_toggle, keys)
            st.rerun()

        st.divider()

        # ── Status Supabase ──
        if not st.session_state.get("_sb_online", True):
            st.markdown(
                '<div style="background:#e67e22;color:white;padding:8px 12px;'
                'border-radius:8px;font-size:13px;text-align:center;margin-bottom:8px">'
                '📴 Mod offline — datele sunt salvate local</div>',
                unsafe_allow_html=True
            )
        else:
            pending = len(st.session_state.get("_offline_queue", []))
            if pending:
                st.caption(f"☁️ {pending} mesaje în așteptare pentru sincronizare")

        st.divider()

        # ── Mod Dark ──
        dark_mode = st.toggle("🌙 Mod Întunecat", value=st.session_state.get("dark_mode", False))
        if dark_mode != st.session_state.get("dark_mode", False):
            st.session_state.dark_mode = dark_mode
            st.rerun()

        # ── Mod Pas cu Pas ──
        _render_toggle("🔢 Explicație Pas cu Pas", "pas_cu_pas",
                       "Profesorul explică fiecare pas în detaliu.")

        # ── Mod Strategie ──
        _render_toggle("🧠 Explică-mi Strategia", "mod_strategie",
                       "Profesorul explică CUM să gândești, nu calculele.")

        # ── Mod Avansat ──
        _render_toggle("⚡ Mod Avansat", "mod_avansat",
                       "Răspunsuri scurte, doar esențialul.")

        # ── Mod BAC Intensiv ──
        _render_toggle("🎓 Pregătire BAC Intensivă", "mod_bac_intensiv",
                       "Focusat pe ce pică la BAC.")

        st.divider()

        # ── Șterge istoricul ──
        if st.button("🗑️ Șterge Istoricul", type="primary"):
            clear_history_db(st.session_state.session_id)
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # ── Upload fișier ──
        st.header("📁 Materiale")
        media_content = _render_file_upload(keys)

        st.divider()

        # ── Moduri examinare ──
        st.subheader("📝 Examinare & BAC")
        media_content = _render_exam_buttons(media_content)

        st.divider()

        # ── Istoric conversații ──
        st.subheader("🕐 Conversații anterioare")
        _render_history()

        st.divider()

        # ── Cheie API (dacă e nevoie) ──
        render_api_key_section(keys)

        # ── Debug ──
        _render_debug_section(keys)

    return keys, media_content


# ──────────────────────────────────────────────────────────────────
# Helpers interne
# ──────────────────────────────────────────────────────────────────

def _render_toggle(label: str, key: str, help_text: str):
    """Randează un toggle care regenerează system prompt la schimbare."""
    value = st.toggle(label, value=st.session_state.get(key, False), help=help_text)
    if value != st.session_state.get(key, False):
        st.session_state[key] = value
        st.session_state.system_prompt = get_system_prompt(
            materie=st.session_state.get("materie_selectata"),
            pas_cu_pas=st.session_state.get("pas_cu_pas", False),
            mod_avansat=st.session_state.get("mod_avansat", False),
            mod_strategie=st.session_state.get("mod_strategie", False),
            mod_bac_intensiv=st.session_state.get("mod_bac_intensiv", False),
        )
        icon = "✅" if value else "💬"
        st.toast(f"{'Activat' if value else 'Dezactivat'}: {label}", icon=icon)
        st.rerun()

    # Info banners pentru moduri active
    info_map = {
        "pas_cu_pas":      ("🔢 **Pas cu Pas activ** — fiecare problemă explicată detaliat.", "📋"),
        "mod_strategie":   ("🧠 **Strategie activ** — înveți să gândești, nu să copiezi.", "🗺️"),
        "mod_avansat":     ("⚡ **Mod Avansat activ** — răspunsuri scurte, doar esențialul.", "🎯"),
        "mod_bac_intensiv":("🎓 **BAC Intensiv activ** — focusat pe ce pică la examen.", "📝"),
    }
    if st.session_state.get(key) and key in info_map:
        msg, icon = info_map[key]
        st.info(msg, icon=icon)


def _render_file_upload(keys: list[str]) -> object | None:
    """Randează secțiunea de upload fișier și returnează media_content."""
    uploaded_file = st.file_uploader(
        "Încarcă imagine, PDF sau document",
        type=["jpg", "jpeg", "png", "webp", "gif", "pdf"],
        help="Imaginile sunt analizate vizual de AI. PDF-urile sunt citite integral."
    )
    media_content = None

    if uploaded_file and st.session_state.get("_removed_file_key") == f"{uploaded_file.name}_{uploaded_file.size}":
        uploaded_file = None

    if uploaded_file:
        st.session_state.pop("_removed_file_key", None)
        file_key  = f"_gfile_{uploaded_file.name}_{uploaded_file.size}"
        cached_gf = st.session_state.get(file_key)

        if cached_gf:
            try:
                gemini_client = genai.Client(api_key=keys[st.session_state.key_index])
                refreshed = gemini_client.files.get(cached_gf.name)
                state_str = str(refreshed.state)
                if state_str in ("FileState.ACTIVE", "ACTIVE", "FileState.PROCESSING", "PROCESSING") \
                        or getattr(refreshed.state, "name", "") in ("ACTIVE", "PROCESSING"):
                    media_content = refreshed
            except Exception:
                st.session_state.pop(file_key, None)
                cached_gf = None

        if not cached_gf:
            suffix_map = {
                "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png",
                "image/webp": ".webp", "image/gif": ".gif", "application/pdf": ".pdf",
            }
            ftype     = uploaded_file.type
            suffix    = suffix_map.get(ftype, ".bin")
            is_image  = ftype.startswith("image/")
            spinner   = "🖼️ Profesorul analizează imaginea..." if is_image else "📚 Se trimite documentul la AI..."

            try:
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    gemini_client = genai.Client(api_key=keys[st.session_state.key_index])
                    with st.spinner(spinner):
                        gfile = gemini_client.files.upload(
                            file=tmp_path,
                            config=genai_types.UploadFileConfig(mime_type=ftype)
                        )
                        poll = 0
                        while str(gfile.state) in ("FileState.PROCESSING", "PROCESSING") and poll < 60:
                            time.sleep(1)
                            gfile = gemini_client.files.get(gfile.name)
                            poll += 1
                    if _is_gfile_active(gfile):
                        media_content = gfile
                        st.session_state[file_key] = gfile
                    else:
                        st.error(f"❌ Fișierul nu a putut fi procesat.")
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except Exception as e:
                st.error(f"❌ Eroare la încărcarea fișierului: {e}")

        if media_content:
            st.session_state["_current_uploaded_file_meta"] = {
                "name": uploaded_file.name, "type": uploaded_file.type, "size": uploaded_file.size,
            }
            if uploaded_file.type.startswith("image/"):
                st.image(uploaded_file, caption=f"🖼️ {uploaded_file.name}", use_container_width=True)
                st.success("✅ Imaginea e pe serverele Google — AI-ul o vede complet.")
            else:
                st.success(f"✅ **{uploaded_file.name}** încărcat ({uploaded_file.size // 1024} KB)")
                st.caption("📄 AI-ul poate citi și analiza tot conținutul documentului.")

            if st.button("🗑️ Elimină fișierul", use_container_width=True, key="remove_media"):
                fk = f"_gfile_{uploaded_file.name}_{uploaded_file.size}"
                gf = st.session_state.pop(fk, None)
                if gf:
                    try:
                        gc = genai.Client(api_key=keys[st.session_state.key_index])
                        gc.files.delete(gf.name)
                    except Exception:
                        pass
                media_content = None
                st.session_state.pop("_current_uploaded_file_meta", None)
                st.session_state["_removed_file_key"] = f"{uploaded_file.name}_{uploaded_file.size}"
                st.rerun()

    return media_content


def _render_exam_buttons(media_content):
    """Randează butoanele pentru moduri de examinare."""
    _BAC_KEYS = ["bac_mode", "bac_active", "bac_materie", "bac_profil", "bac_subject",
                 "bac_barem", "bac_raspuns", "bac_corectat", "bac_corectare",
                 "bac_start_time", "bac_timp_min", "bac_from_photo", "bac_ocr_done"]
    _HW_KEYS  = ["homework_mode", "hw_materie", "hw_text", "hw_corectare",
                 "hw_done", "hw_from_photo", "hw_ocr_done"]
    _QUIZ_KEYS = ["quiz_mode", "quiz_active", "quiz_questions", "quiz_correct",
                  "quiz_answers", "quiz_submitted", "quiz_materie", "quiz_nivel"]
    _ADMITERE_KEYS = ["admitere_mode", "admitere_univ", "admitere_spec", "admitere_proba",
                      "admitere_active", "admitere_subject", "admitere_barem",
                      "admitere_raspuns", "admitere_corectat", "admitere_corectare",
                      "admitere_start_time", "admitere_grila_answers", "admitere_grila_submitted"]

    def _clear_all():
        for k in _BAC_KEYS + _HW_KEYS + _QUIZ_KEYS + _ADMITERE_KEYS + ["_suggested_question", "_pending_user_msg"]:
            st.session_state.pop(k, None)

    col_q, col_b = st.columns(2)
    with col_q:
        if st.button("🎯 Quiz rapid", use_container_width=True,
                     type="primary" if st.session_state.get("quiz_mode") else "secondary"):
            entering = not st.session_state.get("quiz_mode", False)
            _clear_all()
            st.session_state.quiz_mode = entering
            st.rerun()
    with col_b:
        if st.button("🎓 Simulare BAC", use_container_width=True,
                     type="primary" if st.session_state.get("bac_mode") else "secondary"):
            entering = not st.session_state.get("bac_mode", False)
            _clear_all()
            st.session_state.bac_mode = entering
            st.rerun()

    if st.button("🏛️ Admitere Facultate", use_container_width=True,
                 type="primary" if st.session_state.get("admitere_mode") else "secondary"):
        entering = not st.session_state.get("admitere_mode", False)
        _clear_all()
        st.session_state.admitere_mode = entering
        st.rerun()

    if st.button("📚 Corectează Temă", use_container_width=True,
                 type="primary" if st.session_state.get("homework_mode") else "secondary"):
        entering = not st.session_state.get("homework_mode", False)
        _clear_all()
        st.session_state.homework_mode = entering
        st.rerun()

    return media_content


def _render_history():
    """Randează istoricul conversațiilor din sidebar."""
    if st.button("🔄 Conversație nouă", use_container_width=True):
        _cleanup_gfiles()
        new_sid = generate_unique_session_id()
        register_session(new_sid)
        _my_sids = st.session_state.get("_my_session_ids", [])
        if new_sid not in _my_sids:
            _my_sids.append(new_sid)
        st.session_state["_my_session_ids"] = _my_sids
        switch_session(new_sid)
        st.rerun()

    current_sid = st.session_state.session_id
    _my_sids = st.session_state.get("_my_session_ids", [current_sid])
    if current_sid not in _my_sids:
        _my_sids = [current_sid] + _my_sids
        st.session_state["_my_session_ids"] = _my_sids

    sessions = []
    try:
        from modules.auth.supabase_auth import get_supabase_client
        from config import get_app_id
        _sb = get_supabase_client()
        if _sb:
            resp = (
                _sb.table("session_previews")
                .select("session_id, last_active, msg_count, preview")
                .eq("app_id", get_app_id())
                .in_("session_id", _my_sids)
                .gt("msg_count", 0)
                .order("last_active", desc=True)
                .limit(15)
                .execute()
            )
            sessions = resp.data or []
    except Exception:
        pass

    for s in sessions:
        is_current   = s["session_id"] == current_sid
        preview_text = s['preview'] or "Conversație"
        label        = f"{'▶ ' if is_current else ''}{preview_text}"
        caption      = f"{format_time_ago(s['last_active'])} · {s['msg_count']} mesaje"
        with st.container():
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"sess_{s['session_id']}",
                             use_container_width=True,
                             type="primary" if is_current else "secondary",
                             help=caption):
                    if not is_current:
                        switch_session(s["session_id"])
                        st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{s['session_id']}", help="Șterge"):
                    clear_history_db(s["session_id"])
                    if is_current:
                        st.session_state.messages = []
                    _my_sids2 = st.session_state.get("_my_session_ids", [])
                    if s["session_id"] in _my_sids2:
                        _my_sids2.remove(s["session_id"])
                    st.session_state["_my_session_ids"] = _my_sids2
                    st.rerun()


def _render_debug_section(keys: list[str]):
    """Randează secțiunea de debug (colapsabilă)."""
    _debug_val = st.session_state.get("_debug_info_open", False)
    _debug = st.checkbox("🔧 Debug Info", value=_debug_val, key="chk_debug_info")
    if _debug != _debug_val:
        st.session_state["_debug_info_open"] = _debug

    if _debug:
        msg_count = len(st.session_state.get("messages", []))
        from config import MAX_MESSAGES_IN_MEMORY
        st.caption(f"📊 Mesaje în memorie: {msg_count}/{MAX_MESSAGES_IN_MEMORY}")
        st.caption(f"🔑 Cheie API activă: {st.session_state.key_index + 1}/{len(keys)}")
        st.caption(f"🆔 Sesiune: {st.session_state.session_id[:16]}...")


def _handle_pedagogie_toggle(activate: bool, keys: list[str]):
    """Logica de activare/dezactivare a modului Sfaturi de studiu."""
    if activate:
        st.session_state["_ped_prev_session_id"]    = st.session_state.get("session_id", "")
        st.session_state["_ped_prev_messages"]      = list(st.session_state.get("messages", []))
        st.session_state["_ped_prev_materie"]       = st.session_state.get("materie_selectata")
        st.session_state["_ped_prev_detected"]      = st.session_state.get("_detected_subject")
        st.session_state["_ped_prev_system_prompt"] = st.session_state.get("system_prompt", "")

        _ped_sid = generate_unique_session_id()
        register_session(_ped_sid)
        st.session_state["session_id"]        = _ped_sid
        st.session_state["messages"]          = []
        _my_sids = st.session_state.get("_my_session_ids", [])
        if _ped_sid not in _my_sids:
            _my_sids.append(_ped_sid)
        st.session_state["_my_session_ids"]   = _my_sids
        st.session_state["pedagogie_mode"]    = True
        st.session_state["_detected_subject"] = "pedagogie"
        st.session_state["system_prompt"]     = get_system_prompt(
            materie="pedagogie",
            pas_cu_pas=st.session_state.get("pas_cu_pas", False),
            mod_avansat=st.session_state.get("mod_avansat", False),
            mod_strategie=st.session_state.get("mod_strategie", False),
            mod_bac_intensiv=st.session_state.get("mod_bac_intensiv", False),
        )
        invalidate_session_cache()
        components.html(
            f"<script>localStorage.setItem('profesor_session_id', {json.dumps(_ped_sid)});</script>",
            height=0,
        )
    else:
        # Restaurează sesiunea anterioară
        _prev_sid = st.session_state.get("_ped_prev_session_id", "")
        _prev_msg = st.session_state.get("_ped_prev_messages", [])
        _prev_mat = st.session_state.get("_ped_prev_materie")
        _prev_det = st.session_state.get("_ped_prev_detected")
        _prev_sys = st.session_state.get("_ped_prev_system_prompt", "")

        st.session_state["pedagogie_mode"] = False
        for _k in ["_ped_prev_session_id", "_ped_prev_messages",
                   "_ped_prev_materie", "_ped_prev_detected", "_ped_prev_system_prompt"]:
            st.session_state.pop(_k, None)

        from modules.utils.session import is_valid_session_id
        if _prev_sid and is_valid_session_id(_prev_sid):
            st.session_state["session_id"]        = _prev_sid
            st.session_state["messages"]          = _prev_msg
            st.session_state["materie_selectata"] = _prev_mat
            st.session_state["_detected_subject"] = _prev_det
            st.session_state["system_prompt"]     = _prev_sys or get_system_prompt(materie=_prev_mat)
            try:
                st.query_params["sid"] = _prev_sid
            except Exception:
                pass
            components.html(
                f"<script>localStorage.setItem('profesor_session_id', {json.dumps(_prev_sid)});</script>",
                height=0,
            )
        else:
            _new_sid = generate_unique_session_id()
            register_session(_new_sid)
            st.session_state["session_id"]        = _new_sid
            st.session_state["messages"]          = []
            st.session_state["materie_selectata"] = None
            st.session_state.pop("_detected_subject", None)
            st.session_state["system_prompt"]     = get_system_prompt(materie=None)
            try:
                st.query_params["sid"] = _new_sid
            except Exception:
                pass
            components.html(
                f"<script>localStorage.setItem('profesor_session_id', {json.dumps(_new_sid)});</script>",
                height=0,
            )
        invalidate_session_cache()
