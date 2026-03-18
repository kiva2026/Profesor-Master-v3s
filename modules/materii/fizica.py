"""
modules/materii/fizica.py — Prompturi pentru Fizică Real și Fizică Tehnologic.

Exportă:
  PROMPT_TEXT_REAL:       str — fizică profil real (M-I, Științe ale naturii)
  PROMPT_TEXT_TEHNOLOGIC: str — fizică profil tehnologic
"""

# ──────────────────────────────────────────────────────────────────
# Bloc comun — notații și structura obligatorie a problemelor
# ──────────────────────────────────────────────────────────────────
_FIZICA_NOTATIONS = r"""
       NOTAȚII OBLIGATORII (toate clasele):
       - Viteză: v; Accelerație: a; Masă: m; Forță: F; Timp: t
       - Distanță/deplasare: d sau s sau x (conform problemei)
       - Energie cinetică: Ec = mv²/2 (NU ½mv²)
       - Energie potențială gravitațională: Ep = mgh
       - Lucru mecanic: L = F·d·cosα; Impuls: p = mv
       - Moment forță: M = F·d (brațul forței)

       STRUCTURA OBLIGATORIE pentru orice problemă de fizică:
       **Date:**        — listează toate mărimile cunoscute cu unități SI
       **Necunoscute:** — ce trebuie aflat
       **Formule:**     — scrie formula generală ÎNAINTE de a substitui valori
       **Calcul:**      — substituie și calculează cu unități la fiecare pas
       **Răspuns:**     — valoarea numerică + unitatea de măsură
"""

# ──────────────────────────────────────────────────────────────────
# Fizică Real
# ──────────────────────────────────────────────────────────────────

PROMPT_TEXT_REAL = r"""
    2. FIZICĂ — PROFIL REAL (Matematică-Fizică, Științe ale Naturii, Vocațional):

       PROFIL: Curriculum extins — mecanică avansată, termodinamică, electromagnetism complet,
       optică ondulatorie, fizică modernă (relativitate, cuantică, nucleară).
       Nivel ridicat de abstractizare, demonstrații matematice, probleme cu mai mulți pași.
""" + _FIZICA_NOTATIONS + r"""
       ══════════════════════════════════════════
       CLASA A IX-A — Mecanică + Mecanica fluidelor
       ══════════════════════════════════════════

       CINEMATICĂ:
       - MRU: x = x₀ + v·t; MRUV: v = v₀ + a·t; x = x₀ + v₀t + at²/2; v² = v₀² + 2aΔx
       - Mișcare circulară uniformă: T, f, ω = 2π/T, v = ω·r, aₙ = v²/r

       DINAMICĂ NEWTONIANĂ:
       - Principiul II: ΣF⃗ = m·a⃗; Principiul III: F₁₂ = −F₂₁
       - Forța gravitațională: G = m·g (g = 10 m/s²)
       - Forța elastică (Hooke): F_e = k·|Δx|
       - Forța de frecare: F_f = μ·N

       LUCRU MECANIC, ENERGIE, IMPULS:
       - L = F·d·cosα; P = L/t = F·v; η = P_util/P_consumată
       - Ec = mv²/2; Ep = mgh; Ee = kx²/2
       - Conservarea energiei mecanice: Ec₁ + Ep₁ = Ec₂ + Ep₂ (fără frecare)
       - Teorema impulsului: ΣF⃗·Δt = Δp⃗

       ECHILIBRU ȘI MECANICA FLUIDELOR:
       - Echilibru translație: ΣF⃗ = 0⃗; rotație: ΣM = 0
       - Legea lui Arhimede: F_A = ρ_fluid·V_scufundat·g
       - Teorema Bernoulli: p + ρv²/2 + ρgh = const

       ══════════════════════════════════════════
       CLASA A X-A — Termodinamică + Electricitate
       ══════════════════════════════════════════

       TERMODINAMICĂ:
       - T(K) = t(°C) + 273; pV/T = const (gaz ideal)
       - Transformări: izoterm p₁V₁ = p₂V₂; izobar V₁/T₁ = V₂/T₂; izocor p₁/T₁ = p₂/T₂
       - Principiul I: ΔU = Q + L; Motoare termice: η = 1 − Q_cedat/Q_absorbit

       CURENT CONTINUU (DC):
       - U = R·I; R = ρ·l/A; W = U·I·t; P = U·I = R·I²
       - Serie: R_total = ΣRᵢ; Paralel: 1/R_total = Σ(1/Rᵢ)
       - Generator real: U = ε − r·I; Kirchhoff I: ΣI_nod = 0; II: ΣU_ochi = 0

       CURENT ALTERNATIV (AC):
       - U_ef = U_max/√2; X_L = ω·L; X_C = 1/(ω·C)
       - Z = √(R² + (X_L−X_C)²); P = U_ef·I_ef·cosφ

       ══════════════════════════════════════════
       CLASA A XI-A — Oscilații, unde, optică ondulatorie
       ══════════════════════════════════════════

       OSCILAȚII MECANICE:
       - Oscilator armonic: x(t) = A·cos(ωt + φ₀)
       - Pendul simplu: T = 2π√(l/g); Resort-masă: T = 2π√(m/k)

       UNDE ȘI OPTICĂ ONDULATORIE:
       - λ = v·T = v/f
       - Interferența Young: Δy = λ·D/d; Difracție: d·sinθ = k·λ
       - Polarizare — legea Malus: I = I₀·cos²θ

       ══════════════════════════════════════════
       CLASA A XII-A — Fizică modernă
       ══════════════════════════════════════════

       RELATIVITATE:
       - Dilatarea timpului: Δt' = Δt/√(1-v²/c²)
       - Echivalența masă-energie: E = mc²

       FIZICĂ CUANTICĂ:
       - Efectul fotoelectric: E_f = hf; E_c = hf − L
       - Modelul Bohr: E_n = -13,6/n² eV; condiție cuantificare: mvr = nℏ
       - Dezintegrarea nucleară: α, β, γ; legi de conservare masă-număr atomic

       SEMICONDUCTORI:
       - Joncțiunea PN, diodă, tranzistor — principiu de funcționare
"""

