#!/usr/bin/env python3
"""Einheitliche Tempo-Messung fuer alle Profile eines OpenAI-kompatiblen Servers (llama-swap, vLLM, Strata).

Gleiche Prompts, gleiche Laenge, gleiche Wiederholungen fuer jedes Modell:
  - "code":  Python-Aufgabe (Entwurfskoepfe wie MTP/DSpark treffen hier besser)
  - "prosa": deutscher Erklaertext
Je Modell: 1 Aufwaermlauf (laedt das Modell, wird verworfen), dann --wdh Laeufe je Prompt.
Gemessen: Ausgabe-Tokens/s (llama.cpp-Timings, sonst Tokens / (Gesamtzeit - Prompt-Zeit)),
Prompt-Verarbeitung tok/s, Trefferquote des Entwurfsmodells. Ergebnis: Median je Modell und Prompt.

  python tempo_messung.py --url http://127.0.0.1:8080 \
      --modelle gemma-4-26b-a4b-mtp gemma-4-26b-a4b qwen3.8-27b inkling-2-mini-unsloth
  -> tempo_<datum>.csv und tempo_<datum>.md

Nur Standardbibliothek. API-Schluessel (falls noetig) ueber QT_API_KEY / OPENAI_API_KEY.
"""
import argparse
import csv
import json
import os
import statistics
import time
import urllib.request

PROMPTS = {
    "code": ("Schreibe eine Python-Klasse RingBuffer mit fester Kapazitaet, Methoden push, pop, peek, __len__, "
             "__iter__ und einer Methode mean() fuer numerische Werte. Mit Docstrings und Typ-Hinweisen."),
    "prosa": ("Erklaere ausfuehrlich und in ganzen Saetzen, wie ein Taupunktspiegel-Hygrometer funktioniert, "
              "welche Fehlerquellen es gibt und wie man es kalibriert."),
}
DEFAULT_MODELLE = [
    "gemma-4-26b-a4b-mtp", "gemma-4-26b-a4b", "gemma-4-26b-a4b-nothink",
    "qwen3.8-27b", "qwen3.8-27b-heretic", "qwen3.8-flash-next-gyro-gyro-s",
    "inkling-2-mini-unsloth", "inkling-2-mini-mainline",
]


def anfrage(url, key, model, prompt, max_tokens, timeout):
    body = json.dumps({"model": model, "max_tokens": max_tokens, "temperature": 0.7, "seed": 42,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    hdr = {"Content-Type": "application/json"}
    if key:
        hdr["Authorization"] = f"Bearer {key}"
    u = url.rstrip("/")
    u = u[:-3] if u.endswith("/v1") else u
    req = urllib.request.Request(u + "/v1/chat/completions", data=body, headers=hdr)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    dt = time.time() - t0
    usage, tim = j.get("usage") or {}, j.get("timings") or {}
    n = tim.get("predicted_n") or usage.get("completion_tokens") or 0
    if tim.get("predicted_per_second"):
        tps = tim["predicted_per_second"]
    else:   # Server ohne Timings (z.B. Strata, vLLM): Prompt-Zeit grob abziehen, falls bekannt
        tps = n / max(dt - (tim.get("prompt_ms") or 0) / 1000, 0.05)   # inkl. Prompt-Zeit: eher zu niedrig
    draft = (tim.get("draft_n_accepted") / tim["draft_n"]) if tim.get("draft_n") else None
    return {"tps": tps, "n": n, "pp": tim.get("prompt_per_second"), "draft": draft, "s": dt,
            "quelle": "timings" if tim.get("predicted_per_second") else "gesamtzeit"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--modelle", nargs="+", default=DEFAULT_MODELLE)
    ap.add_argument("--wdh", type=int, default=3, help="Wiederholungen je Prompt (Standard 3)")
    ap.add_argument("--max-tokens", type=int, default=1500, help="inkl. Denkteil (Standard 1500)")
    ap.add_argument("--timeout", type=int, default=1200, help="Sekunden je Anfrage (Laden von Strata dauert)")
    a = ap.parse_args()
    key = os.environ.get("QT_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    stamp = time.strftime("%Y%m%d-%H%M")
    zeilen = []
    for m in a.modelle:
        print(f"== {m}")
        try:
            anfrage(a.url, key, m, "Sag Hallo.", 64, a.timeout)          # Aufwaermen / Laden
        except Exception as e:
            print(f"   uebersprungen: {e}")
            continue
        for pname, p in PROMPTS.items():
            werte = []
            for i in range(a.wdh):
                try:
                    r = anfrage(a.url, key, m, p, a.max_tokens, a.timeout)
                    werte.append(r)
                    d = f", Entwurf {r['draft']:.0%}" if r["draft"] is not None else ""
                    print(f"   {pname} {i + 1}/{a.wdh}: {r['tps']:.1f} tok/s ({r['n']} Tok{d})")
                except Exception as e:
                    print(f"   {pname} {i + 1}/{a.wdh}: Fehler {e}")
            if werte:
                med = lambda k: statistics.median([w[k] for w in werte if w[k] is not None]) if any(
                    w[k] is not None for w in werte) else None
                zeilen.append({"modell": m, "prompt": pname, "tok_s": round(med("tps"), 1),
                               "tok_s_min": round(min(w["tps"] for w in werte), 1),
                               "tok_s_max": round(max(w["tps"] for w in werte), 1),
                               "pp_tok_s": round(med("pp"), 0) if med("pp") else "",
                               "entwurf_quote": f"{med('draft'):.0%}" if med("draft") is not None else "",
                               "tokens": int(med("n")), "quelle": werte[0]["quelle"], "laeufe": len(werte)})
    if not zeilen:
        print("Keine Messwerte.")
        return
    with open(f"tempo_{stamp}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(zeilen[0]), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    with open(f"tempo_{stamp}.md", "w", encoding="utf-8") as f:
        f.write(f"# Tempo-Messung {stamp}\n\nPrompts: code / prosa, max_tokens {a.max_tokens}, "
                f"{a.wdh} Wiederholungen, Median (min–max).\n\n")
        f.write("| Modell | Prompt | tok/s | Spanne | Prompt tok/s | Entwurf | Tokens | Quelle |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for z in zeilen:
            f.write(f"| {z['modell']} | {z['prompt']} | {z['tok_s']} | {z['tok_s_min']}–{z['tok_s_max']} | "
                    f"{z['pp_tok_s']} | {z['entwurf_quote']} | {z['tokens']} | {z['quelle']} |\n")
    print(f"\n-> tempo_{stamp}.csv, tempo_{stamp}.md")


if __name__ == "__main__":
    main()
