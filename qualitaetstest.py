#!/usr/bin/env python3
"""
Qualitaetsvergleich lokaler LLMs (OpenAI-kompatible API) - nur Python-Standardbibliothek.

Teil A: 12 Programmieraufgaben mit Unit-Tests -> automatisch bewertet (generierter Code wird lokal
        in einem Unterprozess mit Zeitlimit ausgefuehrt).
Teil B: 4 Fachfragen Feuchtemesstechnik -> Antworten werden gespeichert, Bewertung durch dich.

Ablauf (immer nur EIN Server laeuft, beide nutzen Port 8080):
  1) Strata:   python qualitaetstest.py run --label gyro-s  --model qwen3.8-flash-next-gyro-gyro-s
               (API-Schluessel aus Umgebungsvariable STRATA_API_KEY oder --key)
  2) Qwen-27B: python qualitaetstest.py run --label qwen27b --model qwen3.8-27b
  3) Vergleich: python qualitaetstest.py compare ergebnis_gyro-s.json ergebnis_qwen27b.json

Schwere Zusatzrunde (21.11.2026, aus aufgaben_schwer.py): --suite schwer
  8 Aufgaben (Frostpunkt iterativ, Ausdrucksparser, Regex-NFA, Yen k-kuerzeste Pfade, Levenberg-Marquardt,
  Myers-Diff, Polynom-Nullstellen, generischer CRC) + 4 Rechenfragen mit Kennzahlen-Autocheck.
  python qualitaetstest.py run --suite schwer --label gemma-mtp-S --model gemma-4-26b-a4b-mtp --max-tokens 24000
  --suite alle = Standard + schwer.
"""
import argparse, json, os, re, subprocess, sys, tempfile, textwrap, time, urllib.request, urllib.error

