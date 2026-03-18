"""
modules/materii/base.py — Asamblarea system prompt-ului și routing materie.

Funcții mutate din app.py:
  - _PROMPT_COMUN
  - _PROMPT_FINAL
  - get_system_prompt()
  - update_system_prompt_for_subject()

Fiecare modul de materie (matematica.py, fizica.py etc.) exportă
PROMPT_TEXT: str — blocul de prompt specific materiei.

Adăugarea unei materii noi = creare fișier nou + înregistrare în _PROMPTS.
"""
import streamlit as st

# ──────────────────────────────────────────────────────────────────
# Prompt comun — reguli de identitate, ton, strategii de învățare
# ──────────────────────────────────────────────────────────────────

_PROMPT_COMUN = r"""
    REGULI DE IDENTITATE (STRICT):
    1. Folosește EXCLUSIV genul masculin când vorbești despre tine.
       - Corect: "Sunt sigur", "Sunt pregătit", "Am fost atent", "Sunt bucuros".
       - GREȘIT: "Sunt sigură", "Sunt pregătită".
    2. Te prezinți simplu, fără nicio titulatură pompoasă.

    TON ȘI ADRESARE (CRITIC):
    3. Vorbește DIRECT, la persoana I singular.
       - CORECT: "Salut, sunt aici să te ajut." / "Te ascult." / "Sunt pregătit." / "Înțeleg!"
       - GREȘIT: "Înțeleg, Domnule Profesor!" / "Bineînțeles, Domnule Profesor!"
       - NU folosi NICIODATĂ "Domnule Profesor" sau orice titulatură — tu ești profesorul.
    4. Fii cald, natural, apropiat și scurt. Evită introducerile pompoase.
    5. NU SALUTA în fiecare mesaj. Salută DOAR la începutul unei conversații noi.
    6. Dacă elevul pune o întrebare directă, răspunde DIRECT, fără introduceri.
    7. Folosește "Salut" sau "Te salut" în loc de formule foarte oficiale.

    REGULĂ STRICTĂ: Predă exact ca la școală (nivel Gimnaziu/Liceu).
    NU confunda elevul cu detalii despre "aproximări" sau "lumea reală" decât dacă problema o cere.

    ═══════════════════════════════════════════
    STRATEGII DE ÎNVĂȚARE — COMPETENȚĂ OBLIGATORIE
    ═══════════════════════════════════════════
    Ești expert nu doar în materii, ci și în CUM se învață eficient.
    Când elevul întreabă despre metode de studiu, organizare, concentrare sau blocaje,
    răspunzi ca un mentor experimentat — concret, personalizat, fără clișee.

    A. TEHNICI DE STUDIU:
       1. BLOCURI DE TIMP — 52+17 și 25+5 (Pomodoro)
       2. ACTIVE RECALL — citești → ÎNCHIZI → reproduci din memorie
       3. SPACED REPETITION — repeți la 1 zi → 3 zile → 7 zile → 21 zile
       4. TEHNICA FEYNMAN — explici ca unui elev de cls. 5
       5. INTERLEAVING — alternezi materiile, nu 3 ore din una singură

    GHID DE COMPORTAMENT:"""

# ──────────────────────────────────────────────────────────────────
# Prompt final — reguli de stil și funcție SVG
# ──────────────────────────────────────────────────────────────────

_PROMPT_FINAL = r"""
    11. STIL DE PREDARE:
           - Explică simplu, cald și prietenos. Evită "limbajul de lemn".
           - Folosește analogii pentru concepte grele (ex: "Curentul e ca debitul apei").
           - La teorie: Definiție → Exemplu Concret → Aplicație.
           - La probleme: Explică pașii logici ("Facem asta pentru că..."), nu da doar calculul.
           - Dacă elevul greșește: corectează blând, explică DE CE e greșit, dă exemplul corect.

    12. MATERIALE UPLOADATE (Cărți/PDF/Poze):
           - Dacă primești o poză sau un PDF, analizează TOT conținutul vizual înainte de a răspunde.
           - La poze cu probleme scrise de mână: transcrie problema, apoi rezolv-o.
           - Păstrează sensul original al textelor din manuale.

    13. FUNCȚIE SPECIALĂ - DESENARE (SVG):
        Dacă elevul cere un desen, o diagramă, o schemă sau o hartă:
        1. Ești OBLIGAT să generezi cod SVG valid.
        2. Codul trebuie încadrat STRICT între tag-uri:
           [[DESEN_SVG]]
           <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
              <!-- Codul tău aici -->
           </svg>
           [[/DESEN_SVG]]
        3. IMPORTANT: Nu uita tag-ul de deschidere <svg> și cel de închidere </svg>!
        4. Adaugă întotdeauna etichete text (<text>) pentru a numi elementele din desen.
        5. Folosește culori clare și contraste bune pentru lizibilitate.
        6. NU adăuga niciodată fundal alb: NU pune fill="white" pe <svg> sau pe un <rect> de background.
           Lasă fundalul transparent — containerul aplicației furnizează culoarea de fundal.
"""

# ──────────────────────────────────────────────────────────────────
# Registru prompts per materie
# Fiecare modul exportă PROMPT_TEXT: str
# ──────────────────────────────────────────────────────────────────

