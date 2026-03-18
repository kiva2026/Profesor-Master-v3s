"""
modules/materii/detect.py — Detectarea automată a materiei din textul elevului.

Funcții mutate din app.py:
  - detect_subject_from_text()
  - _MATERII_KEYWORDS (dicționar de cuvinte cheie per materie)

Logica de detecție:
  1. Scor pe baza cuvintelor cheie (număr de apariții ponderat)
  2. Fizică: detectare ambiguă dacă nu se poate distinge real vs tehnologic
  3. Returnează codul materiei câștigătoare sau None
"""
import re


# ──────────────────────────────────────────────────────────────────
# Dicționar cuvinte cheie per materie
# ──────────────────────────────────────────────────────────────────

_MATERII_KEYWORDS: dict[str, list[str]] = {
    "matematică": [
        # Algebră
        "ecuație", "inecuație", "sistem", "matrice", "determinant", "polinom",
        "radical", "logaritm", "logaritmi", "ln", "lg", "exponențial",
        "progresie", "aritmetică", "geometrică", "combinări", "permutări",
        "probabilitate", "binomial", "newton",
        # Analiză
        "derivată", "derivate", "integrală", "integrale", "limită", "limite",
        "continuitate", "monotonie", "extreme", "tabel de variație", "asimptotă",
        "funcție", "grafic", "parabola", "dreapta",
        # Geometrie
        "triunghi", "cerc", "unghi", "perpendicular", "paralelogram", "trapez",
        "vector", "coordonate", "distanță", "arie", "volum", "sferă", "cilindru",
        # Notații specifice
        "tg(", "ctg(", "sin(", "cos(", "f(x)", "f'(x)", "∫", "√", "∑",
    ],

    "fizică_real": [
        # Mărimi specifice profilului real
        "relativitate", "cuantă", "foton", "efect fotoelectric", "bohr",
        "dezintegrare", "radioactivitate", "nucleu", "fisiune", "fuziune",
        "polarizare", "interferență", "difracție", "young", "rețea de difracție",
        "circuit oscilant", "LC", "undă electromagnetică",
        # Cuvinte comune fizică (ambigue)
        "accelerație", "viteză", "forță", "energie", "putere", "impuls",
        "moment", "gravitație", "frecare", "tensiune", "curent", "rezistență",
        "condensator", "bobină", "transformator",
    ],

    "fizică_tehnolog": [
        # Specific tehnologic
        "plan înclinat", "scripete", "randament mașini", "motoare termice",
        "circuit dc", "curent continuu", "rezistoare", "kirchhoff",
        "optică geometrică", "lentile", "oglinzi", "refracție",
        # Cuvinte comune fizică (ambigue — aceleași ca real)
        "accelerație", "viteză", "forță", "energie", "putere", "impuls",
        "curent", "rezistență", "tensiune",
    ],

    # Cuvinte cheie EXCLUSIV fizică (ambiguu profil)
    "_fizica_comun": [
        "fizic", "mecanică", "cinematică", "dinamică", "termodinamică",
        "electromagnetism", "optică", "undă", "oscilație", "rezonanță",
        "legea lui", "newton", "ohm", "kirchhoff", "bernoulli", "arhimede",
        "mru", "mrua", "mișcare", "traiectorie", "inerție",
        "câmp electric", "câmp magnetic", "inducție", "flux",
        "joule", "watt", "pascal", "hertz",
        "m/s", "m/s²", "n/m", "kg/m", "j/mol",
    ],

    "chimie": [
        "atom", "moleculă", "element chimic", "tabelul periodic", "legătură chimică",
        "ionică", "covalentă", "metalică", "electroni", "protoni", "neutroni",
        "reacție chimică", "ecuație chimică", "stoechiometrie", "mol", "moli",
        "concentrație molară", "soluție", "dizolvare", "precipitat",
        "acid", "bază", "ph", "neutralizare", "oxidare", "reducere", "redox",
        "alcan", "alchen", "alchin", "benzen", "aromatici",
        "alcool", "ester", "aldehidă", "cetonă", "acid carboxilic",
        "polimer", "plastic", "nailon", "pvc", "aminoacid", "glucoză",
        "coroziune", "electroliză", "galvanic",
    ],

    "limba și literatura română": [
        "eseu", "roman", "nuvela", "poezie", "proza", "lirică", "epică",
        "personaj", "narator", "autor", "opera literară", "curent literar",
        "romantism", "realism", "modernism", "simbolism", "expresionism",
        "eminescu", "creangă", "rebreanu", "sadoveanu", "blaga", "călinescu",
        "bacovia", "arghezi", "preda", "eliade",
        "figuri de stil", "metaforă", "comparație", "personificare", "hiperbola",
        "prozodie", "rimă", "ritm", "strofă", "vers",
        "morfologie", "sintaxă", "substantiv", "verb", "adjectiv", "pronume",
        "propoziție", "frază", "subiect", "predicat", "complement",
        "text argumentativ", "comentariu literar", "caracterizare personaj",
    ],

    "informatică": [
        "algoritm", "pseudocod", "program", "cod", "python", "c++", "java",
        "variabilă", "funcție", "clasă", "obiect", "metodă", "moștenire",
        "vector", "array", "listă", "stivă", "coadă", "dicționar",
        "for", "while", "if", "else", "return", "def", "import",
        "sortare", "căutare", "recursivitate", "backtracking",
        "graf", "arbore", "bfs", "dfs", "dijkstra", "prim", "kruskal",
        "programare dinamică", "complexitate", "O(n)",
        "baze de date", "sql", "html", "css", "javascript",
        "compilator", "interpretor", "debug", "eroare de compilare",
    ],

    "biologie": [
        "celulă", "membrană celulară", "nucleu celular", "mitocondrie",
        "adn", "arn", "proteină", "enzimă", "hormon", "receptor",
        "mitoză", "meioză", "cromozom", "genă", "allele", "mendel",
        "fotosinteza", "respirație celulară", "glucoză", "atp",
        "sistem nervos", "neuron", "sinapsa", "reflex",
        "sistem circulator", "inimă", "sânge", "eritrocit", "leucocit",
        "sistem digestiv", "ficat", "pancreas", "enzime digestive",
        "ecosistem", "lanț trofic", "biodiversitate",
        "evoluție", "darwin", "selecție naturală",
        "anatomie", "histologie", "citologie",
    ],

    "geografie": [
        "relief", "munte", "câmpie", "deal", "podiș", "depresiune",
        "carpați", "dunăre", "deltă", "județul", "regiune",
        "climă", "temperatură", "precipitații", "vânt",
        "hidrografie", "fluviu", "lac", "râu",
        "populație", "densitate", "urban", "rural",
        "agricultura", "industrie", "turism", "transport",
        "uniunea europeană", "ue", "europa",
        "hartă", "coordonate geografice", "latitudine", "longitudine",
        "românia", "bucurești",
    ],

    "istorie": [
        "revoluție", "război", "tratat", "independență", "unire",
        "imperiu", "regat", "domnie", "voievod", "rege",
        "primul război mondial", "al doilea război mondial",
        "comunism", "democrație", "monarhie", "republică",
        "1848", "1859", "1877", "1918", "1989",
        "stefan cel mare", "mircea", "cuza", "carol",
        "roma", "grecia", "egipt", "medieval", "antic",
        "sursa istorică", "document", "cronologie",
        "bac", "eseu istoric",
    ],

    "limba franceză": [
        "en français", "français", "bonjour", "merci",
        "verbe", "conjugaison", "imparfait", "passé composé",
        "subjonctif", "conditionnel", "accord", "féminin", "masculin",
        "article", "pronom", "adjectif",
        "exercice", "traduction",
    ],

    "limba engleză": [
        "in english", "english", "hello", "tense", "present simple",
        "past simple", "present perfect", "conditionals",
        "passive voice", "modal verbs", "vocabulary",
        "grammar", "essay", "writing", "reading",
        "translation", "comprehension",
    ],

    "limba germană": [
        "auf deutsch", "deutsch", "hallo", "artikel", "dativ", "akkusativ",
        "nominativ", "genitiv", "verb", "konjunktiv", "präteritum",
        "perfekt", "futur", "adjektiv", "substantiv",
    ],

    "pedagogie": [
        "cum să învăț", "tehnici de studiu", "memorare", "concentrare",
        "pomodoro", "active recall", "spaced repetition", "feynman",
        "organizare", "planificare", "motivație", "stres", "anxietate",
        "sfat", "sfaturi", "metode de studiu", "program de studiu",
        "bac pregătire", "cum să mă pregătesc",
    ],
}