# ----------------------------------------------------------------------------- Teil A: Aufgaben
TASKS = [
 {"id": "taupunkt_magnus", "func": "dew_point",
  "prompt": "Schreibe eine Python-Funktion dew_point(t_c: float, rh: float) -> float, die den Taupunkt in °C "
            "aus Lufttemperatur t_c (°C) und relativer Feuchte rh (%) nach der Magnus-Formel ueber Wasser "
            "mit a=17.62 und b=243.12 °C berechnet. Bei rh <= 0 oder rh > 100 soll ValueError geworfen werden.",
  "tests": """
import math
def ref(t, rh):
    g = math.log(rh/100) + 17.62*t/(243.12+t)
    return 243.12*g/(17.62-g)
for t, rh in [(20,50),(25,80),(0,30),(-10,90),(40,10),(23.5,100)]:
    assert abs(dew_point(t, rh) - ref(t, rh)) < 1e-6, (t, rh)
for bad in [0, -5, 100.1]:
    try:
        dew_point(20, bad); assert False, bad
    except ValueError: pass
"""},
 {"id": "dauer_parsen", "func": "parse_duration",
  "prompt": "Schreibe parse_duration(s: str) -> int, die Dauern wie '1h30m15s', '45m', '2h', '90s', '1d2h' "
            "(d=Tage, h, m, s; jede Einheit hoechstens einmal, Reihenfolge d,h,m,s) in Sekunden umrechnet. "
            "Leerstring oder ungueltige Formate ('1x', 'h5', '5m5h', '1h1h') -> ValueError.",
  "tests": """
assert parse_duration('1h30m15s') == 5415
assert parse_duration('45m') == 2700
assert parse_duration('2h') == 7200
assert parse_duration('90s') == 90
assert parse_duration('1d2h') == 93600
assert parse_duration('0s') == 0
for bad in ['', '1x', 'h5', '5m5h', '1h1h', '10']:
    try:
        parse_duration(bad); assert False, bad
    except ValueError: pass
"""},
 {"id": "roemisch", "func": "int_to_roman, roman_to_int",
  "prompt": "Schreibe zwei Funktionen int_to_roman(n: int) -> str und roman_to_int(s: str) -> int fuer "
            "1..3999 in Standard-Subtraktionsschreibweise. Werte ausserhalb und ungueltige Strings "
            "(z.B. 'IIII', 'VX', 'IC', '') -> ValueError.",
  "tests": """
for n in range(1, 4000):
    assert roman_to_int(int_to_roman(n)) == n, n
assert int_to_roman(1994) == 'MCMXCIV'
assert int_to_roman(3999) == 'MMMCMXCIX'
assert roman_to_int('XLII') == 42
for bad in [0, 4000, -1]:
    try:
        int_to_roman(bad); assert False, bad
    except ValueError: pass
for bad in ['IIII', 'VX', 'IC', '', 'ABC']:
    try:
        roman_to_int(bad); assert False, bad
    except ValueError: pass
"""},
 {"id": "intervalle", "func": "merge_intervals",
  "prompt": "Schreibe merge_intervals(iv: list[tuple[float,float]]) -> list[tuple[float,float]], die sich "
            "ueberlappende oder beruehrende geschlossene Intervalle zusammenfasst und sortiert zurueckgibt. "
            "Intervalle mit start > end -> ValueError.",
  "tests": """
assert merge_intervals([]) == []
assert merge_intervals([(1,3),(2,6),(8,10),(15,18)]) == [(1,6),(8,10),(15,18)]
assert merge_intervals([(1,4),(4,5)]) == [(1,5)]
assert merge_intervals([(5,6),(1,2),(2,3)]) == [(1,3),(5,6)]
assert merge_intervals([(1,10),(2,3),(4,5)]) == [(1,10)]
try:
    merge_intervals([(3,1)]); assert False
except ValueError: pass
"""},
 {"id": "lru_cache", "func": "LRUCache",
  "prompt": "Schreibe eine Klasse LRUCache(capacity: int) mit get(key) -> Wert oder -1 und put(key, value). "
            "Bei voller Kapazitaet wird der am laengsten nicht benutzte Eintrag entfernt. get und put zaehlen "
            "als Benutzung. capacity <= 0 -> ValueError. Ohne functools.lru_cache.",
  "tests": """
c = LRUCache(2)
c.put(1, 1); c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) == -1
c.put(4, 4)
assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
c.put(3, 33); c.put(5, 5)
assert c.get(4) == -1 and c.get(3) == 33
try:
    LRUCache(0); assert False
except ValueError: pass
"""},
 {"id": "topo_sort", "func": "topo_sort",
  "prompt": "Schreibe topo_sort(deps: dict[str, list[str]]) -> list[str]. deps[x] sind die Knoten, die VOR x "
            "kommen muessen. Knoten, die nur als Abhaengigkeit vorkommen, gehoeren auch ins Ergebnis. "
            "Bei Zyklen ValueError. Bei mehreren gueltigen Reihenfolgen: alphabetisch kleinster verfuegbarer Knoten zuerst.",
  "tests": """
assert topo_sort({}) == []
assert topo_sort({'b': ['a'], 'c': ['b']}) == ['a', 'b', 'c']
assert topo_sort({'d': ['b', 'c'], 'b': ['a'], 'c': ['a']}) == ['a', 'b', 'c', 'd']
assert topo_sort({'z': [], 'y': [], 'x': ['z']}) == ['y', 'z', 'x']
for bad in [{'a': ['b'], 'b': ['a']}, {'a': ['a']}, {'a': ['b'], 'b': ['c'], 'c': ['a']}]:
    try:
        topo_sort(bad); assert False, bad
    except ValueError: pass
"""},
 {"id": "rechner", "func": "evaluate",
  "prompt": "Schreibe evaluate(expr: str) -> float, die arithmetische Ausdruecke mit + - * /, Klammern, "
            "unaerem Minus, Dezimalzahlen und Leerzeichen auswertet - OHNE eval/exec/ast/compile. "
            "Punkt vor Strich, Linksassoziativitaet. Division durch 0 -> ZeroDivisionError, Syntaxfehler -> ValueError.",
  "tests": """
import math
cases = {'1+2*3': 7, '(1+2)*3': 9, '10/4': 2.5, '2*(3+4)*5': 70, '-3+5': 2, '-(2+3)*2': -10,
         ' 1.5 * 2 ': 3, '8-3-2': 3, '16/4/2': 2, '2*-3': -6, '((2))': 2, '3+4*2/(1-5)': 1}
for e, v in cases.items():
    assert math.isclose(evaluate(e), v), (e, evaluate(e))
for bad in ['', '1+', '(1+2', '1+2)', '2**3', 'abc', '1 2']:
    try:
        evaluate(bad); assert False, bad
    except ValueError: pass
try:
    evaluate('1/(2-2)'); assert False
except ZeroDivisionError: pass
"""},
 {"id": "crc16", "func": "crc16_ccitt",
  "prompt": "Schreibe crc16_ccitt(data: bytes) -> int fuer CRC-16/CCITT-FALSE (Polynom 0x1021, Startwert 0xFFFF, "
            "keine Reflexion, kein Final-XOR). Ohne externe Bibliotheken wie crcmod oder binascii.",
  "tests": """
assert crc16_ccitt(b'123456789') == 0x29B1
assert crc16_ccitt(b'') == 0xFFFF
assert crc16_ccitt(b'A') == 0xB915
assert crc16_ccitt(bytes(range(256))) == 0x3FBD
"""},
 {"id": "regression", "func": "linfit",
  "prompt": "Schreibe linfit(x: list[float], y: list[float]) -> tuple[float, float, float], die per Methode der "
            "kleinsten Quadrate Steigung, Achsenabschnitt und Bestimmtheitsmass R^2 zurueckgibt. Ohne numpy. "
            "Unterschiedliche Laengen, weniger als 2 Punkte oder alle x gleich -> ValueError. "
            "Wenn alle y gleich sind, ist R^2 = 1.0.",
  "tests": """
import math
k, d, r2 = linfit([0,1,2,3], [1,3,5,7])
assert math.isclose(k, 2) and math.isclose(d, 1) and math.isclose(r2, 1)
k, d, r2 = linfit([1,2,3,4,5], [2.1,3.9,6.2,7.8,10.1])
assert math.isclose(k, 1.99, abs_tol=1e-9) and math.isclose(d, 0.05, abs_tol=1e-9)
assert math.isclose(r2, 0.9973053289, abs_tol=1e-6), r2
k, d, r2 = linfit([1,2,3], [5,5,5])
assert math.isclose(k, 0, abs_tol=1e-12) and math.isclose(d, 5) and math.isclose(r2, 1.0)
for bx, by in [([1],[1]), ([1,2],[1]), ([2,2,2],[1,2,3])]:
    try:
        linfit(bx, by); assert False
    except ValueError: pass
"""},
 {"id": "gleitender_median", "func": "sliding_median",
  "prompt": "Schreibe sliding_median(values: list[float], k: int) -> list[float], die den Median jedes "
            "zusammenhaengenden Fensters der Laenge k liefert (bei geradem k Mittelwert der beiden mittleren Werte). "
            "k < 1 oder k > len(values) -> ValueError. Muss fuer 20000 Werte und k=501 unter 2 Sekunden laufen.",
  "tests": """
import random, time, statistics
assert sliding_median([1,3,-1,-3,5,3,6,7], 3) == [1,-1,-1,3,5,6]
assert sliding_median([1,2,3,4], 2) == [1.5,2.5,3.5]
assert sliding_median([5], 1) == [5]
for bad in [0, 5]:
    try:
        sliding_median([1,2,3,4], bad); assert False
    except ValueError: pass
random.seed(1); v = [random.random() for _ in range(20000)]
t = time.time(); r = sliding_median(v, 501); dt = time.time() - t
assert dt < 2.0, f'zu langsam: {dt:.2f}s'
assert len(r) == 20000 - 500
for i in (0, 777, 19499):
    assert abs(r[i] - statistics.median(v[i:i+501])) < 1e-12
"""},
 {"id": "ringpuffer_mittel", "func": "RunningStats",
  "prompt": "Schreibe eine Klasse RunningStats mit add(x: float), count, mean, variance (Stichprobenvarianz, "
            "n-1) und std als Properties, numerisch stabil nach Welford. Bei count < 2 sollen variance und std "
            "0.0 liefern, bei count == 0 mean ebenfalls 0.0.",
  "tests": """
import math, statistics, random
s = RunningStats()
assert s.count == 0 and s.mean == 0.0 and s.variance == 0.0
data = [1e9 + x for x in (4, 7, 13, 16)]
for x in data: s.add(x)
assert s.count == 4
assert math.isclose(s.mean, statistics.mean(data))
assert math.isclose(s.variance, statistics.variance(data), rel_tol=1e-9), s.variance
assert math.isclose(s.std, statistics.stdev(data), rel_tol=1e-9)
s2 = RunningStats(); s2.add(5.0)
assert s2.variance == 0.0 and s2.std == 0.0 and s2.mean == 5.0
"""},
 {"id": "relative_feuchte_mischung", "func": "rh_after_mixing",
  "prompt": "Schreibe rh_after_mixing(t1, rh1, m1, t2, rh2, m2, p=101325.0) -> tuple[float, float]. Zwei feuchte "
            "Luftstroeme (Temperatur °C, rel. Feuchte %, Trockenluft-Massenstrom kg/s) werden adiabat gemischt. "
            "Berechne Mischtemperatur (massengewichtet, cp konstant genuegt) und relative Feuchte der Mischung in %. "
            "Verwende Saettigungsdampfdruck nach Magnus ueber Wasser e_s(t)=611.2*exp(17.62*t/(243.12+t)) Pa und "
            "Wasserbeladung x = 0.622*e/(p-e). Massenstroeme <= 0 -> ValueError.",
  "tests": """
import math
def es(t): return 611.2*math.exp(17.62*t/(243.12+t))
def ref(t1, r1, m1, t2, r2, m2, p=101325.0):
    e1, e2 = r1/100*es(t1), r2/100*es(t2)
    x1, x2 = 0.622*e1/(p-e1), 0.622*e2/(p-e2)
    x = (m1*x1+m2*x2)/(m1+m2); t = (m1*t1+m2*t2)/(m1+m2)
    e = x*p/(0.622+x); return t, 100*e/es(t)
for args in [(20,50,1,30,60,1), (10,80,2,25,30,1), (0,90,1,40,20,3)]:
    t, rh = rh_after_mixing(*args); tr, rr = ref(*args)
    assert abs(t-tr) < 1e-6 and abs(rh-rr) < 0.05, (args, t, rh, tr, rr)
try:
    rh_after_mixing(20,50,0,30,60,1); assert False
except ValueError: pass
"""},
]

