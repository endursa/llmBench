"""Schwere Zusatzaufgaben fuer qualitaetstest.py (--suite schwer). Nur Standardbibliothek."""

TASKS_HARD = [
 {"id": "frostpunkt_iterativ", "func": "dew_or_frost_point",
  "prompt": "Schreibe dew_or_frost_point(x_gkg: float, p_pa: float) -> float. x_gkg ist die Wasserbeladung in g/kg "
            "Trockenluft, p_pa der Gesamtdruck in Pa. Dampfdruck e = x*p/(0.622+x) mit x in kg/kg. Gesucht ist die "
            "Temperatur t (°C), bei der f(p,t)*e_s(t) = e gilt, mit Enhancement-Faktor f(p,t) = 1.00062 + 3.14e-8*p "
            "+ 5.6e-7*t**2. Saettigungsdampfdruck ueber Wasser e_w(t)=611.2*exp(17.62*t/(243.12+t)), ueber Eis "
            "e_i(t)=611.2*exp(22.46*t/(272.62+t)). Loese zuerst ueber Wasser; liegt diese Loesung unter 0 °C, gib "
            "stattdessen die Loesung ueber Eis zurueck (Frostpunkt). Genauigkeit besser 1e-6 K. x_gkg <= 0 oder "
            "p_pa <= 0 -> ValueError.",
  "tests": """
import math
def ew(t): return 611.2*math.exp(17.62*t/(243.12+t))
def ei(t): return 611.2*math.exp(22.46*t/(272.62+t))
def solve(es, e, p):
    lo, hi = -100.0, 100.0
    for _ in range(200):
        m = (lo+hi)/2
        if (1.00062+3.14e-8*p+5.6e-7*m*m)*es(m) < e: lo = m
        else: hi = m
    return (lo+hi)/2
def ref(xg, p):
    x = xg/1000; e = x*p/(0.622+x)
    t = solve(ew, e, p)
    return t if t >= 0 else solve(ei, e, p)
for xg, p in [(7.3,101325),(0.5,101325),(15,95000),(0.02,101325),(2.5,300000),(3.8,101325),(25,101325),(0.3,50000)]:
    r = ref(xg, p); v = dew_or_frost_point(xg, p)
    assert abs(v-r) < 1e-5, (xg, p, v, r)
for bad in [(0,101325),(-1,101325),(5,0)]:
    try:
        dew_or_frost_point(*bad); assert False, bad
    except ValueError: pass
"""},

 {"id": "ausdruck_parser", "func": "evaluate_expr", "forbid": r"(?<![\w.])(eval|exec|compile)\s*\(|import\s+ast|from\s+ast",
  "prompt": "Schreibe evaluate_expr(s: str, variables: dict | None = None) -> float, einen Parser/Auswerter fuer "
            "mathematische Ausdruecke OHNE eval/exec/compile/ast. Unterstuetzt: Zahlen (auch 1.5e-3), + - * /, "
            "Potenz ^ (rechtsassoziativ, bindet staerker als unaeres Minus: -2^2 = -4, aber 2^-1 = 0.5), unaeres "
            "Plus/Minus, Klammern, Funktionen sin cos sqrt exp ln mit einem Argument, Konstanten pi und e, Variablen "
            "aus dem dict. Leerzeichen beliebig. Bei Syntaxfehlern, unbekannten Namen, Division durch 0 oder "
            "Definitionsluecken (sqrt/ln negativ) -> ValueError.",
  "tests": """
import math
env = {"sin": math.sin, "cos": math.cos, "sqrt": math.sqrt, "exp": math.exp, "ln": math.log, "pi": math.pi, "e": math.e}
cases = [("1+2*3", 7), ("2^3^2", 512), ("-2^2", -4), ("2^-1", 0.5), ("(1+2)*-3", -9), ("--3", 3),
         ("1.5e-3*2", 0.003), ("sin(pi/2)+cos(0)", 2), ("sqrt(16)^0.5", 2), ("ln(e^3)", 3),
         ("2*x^2 - y/4", None), (" 3 - - - 2 ", 1), ("exp(1)-e", 0), ("10/4/5", 0.5), ("-(2+3)^2", -25),
         ("2^3*2", 16), ("+4-+2", 2), ("8/2^2", 2)]
vars_ = {"x": 3.0, "y": 2.0}
for s, want in cases:
    if want is None: want = 2*3.0**2 - 2.0/4
    got = evaluate_expr(s, vars_)
    assert abs(got - want) < 1e-9, (s, got, want)
for bad in ["1+", "(1+2", "1+2)", "2**3", "foo(1)", "z+1", "1/0", "sqrt(-1)", "ln(0)", "", "3 4", "sin()", "1e"]:
    try:
        evaluate_expr(bad, vars_); assert False, bad
    except ValueError: pass
"""},

 {"id": "regex_nfa", "func": "rx_fullmatch", "forbid": r"import\s+re\b|from\s+re\s+import|import\s+regex|import\s+fnmatch|from\s+fnmatch",
  "prompt": "Schreibe rx_fullmatch(pattern: str, text: str) -> bool OHNE das Modul re (oder regex/fnmatch). Das Muster "
            "muss den ganzen Text treffen. Unterstuetzt: Literale, '.', Quantoren * + ? (gierig egal, nur Treffer "
            "zaehlt), Gruppen ( ), Alternation |, Zeichenklassen [abc], Bereiche [a-z0-9], Negation [^...], "
            "Escape mit Backslash (z.B. \\. \\* \\( ). Die Laufzeit muss polynomiell sein (z.B. Thompson-NFA "
            "oder Memoisierung) - Muster wie (a|aa)*b gegen 'a'*40 duerfen nicht exponentiell laufen. Ungueltige "
            "Muster (offene Klammer, Quantor ohne Operand) -> ValueError.",
  "tests": """
import re as _re, random, time
pats = ["a*b", "(ab|cd)+e?", "[a-c]+x?", "[^ab]*", "a.c", "(a|b)*abb", "x(y|z)*\\\\.", "(a?)+b", "((ab)*|c)+",
        "\\\\(a\\\\)", "a|b|", "[0-9]+(\\\\.[0-9]*)?", "(a*)*b", "colou?r", "[a\\\\-z]+"]
rnd = random.Random(7)
alpha = "abcxyz.()0-9"
for p in pats:
    rp = _re.compile(p)
    for _ in range(300):
        s = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 8)))
        assert rx_fullmatch(p, s) == bool(rp.fullmatch(s)), (p, s)
    for s in ["", "ab", "abb", "aabb", "abcde", "colour", "color", "3.14", "x.", "xyzy.", "(a)", "a-z"]:
        assert rx_fullmatch(p, s) == bool(rp.fullmatch(s)), (p, s)
t0 = time.time()
assert rx_fullmatch("(a|aa)*b", "a"*40) is False
assert rx_fullmatch("(a*)*b", "a"*30) is False
assert rx_fullmatch("(a|aa)*", "a"*60) is True
assert time.time() - t0 < 5, "zu langsam (exponentielles Backtracking?)"
for bad in ["(ab", "*a", "a(|", "[ab", "+"]:
    try:
        rx_fullmatch(bad, "a"); assert False, bad
    except ValueError: pass
"""},

 {"id": "k_kuerzeste_pfade", "func": "k_shortest_paths",
  "prompt": "Schreibe k_shortest_paths(graph: dict, src, dst, k: int) -> list[tuple[float, list]]. graph ist ein "
            "gerichteter Graph {u: {v: gewicht, ...}, ...} mit Gewichten > 0. Liefere die k kuerzesten SCHLEIFENFREIEN "
            "Pfade von src nach dst (z.B. Yen-Algorithmus) als Liste (kosten, [knoten...]) aufsteigend nach Kosten; "
            "gibt es weniger als k, dann alle. Knoten ohne eigenen Eintrag haben keine ausgehenden Kanten. "
            "src == dst -> [(0, [src])].",
  "tests": """
import random, itertools
def all_paths(g, s, d):
    out = []
    def dfs(u, path, cost):
        if u == d: out.append((cost, path[:])); return
        for v, w in g.get(u, {}).items():
            if v not in path:
                path.append(v); dfs(v, path, cost+w); path.pop()
    dfs(s, [s], 0); return sorted(out, key=lambda x: x[0])
def check(g, s, d, k):
    ref = all_paths(g, s, d)[:k]
    got = k_shortest_paths(g, s, d, k)
    assert len(got) == len(ref), (len(got), len(ref))
    seen = set()
    for (c, p), (rc, _) in zip(got, ref):
        assert abs(c - rc) < 1e-9, (c, rc)
        assert p[0] == s and p[-1] == d and len(set(p)) == len(p), p
        assert abs(sum(g[a][b] for a, b in zip(p, p[1:])) - c) < 1e-9
        assert tuple(p) not in seen; seen.add(tuple(p))
g = {"C": {"D": 3, "E": 2}, "D": {"F": 4}, "E": {"D": 1, "F": 2, "G": 3}, "F": {"G": 2, "H": 1}, "G": {"H": 2}}
check(g, "C", "H", 3); check(g, "C", "H", 10)
rnd = random.Random(3)
for n in [6, 8, 9]:
    for _ in range(4):
        g = {i: {j: rnd.randint(1, 9) for j in range(n) if j != i and rnd.random() < 0.45} for i in range(n)}
        for k in [1, 4, 15]:
            check(g, 0, n-1, k)
assert k_shortest_paths({1: {2: 1}}, 2, 1, 3) == []
assert k_shortest_paths({1: {2: 1}}, 1, 1, 2) == [(0, [1])]
"""},

 {"id": "exp_fit_lm", "func": "fit_exp_decay", "forbid": r"import\s+(numpy|scipy)|from\s+(numpy|scipy)",
  "prompt": "Schreibe fit_exp_decay(t: list[float], y: list[float]) -> tuple[float, float, float], die die Parameter "
            "(A, tau, C) des Modells y = A*exp(-t/tau) + C per nichtlinearer Kleinste-Quadrate-Anpassung "
            "(z.B. Levenberg-Marquardt) bestimmt - nur Standardbibliothek, kein numpy/scipy. Sinnvolle Startwerte "
            "muss die Funktion selbst aus den Daten schaetzen. A darf negativ sein (Anstieg auf C). tau > 0. "
            "Weniger als 3 Punkte -> ValueError. Typischer Einsatz: Sprungantwort eines Feuchtesensors (t63).",
  "tests": """
import math, random
def gen(A, tau, C, n=40, tmax=None, noise=0.0, seed=1):
    rnd = random.Random(seed); tmax = tmax or 5*tau
    t = [tmax*i/(n-1) for i in range(n)]
    return t, [A*math.exp(-x/tau)+C + rnd.gauss(0, noise) for x in t]
for A, tau, C in [(50, 12, 30), (-60, 3.5, 75), (1e-3, 0.02, 2e-3), (200, 300, -10), (5, 1, 0)]:
    t, y = gen(A, tau, C)
    a, ta, c = fit_exp_decay(t, y)
    assert abs(a-A) < 1e-4*abs(A) and abs(ta-tau) < 1e-4*tau and abs(c-C) < 1e-4*max(abs(C), abs(A)), (A, tau, C, a, ta, c)
t, y = gen(-40, 8, 60, n=60, tmax=30, noise=0.2, seed=5)   # Sensor-Sprung 20->60 %rF, verrauscht, nur ~4 tau
a, ta, c = fit_exp_decay(t, y)
assert abs(ta-8) < 0.4 and abs(c-60) < 0.6 and abs(a+40) < 1.0, (a, ta, c)
try:
    fit_exp_decay([0, 1], [1, 2]); assert False
except ValueError: pass
"""},

 {"id": "diff_myers", "func": "edit_script",
  "prompt": "Schreibe edit_script(a: list[str], b: list[str]) -> list[tuple[str, str]], ein MINIMALES Edit-Skript "
            "(wie diff) aus Operationen ('=', zeile), ('-', zeile), ('+', zeile): '=' uebernimmt eine Zeile aus a, "
            "'-' loescht eine Zeile aus a, '+' fuegt eine Zeile aus b ein, in Reihenfolge abgearbeitet. Minimal heisst: "
            "Anzahl der '-' und '+' ist so klein wie moeglich. Muss effizient fuer grosse, aehnliche Dateien sein "
            "(z.B. Myers O((N+M)·D)): 20000 Zeilen mit wenigen Aenderungen in deutlich unter 5 s.",
  "tests": """
import random, time
def lcs(a, b):
    prev = [0]*(len(b)+1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j]+1 if x == y else max(prev[j+1], cur[j]))
        prev = cur
    return prev[-1]
def check(a, b, need_min=True):
    ops = edit_script(a, b)
    ra, rb, i = [], [], 0
    for op, line in ops:
        assert op in "=-+", op
        if op in "=-":
            assert a[i] == line, (i, line); i += 1
        if op in "=+": rb.append(line)
    assert i == len(a) and rb == b
    if need_min:
        assert sum(op != "=" for op, _ in ops) == len(a)+len(b)-2*lcs(a, b)
rnd = random.Random(11)
for _ in range(60):
    a = [rnd.choice("abcd") for _ in range(rnd.randint(0, 25))]
    b = [rnd.choice("abcd") for _ in range(rnd.randint(0, 25))]
    check(a, b)
check([], []); check(["x"], []); check([], ["y"])
a = [f"zeile {i} {rnd.random():.6f}" for i in range(20000)]
b = a[:]
for _ in range(15):
    p = rnd.randrange(len(b)); b[p] = "geaendert " + b[p]
del b[5000:5010]; b[12000:12000] = ["neu"]*7
t0 = time.time(); ops = edit_script(a, b); dt = time.time()-t0
assert dt < 5, f"zu langsam: {dt:.1f} s"
assert sum(op != "=" for op, _ in ops) == 15*2 + 10 + 7, sum(op != "=" for op, _ in ops)
check(a, b, need_min=False)
"""},

 {"id": "polynom_nullstellen", "func": "poly_roots", "forbid": r"import\s+(numpy|scipy|sympy|mpmath)|from\s+(numpy|scipy|sympy|mpmath)",
  "prompt": "Schreibe poly_roots(coeffs: list[float]) -> list[complex], die ALLE komplexen Nullstellen (mit "
            "Vielfachheit) eines Polynoms mit reellen Koeffizienten liefert, coeffs vom hoechsten Grad abwaerts "
            "(z.B. [1, 0, -1] = x^2-1). Nur Standardbibliothek. Einfache Nullstellen auf 1e-8 genau, auch "
            "mehrfache Nullstellen muessen brauchbar (1e-4) gefunden werden. Fuehrende Nullen ignorieren; "
            "konstantes oder leeres Polynom -> ValueError.",
  "tests": """
import cmath
def polymul(p, q):
    r = [0j]*(len(p)+len(q)-1)
    for i, a in enumerate(p):
        for j, b in enumerate(q): r[i+j] += a*b
    return r
def from_roots(rs):
    p = [1+0j]
    for r in rs: p = polymul(p, [1, -r])
    return [c.real for c in p]
def match(got, want, tol):
    got = list(got); assert len(got) == len(want), (len(got), len(want))
    for w in want:
        k = min(range(len(got)), key=lambda i: abs(got[i]-w))
        assert abs(got[k]-w) < tol*max(1, abs(w)), (w, got[k]); got.pop(k)
cases = [([1, -2], 1e-8), ([3, -1, 4], 1e-8), ([1j, -1j, 2, -3, 0.5], 1e-8), ([1+2j, 1-2j, -1+0.5j, -1-0.5j, 7], 1e-8),
         ([1, 1, 1, -2], 1e-4), ([0.5, 0.5, -3+1j, -3-1j], 1e-4), (list(range(1, 11)), 1e-6), ([0, 0, 1], 1e-4)]
for rs, tol in cases:
    match(poly_roots(from_roots(rs)), rs, tol)
match(poly_roots([0, 0, 2, 0, -8]), [2, -2], 1e-8)
match(poly_roots([1, 0, 1]), [1j, -1j], 1e-8)
for bad in [[], [5], [0, 0, 3]]:
    try:
        poly_roots(bad); assert False, bad
    except ValueError: pass
"""},

 {"id": "crc_generisch", "func": "crc_generic", "forbid": r"import\s+(crcmod|crcengine|binascii|zlib)|from\s+(crcmod|crcengine|binascii|zlib)",
  "prompt": "Schreibe crc_generic(data: bytes, width: int, poly: int, init: int, refin: bool, refout: bool, "
            "xorout: int) -> int nach dem Rocksoft/Williams-Parametermodell (wie im CRC-Katalog von Greg Cook), "
            "fuer beliebige Breiten 1..64 Bit, auch nicht durch 8 teilbare (CRC-3, CRC-5). Ohne binascii/zlib/crcmod. "
            "width ausserhalb 1..64 -> ValueError.",
  "tests": """
chk = b"123456789"
cat = [((32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF), 0xCBF43926),
       ((32, 0x1EDC6F41, 0xFFFFFFFF, True, True, 0xFFFFFFFF), 0xE3069283),
       ((32, 0x04C11DB7, 0xFFFFFFFF, False, False, 0x00000000), 0x0376E6E7),
       ((16, 0x8005, 0xFFFF, True, True, 0x0000), 0x4B37),
       ((16, 0x1021, 0x0000, True, True, 0x0000), 0x2189),
       ((16, 0x1021, 0x0000, False, False, 0x0000), 0x31C3),
       ((16, 0x1021, 0xFFFF, False, False, 0x0000), 0x29B1),
       ((8, 0x07, 0x00, False, False, 0x00), 0xF4),
       ((8, 0x31, 0x00, True, True, 0x00), 0xA1),
       ((5, 0x05, 0x1F, True, True, 0x1F), 0x19),
       ((3, 0x3, 0x7, True, True, 0x0), 0x6),
       ((7, 0x09, 0x00, False, False, 0x00), 0x75),
       ((64, 0x42F0E1EBA9EA3693, 0xFFFFFFFFFFFFFFFF, True, True, 0xFFFFFFFFFFFFFFFF), 0x995DC9BBDF1939FA),
       ((64, 0x42F0E1EBA9EA3693, 0, False, False, 0), 0x6C40DF5F0B497347),
       ((12, 0x80F, 0x000, False, True, 0x000), 0xDAF)]
for params, want in cat:
    got = crc_generic(chk, *params)
    assert got == want, (params, hex(got), hex(want))
assert crc_generic(b"", 16, 0x1021, 0xFFFF, False, False, 0) == 0xFFFF
for w in [0, 65]:
    try:
        crc_generic(chk, w, 1, 0, False, False, 0); assert False
    except ValueError: pass
"""},
]

