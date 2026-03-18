"""
modules/materii/chimie.py — Prompt pentru Chimie (cls IX-XII, România).
"""

PROMPT_TEXT = r"""
    3. CHIMIE — PROGRAMA ROMÂNEASCĂ (Liceu):

       NOTAȚII OBLIGATORII:
       - Formulele chimice cu majuscule: H₂O, NaCl, CO₂, H₂SO₄
       - Ecuații chimice echilibrate cu coeficienți stoechiometrici
       - Concentrația molară: c (mol/L); masă molară: M (g/mol); număr de moli: n (mol)
       - pH = -log[H⁺]; pOH = -log[OH⁻]; pH + pOH = 14

       STRUCTURA OBLIGATORIE pentru calcule stoechiometrice:
       1. Scrie ecuația chimică echilibrată
       2. Identifică raportul molar
       3. Calculează masa/volumul/numărul de moli
       4. Verifică unitatea de măsură

       ══════════════════════════════════════════
       CLASA A IX-A — Chimie anorganică
       ══════════════════════════════════════════

       STRUCTURA ATOMULUI:
       - Proton (+), neutron (0), electron (-); număr atomic Z, masă atomică A
       - Configurație electronică: straturi K(2), L(8), M(18)
       - Tabelul periodic: grupe, perioade, metale/nemetale

       LEGĂTURA CHIMICĂ:
       - Ionică: metal + nemetal → transfer de electroni; NaCl
       - Covalentă: nemetal + nemetal → punere în comun; H₂O, CO₂
       - Metalică: rețea de ioni în mare de electroni

       REACȚII CHIMICE:
       - Tipuri: sinteză, analiză, substituție, schimb
       - Echilibrarea ecuațiilor: metoda bilanțului electronic
       - Viteza de reacție; echilibrul chimic; principiul Le Châtelier

       SOLUȚII:
       - Concentrație masică: c% = m_solvit/m_soluție × 100
       - Concentrație molară: c = n/V; n = m/M
       - Diluție: c₁V₁ = c₂V₂

       ACIZI ȘI BAZE:
       - Teoria Brønsted-Lowry: acid = donor H⁺; bază = acceptor H⁺
       - pH: acid → pH<7; neutru → pH=7; bază → pH>7
       - Titrare acid-bază: n_acid·V_acid = n_bază·V_bază (la echivalență)

       ELECTROCHIMIE:
       - Oxidare = pierdere electroni; Reducere = câștig electroni
       - Pila galvanică: anod (oxidare, -), catod (reducere, +)
       - Electroliza: curentul forțează reacția nespontană

       ══════════════════════════════════════════
       CLASA A X-A — Chimie organică
       ══════════════════════════════════════════

       HIDROCARBURI:
       - Alcani CₙH₂ₙ₊₂: nomenclatură IUPAC, reacție de substituție (cu Cl₂/Br₂, lumină)
       - Alchene CₙH₂ₙ: dubla legătură, adiție electrolfilă, regula lui Markovnikov
       - Alchine CₙH₂ₙ₋₂: tripla legătură, adiție în doi pași
       - Benzen C₆H₆: substituție electrofrilă aromatică, stabilitate aromatică

       COMPUȘI ORGANICI CU FUNCȚIUNI:
       - Alcooli R-OH: reacții de oxidare, esterificare, deshidratare
       - Aldehide R-CHO: oxidare (cu Tollens, Fehling), reducere
       - Cetone R-CO-R': nu se oxidează cu Tollens/Fehling
       - Acizi carboxilici R-COOH: esterificare cu alcooli (catalizator H₂SO₄)
       - Amine R-NH₂: proprietăți bazice

       CALCULE ORGANICĂ:
       - Grad de nesaturare: Ω = (2C + 2 + N - H - X) / 2
       - Formulă moleculară din compoziție procentuală: raport molar → simplificat

       ══════════════════════════════════════════
       CLASA A XI-XII — Biochimie + Chimie aplicată
       ══════════════════════════════════════════

       BIOMOLECULE:
       - Glucoza C₆H₁₂O₆: forma deschisă (aldoză), forma ciclică; test Fehling
       - Zaharoza, amidon, celuloză — diferențe structurale și funcționale
       - Aminoacizi: grup amino (-NH₂) + carboxil (-COOH); amfoterism
       - Proteine: legătură peptidică; structuri primar/secundar/terțiar
       - Grăsimi: trigliceride; saponificare (NaOH → săpun + glicerină)

       CHIMIE APLICATĂ:
       - Polimeri: polimerizare (PE, PP, PVC), policondensare (nailon, poliester)
       - Impactul ecologic: freonii (CFC) și stratul de ozon, efectul de seră
"""
