"""
modules/materii/biologie.py — Prompt pentru Biologie (Liceu România).
"""

PROMPT_TEXT = r"""
    6. BIOLOGIE — PROGRAMA ROMÂNEASCĂ (Liceu):

       NOTAȚII: utilizează denumiri științifice (latină) acolo unde e relevant.
       Diagrame: descrie procesele în pași clari; folosește SVG pentru scheme celulare, genetice.

       ══════════════════════════════════════════
       CLASA A IX-A — Celula + Genetică
       ══════════════════════════════════════════

       CELULA:
       - Componentele: membrană (fosfolipide + proteine), citoplasmă, nucleu, organite
       - Organite: mitocondrie (respirație), cloroplast (fotosinteză), ribozom (sinteza proteinelor),
         RE rugos/neted, aparat Golgi, lizozomi, vacuole
       - Celulă procariotă vs eucariotă; celulă animală vs vegetală

       DIVIZIUNEA CELULARĂ:
       - Mitoza: IPMAT (Interfaza, Profaza, Metafaza, Anafaza, Telofaza)
         → Rezultat: 2 celule fiice identice (2n → 2n)
       - Meioza: reducțională (2n → n) + ecvațională → 4 celule haploide
         → Importanță: variabilitate genetică, formarea gameților

       GENETICA MENDELIANĂ:
       - Legea I (uniformității): F1 toți identici
       - Legea II (segregării): F2 = 3:1 (dominant:recesiv) pentru o genă
       - Legea III (asortimentului independent): 9:3:3:1 pentru două gene
       - Pătrat Punnett: metodă vizuală pentru calculul probabilităților
       - Codominanță, dominanță incompletă, gene legate de sex (daltonism, hemofilie)

       BIOCHIMIE:
       - ADN: dublu helix, baze azotate (A-T, G-C); replicarea semiconservativă
       - ARN: mesager (ARNm), ribozomal (ARNr), de transfer (ARNt)
       - Sinteza proteinelor: transcripție (ADN → ARNm) + traducere (ARNm → proteină)
       - Codul genetic: codon = 3 baze = 1 aminoacid; AUG = start; UAA/UAG/UGA = stop

       ══════════════════════════════════════════
       CLASA A X-A — Sisteme și organe
       ══════════════════════════════════════════

       FOTOSINTEZA:
       - Faza luminoasă (tilacoid): H₂O → O₂ + ATP + NADPH
       - Ciclul Calvin (stromă): CO₂ + ATP + NADPH → glucoză

       RESPIRAȚIA CELULARĂ:
       - Glicoliza (citoplasmă): glucoză → 2 piruvat + 2 ATP
       - Ciclul Krebs (mitocondrie): piruvat → CO₂ + NADH
       - Lanțul respirator (membrană internă): NADH → ATP (maxim 36-38 ATP/glucoză)

       SISTEMUL NERVOS:
       - Neuronul: dendrite (receptori), corp celular, axon (efector)
       - Sinaptogeneza: acetilcolina, dopamina, serotonina
       - Arcul reflex: receptor → nerv aferent → centru nervos → nerv eferent → efector
       - SNC (encefal + măduvă) vs SNP (nervii cranieni + spinali)

       SISTEMUL CIRCULATOR:
       - Inima: 4 camere; circulație mică (plămâni) + mare (corp)
       - Sânge: eritrocite (hemoglobina, oxigen), leucocite (imunitate), trombocite (coagulare)
       - Grupe sanguine ABO și Rh

       SISTEMUL ENDOCRIN:
       - Hipofiza: STH (creștere), TSH (tiroidă), FSH/LH (gonade)
       - Tiroidă: tiroxina (metabolism); Suprarenale: adrenalina (stres)
       - Pancreas endocrin: insulina (↓glicemie) vs glucagon (↑glicemie)

       ══════════════════════════════════════════
       ECOLOGIE ȘI EVOLUȚIE
       ══════════════════════════════════════════

       - Ecosistem: biocenoză (vie) + biotop (neviuSUMMARY
       - Lanț trofic: producători → consumatori primari → secundari → tertiari → descompunători
       - Diversitatea biologică: specii, ecosisteme, genetică
       - Evoluția darwinistă: variabilitate + selecție naturală + izolare reproductivă
"""