# ----------------------------------------------------------------------------- Teil B: Fachfragen
QUESTIONS = [
 ("zweidruck", "Ein Zweidruck-Feuchtegenerator saettigt Luft bei 3,00 bar(abs) und 20,00 °C und entspannt sie "
  "isotherm auf 1,00 bar(abs) bei 20,00 °C. Berechne die relative Feuchte im Pruefraum, zuerst ohne, dann mit "
  "Enhancement-Faktoren (nenne die verwendeten Werte), und erklaere kurz, warum f(p,T) noetig ist."),
 ("taupunktspiegel", "Nenne die wichtigsten Fehlerquellen eines Taupunktspiegel-Hygrometers unterhalb 0 °C "
  "(u.a. Tau/Reif-Unterscheidung, Raoult-Effekt durch Kontamination, Kelvin-Effekt) und wie man sie in der Praxis "
  "erkennt und minimiert."),
 ("unsicherheit", "Relative Feuchte wird aus Taupunkt (u(Td) = 0,10 K, k=1) und Lufttemperatur (u(T) = 0,05 K, k=1) "
  "bestimmt, Arbeitspunkt T = 25 °C, Td = 13,9 °C. Leite die Sensitivitaetskoeffizienten her (Magnus genuegt), "
  "berechne die kombinierte Standardunsicherheit von rF in %rF und die erweiterte Unsicherheit fuer k=2."),
 ("kapazitiv", "Ein kapazitiver Polymer-Feuchtesensor zeigt nach mehreren Tagen bei 95 %rF eine Drift von +2 %rF "
  "und eine Hysterese von 1,5 %rF. Welche physikalischen Ursachen sind wahrscheinlich, wie wuerdest du eine "
  "Kalibrierung und Kompensation (Temperatur, Hysterese, Langzeitdrift) aufbauen?"),
]