# ──────────────────────────────────────────────────────────────────
# Fizică Tehnologic
# ──────────────────────────────────────────────────────────────────

PROMPT_TEXT_TEHNOLOGIC = r"""
    2. FIZICĂ — PROFIL TEHNOLOGIC (Filiera tehnologică):

       PROFIL: Curriculum adaptat aplicațiilor practice și tehnice.
       Accent pe: mecanică aplicată, termodinamică, curent continuu, optică geometrică.
       Nivel mai redus de abstractizare față de profilul real; probleme cu 2-3 pași.
""" + _FIZICA_NOTATIONS + r"""
       ══════════════════════════════════════════
       CLASA A IX-A — Mecanică aplicată
       ══════════════════════════════════════════

       CINEMATICĂ:
       - MRU: x = x₀ + v·t; MRUV: v = v₀ + a·t; x = x₀ + v₀t + at²/2
       - Cădere liberă: v = g·t; h = g·t²/2 (g = 10 m/s²)

       DINAMICĂ:
       - Legile lui Newton; plan înclinat; frecare
       - Energie cinetică: Ec = mv²/2; potențială: Ep = mgh
       - Lucru mecanic: L = F·d·cosα; Putere: P = L/t; Randament: η = P_util/P_total
       - Legea lui Arhimede: condiție de plutire

       ══════════════════════════════════════════
       CLASA A X-A — Termodinamică + Curent continuu
       ══════════════════════════════════════════

       TERMODINAMICĂ:
       - T(K) = t(°C) + 273
       - Transformările gazelor (izoterm, izobar, izocor) — grafice p-V, V-T, p-T
       - Randament motor termic: η = L_util/Q_absorbit

       CURENT CONTINUU (DC):
       - Legea lui Ohm: U = R·I
       - Circuite serie și paralel — calcul R_total, U, I
       - Putere electrică: P = U·I; Energie: W = P·t = U·I·t
       - Efectul Joule: Q = R·I²·t
       - Kirchhoff pentru circuite cu 2-3 ramuri

       ══════════════════════════════════════════
       CLASA A XI-A — Optică + Curent alternativ
       ══════════════════════════════════════════

       OPTICĂ GEOMETRICĂ:
       - Reflexia: θ_i = θ_r; oglinzi plane și sferice
       - Refracția: n₁·sin θ₁ = n₂·sin θ₂; unghiul limită
       - Lentile: formula lentilei: 1/f = 1/d_o + 1/d_i; mărire: M = d_i/d_o

       CURENT ALTERNATIV (AC):
       - Valori eficace: U_ef = U_max/√2; I_ef = I_max/√2
       - Transformator: U₁/U₂ = N₁/N₂; putere: P = U_ef·I_ef·cosφ
"""
