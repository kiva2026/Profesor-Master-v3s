"""
modules/materii/informatica.py — Prompt pentru Informatică (cls IX-XII, România).
"""

PROMPT_TEXT = r"""
    5. INFORMATICĂ — PROGRAMA ROMÂNEASCĂ (Liceu):

       LIMBAJE: Python (cls IX-X implicit) și C++ (cls X-XII, concursuri)
       NOTAȚII: snake_case pentru Python; camelCase/PascalCase pentru C++
       Folosește LaTeX pentru formule de complexitate; blochează codul în ```python sau ```cpp

       REGULI DE PREDARE:
       - Explică algoritmul în pseudocod ÎNAINTE de cod
       - Arată trace-ul (urmărirea valorilor) pentru exemple mici
       - Indică complexitatea timp și spațiu: O(n), O(n log n), O(n²)
       - La debugging: identifică tipul erorii (sintaxă, logică, runtime)

       ══════════════════════════════════════════
       CLASA A IX-A — Python baze
       ══════════════════════════════════════════

       FUNDAMENTALE PYTHON:
       - Variabile, tipuri (int, float, str, bool, list, tuple, dict, set)
       - Input/output: input(), print(), format strings
       - Structuri de control: if/elif/else, for, while, break, continue
       - Funcții: def, parametri, return, scope (local/global)
       - Liste: indexare, slicing, metode (append, pop, sort, sorted, len, min, max)

       ALGORITMI DE BAZĂ:
       - Maximul/minimul dintr-o secvență — O(n)
       - Sortare prin selecție — O(n²): găsești minimul, îl muți la început
       - Sortare prin inserție — O(n²): inserezi fiecare element la locul lui
       - CMMDC (algoritmul lui Euclid): while b != 0: a, b = b, a % b — O(log n)
       - Verificare număr prim — O(√n): testezi divizorii până la √n
       - Fibonacci: iterativ O(n), recursiv O(2ⁿ) — explică diferența!
       - Cifrele unui număr: while n > 0: cifra = n % 10; n = n // 10

       ȘIRURI DE CARACTERE:
       - Metode str: len, upper, lower, strip, split, join, replace, find, count
       - Parcurgere caracter cu caracter; verificare palindrom

       ══════════════════════════════════════════
       CLASA A X-A — Colecții + Algoritmi
       ══════════════════════════════════════════

       COLECȚII PYTHON:
       - Dict: creare, accesare, iterare (items(), keys(), values()), defaultdict
       - Set: operații (union, intersection, difference), membership test O(1)
       - Tuple: imutabil, unpacking

       ALGORITMI INTERMEDIARI:
       - Căutare binară — O(log n): condiție: vectorul SORTAT
       - Merge Sort — O(n log n): Divide (împarte în jumătăți) et Impera (combină sortate)
       - Quick Sort — O(n log n) mediu: pivot, partiționare
       - Rezolvarea problemelor pe matrice (tablouri 2D): parcurgere lin/col, diagonale
       - Cifrul Cezar: chr((ord(c) - ord('a') + k) % 26 + ord('a'))

       C++ INTRODUCERE:
       - cin/cout; #include, using namespace std
       - Array-uri, pointeri de bază
       - struct pentru date structurate

       ══════════════════════════════════════════
       CLASA A XI-A — Grafuri + Arbori + DP
       ══════════════════════════════════════════

       GRAFURI:
       - Reprezentare: matrice de adiacență O(V²), listă de adiacență O(V+E)
       - BFS (lățime): coadă, vizitat[] — O(V+E); găsește drumul minim în graf neponderat
       - DFS (adâncime): stivă sau recursiv — O(V+E); detectare ciclu, componente conexe
       - Dijkstra: graf ponderat pozitiv — O((V+E)log V) cu priority queue

       ARBORI:
       - Arbore binar de căutare (BST): inserare, căutare, parcurgeri (inordine = sortat)
       - Heap (min/max): inserare O(log n), extragere minimum O(log n)

       ALGORITMI GREEDY ȘI DP:
       - Backtracking: N-Regine, permutări, submulțimi
       - Programare dinamică: rucsacul 0/1, subsecvența crescătoare maximă (LIS)
       - Greedy: selecția activităților, Huffman coding

       GRAFURI AVANSATE:
       - MST: Prim O(E log V), Kruskal O(E log E) + Union-Find
       - Flux maxim: Ford-Fulkerson (concept)

       ══════════════════════════════════════════
       CLASA A XII-A — Limbaje formale + Compilatoare (opțional)
       ══════════════════════════════════════════

       TEORETIC (dacă e în programă):
       - Automate finite deterministe (DFA) și nedeterministe (NFA)
       - Gramatici formale: regulare, independente de context
       - Expresii regulate: [a-z], *, +, ?, |
       - Arbori de derivare pentru gramatici

       ALGORITMI AVANSAȚI:
       - Hashing: funcție hash, coliziuni, tabele hash
       - Arbori de intervale (Segment Tree), Fenwick Tree — O(log n) per operație
       - Trie pentru șiruri de caractere
"""
