# Ergebnisse (RTX 4090, 13.–24.11.2026)

Testrechner: RTX 4090 24 GB (+135 MHz Core / +1000 MHz Speicher), llama-swap v271, llama.cpp b12345 (CUDA 13.5);
Gyro-S über Strata 0.1.59; Inkling 2 Mini über den Unsloth-Build b12651-mix-c7059d6.
Effort = `reasoning_effort` im Chat-Template (Qwen3.8/Gyro-S: low, medium, xhigh = Standard; Inkling: 0,0–0,99,
Standard high = 0,9).

## Schwere Runde (8 Aufgaben + 16 Kennzahlen, max. 24 000 Tokens)

| Lauf | Modell / Einstellung | Aufgaben | Kennzahlen | Zeit | Tokens |
| --- | --- | --- | --- | --- | --- |
| gemma-mtp-S | Gemma 4 26B-A4B QAT UD-Q4_K_XL + MTP | 6/8 | 13/16 | 7,4 min | 135 k |
| gyro-medium-S | Gyro-S, Effort medium | 6/8 | 10/16 | 10,6 min | 111 k |
| q27-low-S | Qwen3.8-27B Dynamic 3.1, Effort low + 12k-Budget | 6/8 | 13/16 | 15,4 min | 112 k |
| inkling-unsloth-low-S | Inkling 2 Mini UD-Q4_K_XL + DSpark, Effort low | 5/8 | 13/16 | 8,5 min | 56 k |
| q27-medium-S | Qwen3.8-27B, Effort medium + 12k-Budget | 5/8 | 13/16 | 16,6 min | 110 k |
| gyro-S | Gyro-S, Effort xhigh | 4/8 | 16/16 | 28,4 min | 237 k |
| gyro-low-S | Gyro-S, Effort low | 4/8 | 8/16 | 9,8 min | 106 k |
| q27-budget-S | Qwen3.8-27B, Effort xhigh + 12k-Budget | 4/8 | 10/16 | 30,4 min | 172 k |
| inkling-S | Inkling 2 Mini, Effort high, Unsloth-Build b12588 | 3/8 | 15/16 | 46,7 min | 220 k |
| inkling-medium-S | Inkling 2 Mini, Effort medium, b12588 | 3/8 | 13/16 | 32,7 min | 153 k |
| inkling-unsloth-S | Inkling 2 Mini, Effort high, b12651 | 3/8 | 10/16 | 33,2 min | 215 k |
| inkling-unsloth-medium-S | Inkling 2 Mini, Effort medium, b12651 | 3/8 | 10/16 | 21,5 min | 144 k |
| q27-S | Qwen3.8-27B, Effort xhigh (Template-Standard) | 0/8 | 9/16 | ca. 37 min* | 280 k |

\* Laufzeit im JSON 522 min, davon 7,9 h Standby des Rechners.

Kernaussagen:

- Die Effort-Stufe entscheidet mehr als das Modell: Qwen3.8-27B 0/8 → 6/8, Inkling 3/8 → 5/8 jeweils von Standard auf low.
- Die Zwei-Temperatur-Zwei-Druck-Aufgabe lösen nur Gyro-S xhigh und medium vollständig (3/3); alle Qwen-Varianten und
  Gemma rechnen sie falsch (Gemma ohne Entspannung 5 → 1 bar: 39,3 statt 7,87 %rF).
- Der generische CRC scheitert bei 7 von 10 Läufen vom 21.11.; typische Falle ist das gespiegelte Einlesen der Bytes.

## Standardrunde (12 Aufgaben + 4 Fachfragen)

| Lauf | Modell / Einstellung | Aufgaben | Fachfragen (Hand) | Zeit | Tokens |
| --- | --- | --- | --- | --- | --- |
| gemma4-26b | Gemma 4 26B-A4B, ohne MTP | 12/12 | 4/4 | 5,4 min | 57 k |
| strata-gyro-s | Gyro-S | 12/12 | 4/4 | 18,4 min | 158 k |
| q27-t10 | Qwen3.8-27B Dynamic 3.1, temp 1.0 | 11/12 | 2/4 | 37,6 min | 210 k |
| heretic | Qwen3.8-27B Heretic-ARA i1-Q4_K_M | 10/12 | 2/4 | 37,0 min | 212 k |
| q27-v31 | Qwen3.8-27B Dynamic 3.1, temp 0.6 | 10/12 | – | 25,8 min | 154 k |
| q27-v30 | Qwen3.8-27B Dynamic 3.0, temp 0.6 | 9/12 | – | 27,9 min | 165 k |
| qwen27b | Qwen3.8-27B, erster Lauf | 8/12 | – | 19,9 min | 115 k |

## Ausgabe-Tempo

| Profil | tok/s | Messung |
| --- | --- | --- |
| Gemma 4 26B + MTP | 334 | Kurztest Code, 69 % der MTP-Entwürfe übernommen |
| Gemma 4 26B ohne Thinking + MTP | 248 | Kurztext Prosa, 40 % übernommen |
| Gemma 4 26B | 175–187 | Kurztest und Standardrunde |
| Gyro-S (Strata) | ca. 138 | Standardrunde |
| Qwen3.8-27B + MTP | 90–130 | Standard- und schwere Runde, 72–87 % übernommen |
| Inkling 2 Mini + DSpark (Unsloth b12651) | 109 | Kurztest, 50 % übernommen |
| Qwen3.8-27B Heretic + MTP | 94 | Standardrunde |
| Inkling 2 Mini, offizielles llama.cpp b12651 | 58 | Kurztest, ohne DSpark |

Die Tempowerte stammen aus unterschiedlichen Prompts und sind nur grob vergleichbar.

## Rohdaten

`results/ergebnis_<lauf>.json` je Lauf. Noch nachzutragen (liegen auf dem Testrechner): `q27-medium-S`, `q27-low-S`,
`inkling-*`, `qwen27b`, `q27-v30`, `q27-v31`.


## Einheitliche Tempo-Messung (24.11.2026)

Gleiche Prompts fuer alle Profile (tempo_messung.py), Median aus 3 Laeufen, Ausgabe-tok/s aus den llama.cpp-Timings.

| Profil | Code tok/s (Median, min–max) | Prosa tok/s (Median, min–max) | Mittel | Draft-Quote Code/Prosa |
|---|---|---|---|---|
| gemma-4-26b-a4b-mtp | 316 (308–334) | 263 (260–266) | 289 | 63 % / 48 % |
| gemma-4-26b-a4b | 189 (187–189) | 189 (189–189) | 189 | – / – |
| gemma-4-26b-a4b-nothink | 321 (321–322) | 262 (260–264) | 292 | 62 % / 43 % |
| qwen3.8-27b | 122 (121–122) | 100 (98–100) | 111 | 75 % / 55 % |
| qwen3.8-27b-heretic | 95 (94–95) | 83 (83–83) | 89 | 48 % / 38 % |
| qwen3.8-flash-next-gyro-gyro-s | 140 (112–159) | 130 (110–138) | 135 | 72 % / 52 % |
| inkling-2-mini-unsloth | 111 (111–112) | 64 (64–64) | 88 | 48 % / 10 % |
| inkling-2-mini-mainline | 70 (70–70) | 70 (70–70) | 70 | – / – |

Auffaellig: Inkling mit DSpark ist bei Prosa langsamer als ohne (64 statt 70 tok/s, 10 % Entwurfsquote). Rohdaten: results/tempo_2026-11-24.json
