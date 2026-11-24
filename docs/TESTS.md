# Testbeschreibung

Stand 24.11.2026. Zwei Testrunden, beide über dieselbe API und dasselbe Skript:

| Runde | Aufruf | Inhalt | Bewertung |
| --- | --- | --- | --- |
| Standard | `--suite standard` (Standard) | 12 Programmieraufgaben + 4 Fachfragen | Code automatisch, Fachfragen von Hand |
| Schwer | `--suite schwer` | 8 Programmieraufgaben + 4 Rechenfragen | Code automatisch, Rechenfragen mit Kennzahlen-Autocheck |
| Alle | `--suite alle` | beides | wie oben |

Die schwere Runde entstand am 21.11.2026, weil mehrere Modelle in der Standardrunde 12/12 erreichten und sich nicht
mehr unterschieden.

## Ablauf eines Laufs

1. Jede Aufgabe ist eine eigene Anfrage an `/v1/chat/completions` mit festem System-Prompt:
   - Programmieraufgaben: „Du bist ein sorgfältiger Python-Entwickler. Liefere die vollständige Implementierung in genau
     einem ```python Codeblock, ohne Beispielaufrufe, ohne Tests und ohne input().“
   - Fachfragen: „Du bist Experte für Feuchtemesstechnik und Metrologie. Antworte auf Deutsch, präzise, mit Rechenweg.“
2. `max_tokens` (Standard 12 000, schwere Runde 24 000) gilt **inklusive** Denkteil.
   Mit `--effort` wird zusätzlich `chat_template_kwargs: {"reasoning_effort": …}` mitgeschickt.
3. Aus der Antwort wird der längste ```python-Block genommen. Ist die sichtbare Antwort leer, steht aber ein
   vollständiger Codeblock im Denkteil und endete die Antwort regulär, wird dieser verwendet (Vermerk „Code aus
   Thinking-Teil“).
4. Code + Unit-Tests werden in eine temporäre Datei geschrieben und mit demselben Python-Interpreter als Unterprozess
   ausgeführt (Zeitlimit 60 s je Aufgabe). Exit-Code 0 = bestanden, sonst steht die letzte Fehlerzeile im Ergebnis.
5. Fehlergründe ohne Testlauf:
   - `Token-Limit im Thinking`: Antwort leer, `finish_reason = length` – das Modell hat das Budget im Denkteil verbraucht.
   - `leere Antwort (finish_reason=stop)`: Modell beendete ohne Code.
   - `verbotenes Modul/Konstrukt: …`: verbotener Import oder Aufruf (siehe Sperren), nur mit Standard `--forbid`.
6. Ergebnis: `ergebnis_<label>.json` mit Code, Fehlergrund, Zeit, Tokens, `finish_reason`, den letzten 3 000 Zeichen
   des Denkteils bei Fehlschlägen und allen Fachantworten.

## Standardrunde – 12 Programmieraufgaben

| ID | Funktion | Geprüft wird |
| --- | --- | --- |
| `taupunkt_magnus` | `dew_point(t_c, rh)` | Magnus über Wasser (a = 17,62, b = 243,12 °C), Grenzfälle und ValueError |
| `dauer_parsen` | `parse_duration(s)` | „1h30m15s“, „1d2h“ in Sekunden; ungültige Formate → ValueError |
| `roemisch` | `int_to_roman`, `roman_to_int` | 1…3999, Subtraktionsschreibweise, ungültige Strings („IIII“, „VX“, „IC“) |
| `intervalle` | `merge_intervals(iv)` | Zusammenfassen überlappender/berührender Intervalle, start > end → ValueError |
| `lru_cache` | `LRUCache(capacity)` | Verdrängung, get/put als Benutzung, capacity ≤ 0 → ValueError |
| `topo_sort` | `topo_sort(deps)` | Abhängigkeiten, Knoten nur als Abhängigkeit, Zyklus → ValueError |
| `rechner` | `evaluate(expr)` | + − × ÷, Klammern, unäres Minus, **ohne eval/exec/ast/compile** |
| `crc16` | `crc16_ccitt(data)` | CRC-16/CCITT-FALSE ohne crcmod/binascii |
| `regression` | `linfit(x, y)` | Steigung, Achsenabschnitt, R² ohne numpy; Fehlerfälle |
| `gleitender_median` | `sliding_median(values, k)` | Median je Fenster, gerades k, ungültiges k |
| `ringpuffer_mittel` | `RunningStats` | Welford, Stichprobenvarianz, numerische Stabilität |
| `relative_feuchte_mischung` | `rh_after_mixing(…)` | adiabate Mischung zweier feuchter Luftströme (Temperatur, rF) |

