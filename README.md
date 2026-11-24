# llmBench – Qualitäts- und Tempotest für lokale LLMs

Ein Python-Skript, das ein Sprachmodell über eine OpenAI-kompatible API (llama.cpp / llama-swap, vLLM, Strata,
Open WebUI) mit Programmieraufgaben und Fachfragen aus der Feuchtemesstechnik prüft. Der vom Modell geschriebene
Code wird lokal gegen Unit-Tests ausgeführt; Fachantworten werden auf erwartete Kennzahlen durchsucht.

Nur Python ≥ 3.9 und die Standardbibliothek – keine Installation, keine Adminrechte.

| Datei | Inhalt |
| --- | --- |
| `qualitaetstest.py` | Testlauf (`run`), Modellliste (`models`), Vergleichsbericht (`compare`) |
| `aufgaben_schwer.py` | Schwere Runde: 8 Programmieraufgaben + 4 Rechenfragen mit Sollwerten |
| `docs/TESTS.md` | Beschreibung aller Aufgaben, Bewertung, Grenzen, Änderungshistorie |
| `docs/ERGEBNISSE.md` | Ergebnisse auf RTX 4090 (13.–24.11.2026) |
| `results/` | Rohdaten je Lauf (`ergebnis_<label>.json`) inkl. generiertem Code und Antworten |

## Schnellstart

```bash
# Modell-IDs des Servers anzeigen (URL mit oder ohne /v1; hinter Open WebUI: .../api)
python3 qualitaetstest.py models --url http://127.0.0.1:8080

# Standardrunde: 12 Aufgaben + 4 Fachfragen (Fachfragen von Hand bewerten)
python3 qualitaetstest.py run --label meinmodell --model <id> --url http://127.0.0.1:8080

# Schwere Runde: 8 Aufgaben + 4 Rechenfragen mit Kennzahlen-Autocheck
python3 qualitaetstest.py run --suite schwer --label meinmodell-S --model <id> --max-tokens 24000

# Mit Effort-Stufe (wird als chat_template_kwargs.reasoning_effort geschickt)
python3 qualitaetstest.py run --suite schwer --label meinmodell-low-S --model <id> --effort low --max-tokens 24000

# Vergleichsbericht (Markdown mit allen Antworten)
python3 qualitaetstest.py compare results/ergebnis_a-S.json results/ergebnis_b-S.json --out vergleich.md
```

API-Schlüssel nie auf der Kommandozeile, sondern als Umgebungsvariable:

```bash
read -s QT_API_KEY && export QT_API_KEY                       # Linux/macOS
```
```powershell
$s = Read-Host "API-Key" -AsSecureString                      # Windows PowerShell
$env:QT_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$env:PYTHONUTF8 = "1"
```

Weitere Optionen: `--timeout` (Sekunden pro Anfrage, Standard 3600), `--insecure` (HTTPS-Zertifikat nicht prüfen,
nur Notlösung), `--allow-eval` (Sperre gegen `eval`/`exec` im Ausdrucksparser abschalten), `--suite alle`.

## Sicherheit

Der generierte Code läuft **ungeprüft** auf dem Rechner, der das Skript startet (Unterprozess mit Zeitlimit,
temporäres Verzeichnis, keine Sandbox). Nur mit Modellen und auf Rechnern verwenden, bei denen das vertretbar ist.

## Ergebnisse in Kürze (RTX 4090, schwere Runde)

| Konfiguration | Aufgaben | Kennzahlen | Zeit |
| --- | --- | --- | --- |
| Gemma 4 26B-A4B + MTP | 6/8 | 13/16 | 7,4 min |
| Qwen3.8-27B, Effort low | 6/8 | 13/16 | 15,4 min |
| Gyro-S (Strata), Effort medium | 6/8 | 10/16 | 10,6 min |
| Inkling 2 Mini, Effort low | 5/8 | 13/16 | 8,5 min |
| Gyro-S, Effort xhigh | 4/8 | 16/16 | 28,4 min |
| Qwen3.8-27B, Effort xhigh (Template-Standard) | 0/8 | 9/16 | ca. 37 min |

Details und alle Läufe: [docs/ERGEBNISSE.md](docs/ERGEBNISSE.md).