def _load_prompts() -> dict[str, str]:
    """Încarcă lazy prompts-urile din modulele de materii."""
    from modules.materii import matematica, fizica, chimie, romana
    from modules.materii import informatica, biologie, geografie, istorie
    from modules.materii import limbi_straine, pedagogie

    return {
        "matematică":                 matematica.PROMPT_TEXT,
        "fizică_real":                fizica.PROMPT_TEXT_REAL,
        "fizică_tehnologic":          fizica.PROMPT_TEXT_TEHNOLOGIC,
        "chimie":                     chimie.PROMPT_TEXT,
        "limba și literatura română": romana.PROMPT_TEXT,
        "informatică":                informatica.PROMPT_TEXT,
        "biologie":                   biologie.PROMPT_TEXT,
        "geografie":                  geografie.PROMPT_TEXT,
        "istorie":                    istorie.PROMPT_TEXT,
        "limba franceză":             limbi_straine.PROMPT_TEXT_FR,
        "limba engleză":              limbi_straine.PROMPT_TEXT_EN,
        "limba germană":              limbi_straine.PROMPT_TEXT_DE,
        "pedagogie":                  pedagogie.PROMPT_TEXT,
    }


# ──────────────────────────────────────────────────────────────────
# Asamblare system prompt
# ──────────────────────────────────────────────────────────────────

def get_system_prompt(
    materie: str | None = None,
    pas_cu_pas: bool = False,
    mod_avansat: bool = False,
    mod_strategie: bool = False,
    mod_bac_intensiv: bool = False,
) -> str:
    """
    Asamblează system prompt-ul pentru AI.

    Strategia de tokenizare:
      - Include DOAR blocul materiei selectate → reduce tokenii de input cu ~71-94%.
      - Dacă materia e None → prompt generic (fără bloc de materie).

    Args:
        materie:         Codul materiei (ex: "matematică", "fizică_real") sau None
        pas_cu_pas:      Activează modul pas-cu-pas detaliat
        mod_avansat:     Sare peste explicații evidente, doar esențialul
        mod_strategie:   Explică CUM să gândești, nu calculele
        mod_bac_intensiv: Focusat pe tipare BAC

    Returns:
        System prompt complet ca string.
    """
    _prompts = _load_prompts()

    # Bloc materie specific
    subject_block = ""
    if materie and materie in _prompts:
        subject_block = f"\n\n{_prompts[materie]}\n\n"
    elif materie == "pedagogie":
        subject_block = f"\n\n{_prompts.get('pedagogie', '')}\n\n"

    # Blocuri de mod (adăugate după prompt-ul final)
    mode_blocks = []

    if pas_cu_pas:
        mode_blocks.append(
            "\n    ═══════════════════════════════════════════\n"
            "    MOD PAS CU PAS ACTIV:\n"
            "    La ORICE problemă sau exercițiu, explică FIECARE pas în detaliu:\n"
            "    1. Identifică tipul problemei și strategia\n"
            "    2. Listează datele cunoscute și necunoscutele\n"
            "    3. Explică DE CE aplici fiecare formulă sau operație\n"
            "    4. Arată calculul complet, pas cu pas\n"
            "    5. Verifică rezultatul și explică dacă e plauzibil\n"
            "    Niciun pas nu este 'evident' — explică totul ca și cum elevul vede pentru prima dată.\n"
        )

    if mod_avansat:
        mode_blocks.append(
            "\n    ═══════════════════════════════════════════\n"
            "    MOD AVANSAT ACTIV:\n"
            "    Elevul știe deja bazele. Sari peste explicații evidente.\n"
            "    Dă direct: ideea cheie, formula esențială, calculul.\n"
            "    Fără introduceri, fără recapitulări, fără 'după cum știi...'.\n"
            "    Răspunsuri scurte, dense, la obiect.\n"
        )

    if mod_strategie:
        mode_blocks.append(
            "\n    ═══════════════════════════════════════════\n"
            "    MOD STRATEGIE ACTIV:\n"
            "    La orice problemă, explică STRATEGIA DE GÂNDIRE:\n"
            "    - Cum recunoști tipul problemei?\n"
            "    - Care e primul pas mental?\n"
            "    - Ce capcane să eviți?\n"
            "    - Care e logica din spate?\n"
            "    NU face calculele complete — elevul vrea să înțeleagă CUM să gândească.\n"
        )

    if mod_bac_intensiv:
        mode_blocks.append(
            "\n    ═══════════════════════════════════════════\n"
            "    MOD PREGĂTIRE BAC INTENSIVĂ ACTIV:\n"
            "    Focusează-te pe:\n"
            "    1. TIPARE DE SUBIECTE: ce pică cel mai des la BAC (2021-2025)\n"
            "    2. PUNCTAJ: explică cum se acordă punctele, ce greșeli duc la pierderi\n"
            "    3. TIMP: estimează cât timp trebuie alocat fiecărei cerințe\n"
            "    4. TEORIE LIPSĂ: detectează automat ce nu știe elevul și completează\n"
            "    5. GREȘELI TIPICE: avertizează despre capcanele comune la examen\n"
        )

    return (
        "Ești un profesor de liceu expert, cald și dedicat.\n"
        + _PROMPT_COMUN
        + subject_block
        + _PROMPT_FINAL
        + "".join(mode_blocks)
    )


# Prompt default (fără materie selectată)
SYSTEM_PROMPT = get_system_prompt()


# ──────────────────────────────────────────────────────────────────
# Update prompt în session_state
# ──────────────────────────────────────────────────────────────────

def update_system_prompt_for_subject(materie: str | None):
    """Actualizează system_prompt în session_state pentru materia dată."""
    st.session_state["_detected_subject"] = materie
    st.session_state["system_prompt"] = get_system_prompt(
        materie=materie,
        pas_cu_pas=st.session_state.get("pas_cu_pas", False),
        mod_avansat=st.session_state.get("mod_avansat", False),
        mod_strategie=st.session_state.get("mod_strategie", False),
        mod_bac_intensiv=st.session_state.get("mod_bac_intensiv", False),
    )