SYSTEM_CODE = ("Du bist ein sorgfaeltiger Python-Entwickler. Liefere die vollstaendige Implementierung in genau "
               "einem ```python Codeblock, ohne Beispielaufrufe, ohne Tests und ohne input().")
SYSTEM_FACH = "Du bist Experte fuer Feuchtemesstechnik und Metrologie. Antworte auf Deutsch, praezise, mit Rechenweg."


EFFORT = None   # per --effort gesetzt: an das Chat-Template durchgereicht (Qwen3.8: low/medium/xhigh, Inkling 2: none..max)


SSL_CTX = None   # --insecure: Zertifikat nicht pruefen (nur fuer selbstsignierte Test-Server)


def api(url, path):
    """Basis-URL normalisieren: mit oder ohne abschliessendes /v1 angebbar, http oder https."""
    u = url.strip().rstrip("/")
    if u.endswith("/v1"):
        u = u[:-3]
    elif u.endswith("/api"):          # Open WebUI: /api/models, /api/chat/completions (Schluessel sk-...)
        return u + path.replace("/v1", "", 1)
    return u + path


def open_url(req, timeout):
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX)
    except urllib.error.URLError as e:
        if isinstance(e, urllib.error.HTTPError) and e.code in (401, 403):
            sent = req.get_header("Authorization") or ""
            klen = max(len(sent) - 7, 0)
            raise RuntimeError(f"HTTP {e.code} von {req.full_url}: Schluessel abgelehnt. "
                               f"Mitgeschickt: {'ja, ' + str(klen) + ' Zeichen' if sent else 'NEIN (QT_API_KEY leer?)'}. "
                               "Liegt der Server hinter Open WebUI, die URL mit /api am Ende angeben.") from None
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            raise RuntimeError("HTTPS-Zertifikat wird nicht vertraut (z.B. Firmen-CA oder selbstsigniert). "
                               "Firmen-CA: muss im Windows-Zertifikatsspeicher sein; sonst notfalls --insecure.") from e
        raise


