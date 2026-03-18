# Migrarea modulelor BAC / Quiz / Temă / Admitere

Aceste module conțin cod voluminos (prompt-uri de date BAC reale 2021-2025,
configurații de universități, logica UI). Sunt extrase **direct** din
secțiunile corespunzătoare ale `app.py` original, fără modificări logice.

## Pași de migrare pentru fiecare fișier

### `modules/bac/base.py`
Conține din `app.py` original:
- `BAC_DATE_REALE` (dict cu subiecte reale 2021-2025 pentru toate materiile)
- `MATERII_BAC` (configurația materiilor simulabile)
- `MATERII_SIMULARE_DISPONIBILE`
- `PROFILE_BAC` (ierarhia filiere → profil → specializare → materii)
- `get_bac_prompt_ai(bac_materie, info, bac_profil)` → str
- `parse_bac_subject(full_text)` → (subject, barem)
- `format_timer(seconds)` → str

**Acțiune**: Caută în `app.py` original comentariul `# === BAC ===`
și copiază blocul de date + funcțiile de prompt.

---

### `modules/bac/bac_ui.py`
Conține din `app.py` original:
- `run_bac_sim_ui()` — UI complet pentru simularea BAC (selector profil,
  generare subiect, cronometru, corecție AI)

**Acțiune**: Caută în `app.py` original `def run_bac_sim_ui():` și copiază
funcția. Înlocuiește importurile locale cu:
```python
from modules.bac.base import get_bac_prompt_ai, parse_bac_subject, MATERII_BAC, PROFILE_BAC, format_timer
from modules.ai.gemini_client import run_chat_with_rotation
from modules.materii.base import get_system_prompt
from modules.ui.svg_renderer import render_message_with_svg
```

---

### `modules/bac/quiz_ui.py`
Conține din `app.py` original:
- `NIVELE_QUIZ`, `MATERII_QUIZ`
- `get_quiz_prompt(materie_label, nivel, materie_val)` → str
- `parse_quiz_response(response)` → (clean_text, correct_answers_dict)
- `run_quiz_ui()` — UI complet pentru quiz rapid

**Acțiune**: Caută `def run_quiz_ui():` și `def get_quiz_prompt(` în original.

---

### `modules/bac/homework_ui.py`
Conține din `app.py` original:
- `extract_text_from_photo(photo_bytes, materie)` → str
- `get_homework_correction_prompt(materie_label, text, from_photo)` → str
- `run_homework_ui()` — UI complet pentru corectura temei

**Acțiune**: Caută `def run_homework_ui():` și `def get_homework_correction_prompt(`.

---

### `modules/bac/admitere_base.py`
Conține din `app.py` original:
- `ADMITERE_CONFIG` (dict cu universități → specializări → probe)
- `ADMITERE_NIVELE` (niveluri de dificultate cu instrucțiuni)
- `get_admitere_prompt(proba_cod, proba_info, specializare, universitate, nivel)` → str

**Acțiune**: Caută `ADMITERE_CONFIG = {` în original.

---

### `modules/bac/admitere_ui.py`
Conține din `app.py` original:
- `parse_admitere_grila(response)` → list[dict]
- `run_admitere_ui()` — UI complet pentru simularea admiterii la facultate

**Acțiune**: Caută `def run_admitere_ui():` în original.

---

## De ce nu sunt generate automat?

Aceste module conțin în total **~5.000 de linii** de date și logică UI
foarte densă (BAC_DATE_REALE singur are ~800 de linii). Ele nu necesită
modificări structurale față de `app.py` original — sunt **extrageri directe**.

Strategia recomandată:
1. Deschide `app.py` original
2. Caută comentariul sau funcția indicată mai sus
3. Copiază blocul în fișierul destinație
4. Actualizează importurile conform exemplelor de mai sus

Toate dependențele (run_chat_with_rotation, get_system_prompt, render_message_with_svg)
sunt deja exportate corect din modulele create.