QUESTIONS_HARD = [
 ("frostpunkt_rf", "Luft mit Frostpunkt -20,0 °C, Lufttemperatur -5,0 °C, p = 1013,25 hPa. Verwende Magnus nach WMO: "
  "ueber Wasser c=6,112 hPa, a=17,62, b=243,12 °C; ueber Eis c=6,112 hPa, a=22,46, b=272,62 °C; ohne "
  "Enhancement-Faktor. Berechne (1) den Dampfdruck, (2) den Taupunkt ueber unterkuehltem Wasser, (3) die relative "
  "Feuchte nach WMO-Definition (bezogen auf Wasser) und (4) bezogen auf Eis. Erklaere, warum ein Taupunktspiegel "
  "bei dieser Luft je nach Kondensatphase unterschiedliche Werte anzeigen kann und wie gross der Fehler waere.",
  [("e [hPa]", 1.033, 0.01), ("Td [°C]", -22.29, 0.15), ("rF Wasser [%]", 24.46, 0.3), ("rF Eis [%]", 25.70, 0.3)]),
 ("zweitemp_zweidruck", "Ein Zwei-Temperatur-Zwei-Druck-Generator saettigt bei 5,000 bar(abs) und 10,00 °C, der "
  "Pruefraum hat 1,000 bar(abs) und 25,00 °C. Verwende e_w(t)=6,112*exp(17,62 t/(243,12+t)) hPa und den "
  "Enhancement-Faktor f(p) = 1,0007 + 3,46e-6*p (p in hPa, Buck). Berechne die relative Feuchte im Pruefraum mit "
  "f, die Abweichung, wenn man f vergisst (in %rF), und den Taupunkt im Pruefraum.",
  [("rF [%]", 7.87, 0.05), ("Fehler ohne f [%rF]", 0.107, 0.02), ("Td [°C]", -11.8, 0.15)]),
 ("kalibriergerade", "Kalibrierung eines Feuchtesensors gegen Referenz (Referenz %rF -> Anzeige %rF): 10,0->11,2; "
  "30,0->30,9; 50,0->50,4; 70,0->69,6; 90,0->89,1. Bestimme die Ausgleichsgerade Anzeige = a + b*Referenz "
  "(kleinste Quadrate), die Reststandardabweichung s, die Korrekturfunktion Referenz = f(Anzeige), den korrigierten "
  "Wert fuer eine Anzeige von 60,0 %rF und dessen Standardunsicherheit aus der Regression (Vertrauensbereich der "
  "Geraden an dieser Stelle, k=1).",
  [("a", 1.615, 0.01), ("b", 0.9725, 0.001), ("s [%rF]", 0.149, 0.005), ("korrigiert [%rF]", 60.04, 0.03), ("u Gerade [%rF]", 0.073, 0.006)]),
 ("psychrometer", "Aspirationspsychrometer nach Assmann: Trockentemperatur 25,0 °C, Feuchttemperatur 18,0 °C, "
  "p = 1013,25 hPa, Psychrometerkonstante A = 6,62e-4 1/K (Wasser, belueftet). Mit e_w(t)=6,112*exp(17,62 t/"
  "(243,12+t)) hPa: berechne Dampfdruck, relative Feuchte und Taupunkt. Schaetze danach, wie stark sich die rF "
  "aendert, wenn die Feuchttemperatur um 0,1 K falsch gemessen wird, und nenne die zwei groessten praktischen "
  "Fehlerquellen.",
  [("e [hPa]", 15.90, 0.05), ("rF [%]", 50.3, 0.2), ("Td [°C]", 13.94, 0.1), ("drF/0,1K [%rF]", 0.62, 0.06)]),
]