TIMEOUT = 3600   # s pro Anfrage; langsame Systeme (z.B. DGX Spark, dichtes 27B) brauchen fuer 24k Tokens > 15 min


def chat(url, key, model, system, user, max_tokens, timeout=None):
    timeout = timeout or TIMEOUT
    payload = {"model": model, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if EFFORT:
        payload["chat_template_kwargs"] = {"reasoning_effort": EFFORT}
    body = json.dumps(payload).encode()
    hdr = {"Content-Type": "application/json"}
    if key:
        hdr["Authorization"] = f"Bearer {key}"; hdr["x-api-key"] = key
    req = urllib.request.Request(api(url, "/v1/chat/completions"), data=body, headers=hdr)
    t0 = time.time()
    with open_url(req, timeout) as r:
        j = json.load(r)
    dt = time.time() - t0
    ch = j["choices"][0]; msg = ch["message"]
    usage = j.get("usage", {}) or {}
    usage["finish_reason"] = ch.get("finish_reason")
    return (msg.get("content") or ""), (msg.get("reasoning_content") or ""), usage, dt


def extract_code(text):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len)
    return text  # Fallback: ganze Antwort


def run_tests(code, tests, timeout=30):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write(code + "\n\n# ---- Tests ----\n" + textwrap.dedent(tests))
        try:
            r = subprocess.run([sys.executable, p], cwd=d, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        if r.returncode == 0:
            return True, ""
        err = (r.stderr or r.stdout).strip().splitlines()
        return False, (err[-1] if err else f"Exit {r.returncode}")[:200]


def kennzahlen(answer, expects):
    """Sucht zu jeder erwarteten Kennzahl eine Zahl in der Antwort innerhalb der Toleranz (deutsches Komma ok)."""
    nums = []
    # LaTeX-/Markdown-Schreibweisen normalisieren: 7{,}87  1{.}5  12\,345  \approx  **0,11**
    answer = (answer or "").replace("{,}", ",").replace("{.}", ".").replace("\\,", "").replace("\\;", " ")
    answer = re.sub(r"\\(approx|mathbf|text|boxed|mathrm|quad)", " ", answer)
    for m in re.finditer(r"(?<![\w.,])[-\u2212\u2013]?\s?\d+(?:[.,]\d+)?(?:\s?[eE]\s?[-+]?\d+)?", answer or ""):
        txt = m.group(0).replace("\u2212", "-").replace("\u2013", "-").replace(" ", "").replace(",", ".")
        try: nums.append(float(txt))
        except ValueError: pass
    hits = []
    for name, val, tol in expects:
        ok = any(abs(n - val) <= tol for n in nums) or (val < 0 and any(abs(-n - val) <= tol for n in nums if n > 0))
        hits.append({"name": name, "soll": val, "tol": tol, "gefunden": ok})
    return hits


def select_suite(name):
    global TASKS, QUESTIONS
    if name == "standard":
        return TASKS, [(q[0], q[1], None) for q in QUESTIONS]
    from aufgaben_schwer import TASKS_HARD, QUESTIONS_HARD
    hard_q = [(q[0], q[1], q[2]) for q in QUESTIONS_HARD]
    if name == "schwer":
        return TASKS_HARD, hard_q
    return TASKS + TASKS_HARD, [(q[0], q[1], None) for q in QUESTIONS] + hard_q


def cmd_run(a):
    global EFFORT
    key = a.key or os.environ.get("QT_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("STRATA_API_KEY", "")
    global TIMEOUT
    TIMEOUT = a.timeout
    EFFORT = a.effort
    TASKS, QUESTIONS = select_suite(a.suite)
    res = {"label": a.label, "model": a.model, "url": a.url, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "suite": a.suite, "effort": a.effort, "tasks": [], "questions": []}
    print(f"== Teil A: {len(TASKS)} Programmieraufgaben ({a.label}) ==")
    for t in TASKS:
        try:
            content, reasoning, usage, dt = chat(a.url, key, a.model, SYSTEM_CODE, t["prompt"], a.max_tokens)
            note = ""
            if not content.strip() and "```" in reasoning and usage.get("finish_reason") != "length":
                content = reasoning[reasoning.rfind("```", 0, reasoning.rfind("```")):] if reasoning.count("```") >= 2 else ""
                note = " [Code aus Thinking-Teil]"
            code = extract_code(content)
            if not content.strip():
                fr = usage.get("finish_reason")
                ok, err = False, ("Token-Limit im Thinking" if fr == "length" else f"leere Antwort (finish_reason={fr})")
            elif a.forbid_eval and t["id"] == "rechner" and re.search(r"(?<![\w.])(eval|exec|compile)\s*\(|import\s+ast|from\s+ast", code):
                ok, err = False, "verbotenes eval/exec/ast verwendet"
            elif a.forbid_eval and t.get("forbid") and re.search(t["forbid"], code):
                ok, err = False, "verbotenes Modul/Konstrukt: " + re.search(t["forbid"], code).group(0)
            else:
                ok, err = run_tests(code, t["tests"], timeout=t.get("timeout", 60))
            err = (err or "") + note
        except Exception as e:
            ok, err, usage, dt, code = False, f"API-Fehler: {e}", {}, 0, ""
        res["tasks"].append({"id": t["id"], "ok": ok, "error": err, "seconds": round(dt, 1),
                             "tokens": usage.get("completion_tokens"), "code": code,
                             "finish_reason": (usage or {}).get("finish_reason"),
                             "reasoning_tail": (locals().get("reasoning") or "")[-3000:] if not ok else ""})
        print(f"  {'OK  ' if ok else 'FAIL'} {t['id']:<26} {dt:6.1f}s  {usage.get('completion_tokens','?'):>6} Tok  {err}")
    print(f"== Teil B: {len(QUESTIONS)} Fachfragen ==")
    for qid, q, expects in QUESTIONS:
        try:
            content, reasoning, usage, dt = chat(a.url, key, a.model, SYSTEM_FACH, q, a.max_tokens)
        except Exception as e:
            content, usage, dt = f"API-Fehler: {e}", {}, 0
        entry = {"id": qid, "question": q, "answer": content, "seconds": round(dt, 1),
                 "tokens": usage.get("completion_tokens")}
        extra = ""
        if expects:
            entry["kennzahlen"] = kennzahlen(content, expects)
            extra = f"  Kennzahlen {sum(h['gefunden'] for h in entry['kennzahlen'])}/{len(expects)}"
        res["questions"].append(entry)
        print(f"  {qid:<20} {dt:6.1f}s  {usage.get('completion_tokens','?'):>6} Tok{extra}")
    passed = sum(t["ok"] for t in res["tasks"])
    res["score"] = f"{passed}/{len(TASKS)}"
    res["total_seconds"] = round(sum(t["seconds"] for t in res["tasks"]) + sum(q["seconds"] for q in res["questions"]), 1)
    res["total_tokens"] = sum((t["tokens"] or 0) for t in res["tasks"]) + sum((q["tokens"] or 0) for q in res["questions"])
    out = f"ergebnis_{a.label}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"\nErgebnis {a.label}: {res['score']} Aufgaben bestanden, {res['total_tokens']} Tokens, {res['total_seconds']} s -> {out}")


def cmd_compare(a):
    A = [json.load(open(p, encoding="utf-8")) for p in a.files]
    L = [x["label"] for x in A]
    lines = [f"# Qualitaetsvergleich: {' vs. '.join(L)}", "",
             "## Teil A - Programmieraufgaben (automatisch bewertet)", "",
             "| Aufgabe | " + " | ".join(L) + " |", "|---|" + "---|" * len(L)]
    for i, t in enumerate(A[0]["tasks"]):
        cells = []
        for x in A:
            r = x["tasks"][i]
            cells.append(("✅" if r["ok"] else "❌ " + (r["error"] or "")[:60]) + f" ({r['seconds']} s, {r['tokens']} Tok)")
        lines.append(f"| {t['id']} | " + " | ".join(cells) + " |")
    lines += ["| **Summe** | " + " | ".join(f"**{x['score']}**" for x in A) + " |",
              "| Tokens gesamt | " + " | ".join(str(x["total_tokens"]) for x in A) + " |",
              "| Zeit gesamt | " + " | ".join(f"{x['total_seconds']} s" for x in A) + " |", "",
              "## Teil B - Fachfragen (bitte selbst bewerten)", ""]
    try:
        from aufgaben_schwer import QUESTIONS_HARD
        exp_map = {q[0]: q[2] for q in QUESTIONS_HARD}
    except ImportError:
        exp_map = {}
    for x in A:   # Kennzahlen mit aktueller Pruefroutine neu bewerten
        for r in x["questions"]:
            if r["id"] in exp_map:
                r["kennzahlen"] = kennzahlen(r["answer"], exp_map[r["id"]])
    for i, q0 in enumerate(A[0]["questions"]):
        lines += [f"### {q0['id']}", "", f"> {q0['question']}", ""]
        for x in A:
            r = x["questions"][i]
            kz = ""
            if r.get("kennzahlen"):
                kz = " – Kennzahlen " + ", ".join(("✅ " if h["gefunden"] else "❌ ") + f"{h['name']}={h['soll']}" for h in r["kennzahlen"])
            lines += [f"#### {x['label']} ({r['seconds']} s, {r['tokens']} Tok){kz}", "", r["answer"].strip() or "_(leer)_", ""]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Vergleich geschrieben: {a.out}")
    for x in A:
        kz = [h["gefunden"] for r in x["questions"] for h in r.get("kennzahlen", [])]
        kzs = f"  Kennzahlen {sum(kz)}/{len(kz)}" if kz else ""
        print(f"  {x['label']:<12} {x['score']:>6}  {x['total_tokens']:>7} Tok  {x['total_seconds']:>7} s{kzs}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Test gegen den laufenden Server")
    r.add_argument("--label", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--url", default="http://127.0.0.1:8080")
    r.add_argument("--key", default="")
    r.add_argument("--max-tokens", type=int, default=12000, help="inkl. Thinking (Standard 12000)")
    r.add_argument("--allow-eval", dest="forbid_eval", action="store_false")
    r.add_argument("--effort", default=None,
                   help="reasoning_effort ans Chat-Template, z.B. low / medium / xhigh (Qwen3.8 Standard: xhigh)")
    r.add_argument("--suite", choices=["standard", "schwer", "alle"], default="standard",
                   help="standard = 12+4 (vergleichbar mit alten Laeufen), schwer = 8+4 neu, alle = beides")
    r.add_argument("--timeout", type=int, default=3600, help="Sekunden pro Anfrage (Standard 3600)")
    m = sub.add_parser("models", help="Modell-IDs des Servers auflisten (GET /v1/models)")
    m.add_argument("--url", default="http://127.0.0.1:8080")
    m.add_argument("--key", default="")
    for sp in (r, m):
        sp.add_argument("--insecure", action="store_true", help="HTTPS-Zertifikat nicht pruefen (nur Notloesung)")
    c = sub.add_parser("compare", help="Ergebnisdateien vergleichen")
    c.add_argument("files", nargs="+")
    c.add_argument("--out", default="vergleich.md")
    a = ap.parse_args()
    if getattr(a, "insecure", False):
        import ssl
        global SSL_CTX
        SSL_CTX = ssl._create_unverified_context()
        print("WARNUNG: --insecure, HTTPS-Zertifikat wird nicht geprueft.")
    if a.cmd == "models":
        key = a.key or os.environ.get("QT_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("STRATA_API_KEY", "")
        req = urllib.request.Request(api(a.url, "/v1/models"),
                                     headers={"Authorization": f"Bearer {key}"} if key else {})
        with open_url(req, 30) as r:
            for mdl in json.load(r).get("data", []):
                print(mdl.get("id"), "  max_model_len=" + str(mdl.get("max_model_len")) if mdl.get("max_model_len") else "")
        return
    cmd_run(a) if a.cmd == "run" else cmd_compare(a)


if __name__ == "__main__":
    main()