# ──────────────────────────────────────────────────────────────────
# Detectare materie din text
# ──────────────────────────────────────────────────────────────────

def detect_subject_from_text(text: str) -> str | None:
    """
    Detectează materia din textul elevului.

    Returns:
        Codul materiei (ex: "matematică") sau:
          "_fizica_ambigua" — fizică detectată dar profil necunoscut
          None — nu s-a putut detecta
    """
    if not text:
        return None

    text_lower = text.lower()

    # Calculăm scorul pentru fiecare materie
    scores: dict[str, int] = {}

    for materie, keywords in _MATERII_KEYWORDS.items():
        if materie.startswith("_"):
            continue  # skip cuvinte interne (fizica_comun)
        score = 0
        for kw in keywords:
            if kw in text_lower:
                # Cuvinte mai lungi / specifice = scor mai mare
                weight = 2 if len(kw) > 8 else 1
                score += weight
        if score > 0:
            scores[materie] = score

    # Verifică dacă e fizică (ambiguă sau clară)
    fizica_real_score    = scores.get("fizică_real", 0)
    fizica_tehn_score    = scores.get("fizică_tehnolog", 0)
    fizica_comun_score   = sum(
        1 for kw in _MATERII_KEYWORDS["_fizica_comun"] if kw in text_lower
    )

    # Semnale clare de fizică (cuvinte comune)
    is_fizica = fizica_real_score > 0 or fizica_tehn_score > 0 or fizica_comun_score >= 2

    if is_fizica:
        # Avantaj clar pentru unul din profiluri?
        if fizica_real_score > fizica_tehn_score + 1:
            return "fizică_real"
        elif fizica_tehn_score > fizica_real_score + 1:
            return "fizică_tehnolog"
        else:
            # Ambiguu — întrebăm elevul
            return "_fizica_ambigua"

    # Eliminăm fizică din scor pentru comparare finală
    scores.pop("fizică_real", None)
    scores.pop("fizică_tehnolog", None)

    if not scores:
        return None

    # Câștigătorul e materia cu scorul cel mai mare
    best_materie = max(scores, key=lambda m: scores[m])
    best_score   = scores[best_materie]

    # Prag minim: cel puțin 2 puncte pentru a evita false positives
    if best_score < 2:
        return None

    # Verifică dacă e o victorie clară (nu ambiguitate)
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] < 1:
        # Scor egal între două materii — returnăm None (întrebăm elevul)
        return None

    return best_materie