## Standardrunde – 4 Fachfragen (von Hand bewertet)

| ID | Thema | Worauf es ankommt |
| --- | --- | --- |
| `zweidruck` | Zweidruck-Generator: Sättigung bei 3,00 bar / 20 °C, Entspannung auf 1,00 bar | ohne f: 33,33 %rF; mit Enhancement-Faktoren f(3 bar)/f(1 bar) ≈ 1,0063–1,0069 → **≈ 33,55 %rF** (WMO 33,54, Buck 33,56). 33,38 % ist falsch. |
| `taupunktspiegel` | Fehlerquellen unter 0 °C | Tau/Reif-Verwechslung, Raoult-Effekt (Kontamination, Taupunkt zu hoch), Kelvin-Effekt (kleine Tröpfchen), unterkühltes Wasser |
| `unsicherheit` | rF aus Td (u = 0,10 K) und T (u = 0,05 K) bei 25 °C / 13,9 °C | Sensitivitätskoeffizienten aus Magnus, kombinierte und erweiterte Unsicherheit (k = 2) |
| `kapazitiv` | Polymersensor: Drift +2 %rF, Hysterese 1,5 %rF bei 95 %rF | physikalische Ursachen (Quellung, Kontamination), Kalibrier- und Kompensationskonzept |

## Schwere Runde – 8 Programmieraufgaben (`aufgaben_schwer.py`)

Jede Aufgabe wurde vorab mit einer eigenen Referenzlösung programmiert; alle 8 Referenzen bestehen die Tests.

| ID | Funktion | Geprüft wird | Gesperrt |
| --- | --- | --- | --- |
| `frostpunkt_iterativ` | `dew_or_frost_point(x_gkg, p_pa)` | Taupunkt bzw. Frostpunkt aus Wasserbeladung mit Enhancement-Faktor f(p,t) = 1,00062 + 3,14e-8·p + 5,6e-7·t²; Iteration, Wechsel Wasser/Eis, 8 Fälle auf 1e-5 K gegen Bisektion | – |
| `ausdruck_parser` | `evaluate_expr(s, variables)` | Potenz rechtsassoziativ, −2^2 = −4, 2^−1 = 0,5, Funktionen sin/cos/sqrt/exp/ln, Variablen, 13 Fehlerfälle | eval/exec/compile, ast |
| `regex_nfa` | `rx_fullmatch(pattern, text)` | `.`, `* + ?`, Gruppen, Alternation, Klassen inkl. Negation und Escape; 15 Muster × 300 Zufallsstrings gegen `re.fullmatch`; **Laufzeit**: `(a\|aa)*b` gegen 40 × „a“ in < 5 s | `re`, `regex`, `fnmatch` |
| `k_kuerzeste_pfade` | `k_shortest_paths(graph, src, dst, k)` | k kürzeste schleifenfreie Pfade (Yen) gegen Brute-Force auf Zufallsgraphen | – |
| `exp_fit_lm` | `fit_exp_decay(t, y)` | A·exp(−t/τ) + C per nichtlinearer Kleinste-Quadrate-Anpassung, Startwerte selbst schätzen, 5 Parametersätze auf 1e-4 relativ, ein verrauschter Sensor-Sprung | numpy, scipy |
| `diff_myers` | `edit_script(a, b)` | minimales Edit-Skript (Anzahl −/+ = len(a) + len(b) − 2·LCS), **20 000 Zeilen in < 5 s** | – |
| `polynom_nullstellen` | `poly_roots(coeffs)` | alle komplexen Nullstellen; einfache auf 1e-8, mehrfache auf 1e-4, führende Nullen, Wurzeln 1…10 | numpy, scipy, sympy, mpmath |
| `crc_generisch` | `crc_generic(data, width, poly, init, refin, refout, xorout)` | Rocksoft-Modell, 15 Katalogwerte von CRC-3 bis CRC-64 („123456789“) | crcmod, binascii, zlib |

Sperren gelten nur im Code des Modells (Regex auf Imports bzw. Aufrufe); die Tests selbst dürfen z. B. `re` zum
Vergleich nutzen. Mit `--allow-eval` werden alle Sperren abgeschaltet.

## Schwere Runde – 4 Rechenfragen mit Kennzahlen-Autocheck

Das Skript sucht jede Kennzahl als Zahl in der Antwort und wertet sie als gefunden, wenn sie innerhalb der Toleranz
liegt. Deutsches Komma, LaTeX-Schreibweisen (`7{,}87`, `\approx`, `\boxed`), schmale Leerzeichen und Minuszeichen
werden normalisiert. Den Rechenweg prüft das nicht – die Antworten stehen vollständig im Vergleichsbericht.

| ID | Aufgabe | Kennzahl | Sollwert | Toleranz |
| --- | --- | --- | --- | --- |
| `frostpunkt_rf` | Frostpunkt −20,0 °C, T = −5,0 °C, 1013,25 hPa, Magnus nach WMO (Wasser/Eis) | Dampfdruck e | 1,033 hPa | ± 0,01 |
| | | Taupunkt über unterkühltem Wasser | −22,29 °C | ± 0,15 |
| | | rF bezogen auf Wasser (WMO) | 24,46 % | ± 0,3 |
| | | rF bezogen auf Eis | 25,70 % | ± 0,3 |
| `zweitemp_zweidruck` | Sättiger 5,000 bar / 10,00 °C, Prüfraum 1,000 bar / 25,00 °C, f(p) = 1,0007 + 3,46e-6·p (Buck) | rF mit f | 7,87 % | ± 0,05 |
| | | Fehler ohne f | 0,107 %rF | ± 0,02 |
| | | Taupunkt im Prüfraum | −11,8 °C | ± 0,15 |
| `kalibriergerade` | 5 Punkte Referenz → Anzeige (10/30/50/70/90 %rF), lineare Regression | Achsenabschnitt a | 1,615 | ± 0,01 |
| | | Steigung b | 0,9725 | ± 0,001 |
| | | Reststandardabweichung s | 0,149 %rF | ± 0,005 |
| | | korrigierter Wert bei Anzeige 60,0 | 60,04 %rF | ± 0,03 |
| | | Unsicherheit der Geraden an dieser Stelle (k = 1) | 0,073 %rF | ± 0,006 |
| `psychrometer` | Assmann: 25,0 / 18,0 °C, 1013,25 hPa, A = 6,62e-4 1/K | Dampfdruck e | 15,90 hPa | ± 0,05 |
| | | rF | 50,3 % | ± 0,2 |
| | | Taupunkt | 13,94 °C | ± 0,1 |
| | | rF-Änderung bei 0,1 K Fehler der Feuchttemperatur | 0,62 %rF | ± 0,06 |

Alle Sollwerte wurden mit den in der Aufgabe genannten Formeln nachgerechnet.

## Vergleichsbericht

`compare` liest beliebig viele Ergebnisdateien **derselben Runde**, bewertet die Kennzahlen mit der aktuellen
Prüfroutine neu und schreibt einen Markdown-Bericht: Übersicht, Matrix bestanden/fehlgeschlagen je Aufgabe, danach alle
Fachantworten nebeneinander mit Kennzahlen-Häkchen.

## Grenzen

- Ein Lauf je Konfiguration; Unterschiede von 1–2 Aufgaben können Zufall sein (Sampling mit temp ≈ 1).
- Nur in sich geschlossene Aufgaben ohne Werkzeuge; agentisches Arbeiten, Langkontext und Bildeingabe sind nicht
  abgedeckt.
- Der Kennzahlen-Check findet Zahlen, prüft aber nicht, ob sie am richtigen Platz stehen; ein Treffer im Rechenweg zählt.
- Zeitmessung schließt das Laden des Modells beim ersten Aufruf mit ein, wenn der Server es erst laden muss.
- Der generierte Code läuft ohne Sandbox auf dem Testrechner.

## Änderungshistorie

| Datum | Änderung |
| --- | --- |
| 13.11.2026 | Standardrunde, 12 + 4 |
| 21.11.2026 | Schwere Runde, `--suite`, Sperren je Aufgabe, Kennzahlen-Autocheck |
| 21.11.2026 | `--effort` (reasoning_effort ans Chat-Template) |
| 21.11.2026 | Korrektur: LaTeX-Zahlen (`7{,}87`) wurden nicht erkannt; `compare` bewertet neu |
| 21.11.2026 | Korrektur: Sperre traf `re.compile`; jetzt nur echte `eval`/`exec`/`compile`-Aufrufe |
| 21.11.2026 | Korrektur: Sperre „fnmatch“ traf Wörter im Docstring; jetzt nur Imports |
| 22.11.2026 | `models`, `--timeout` (3600 s), HTTPS, URL mit/ohne `/v1`, Open-WebUI-Pfade (`/api`), `--insecure`, verständliche Meldungen bei 401/403 |
