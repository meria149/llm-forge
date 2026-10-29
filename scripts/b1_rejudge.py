"""B1 — Complète les notes du juge Gemini manquantes (quota 429 pendant les runs parallèles).

Ré-évalue séquentiellement (avec pause) les lignes sans `score_gemini-3.5-flash-lite`,
recalcule la moyenne des deux juges, puis réécrit les .jsonl et .csv.
"""

from __future__ import annotations

import csv
import json
import time

from b1_common import CRITERIA, JUDGE_TMPL, RESULTS, _first_json_obj, call, judge, write_jsonl

GJ = "gemini/gemini-3.5-flash-lite"
G = "gemini-3.5-flash-lite"
X = "grok-3-mini"

CSV_KEYS = {
    "ab": ["task", "variant", "model", "rep", "score", "clarte", "completude", "format", "utilite",
           f"score_{G}", f"score_{X}", "words", "in_tokens", "out_tokens", "latency", "json_strict",
           "json_tolerant", "field_acc", "gen_error"],
    "ablation": ["task", "retire", "model", "rep", "score", "clarte", "completude", "format", "utilite",
                 f"score_{G}", f"score_{X}", "words", "respect_200_mots", "copie_exemple", "json_strict",
                 "json_tolerant", "field_acc", "prompt_chars", "gen_error"],
    "library": ["template", "model", "rep", "score", f"score_{G}", f"score_{X}", "words", "json_valid",
                "injection_reprise"],
}


def gemini_library(tid: str, answer: str) -> dict:
    from b1_library_smoke import CASES
    prompt = JUDGE_TMPL.format(label=tid, context=CASES[tid]["besoin"], artefact="(voir besoin réel)", answer=answer)
    d = _first_json_obj(call(GJ, prompt, max_tokens=400, temperature=0).get("text", ""))
    if d and all(isinstance(d.get(c), (int, float)) for c in CRITERIA):
        d["score"] = sum(d[c] for c in CRITERIA) / 4
        return d
    return {}


def main() -> None:
    for name in ["ab", "ablation", "library"]:
        path = RESULTS / f"{name}_runs.jsonl"
        rows = [json.loads(line) for line in path.open(encoding="utf-8")]
        n = 0
        for r in rows:
            if r.get(f"score_{G}") is not None:
                continue
            d = gemini_library(r["template"], r["output"]) if name == "library" else judge(r["task"], r["output"], GJ)
            if d.get("score") is None:
                print("échec", name, r.get("task") or r.get("template"))
                continue
            r[f"score_{G}"] = d["score"]
            r[f"justif_{G}"] = d.get("justification")
            for c in CRITERIA:
                if name != "library":
                    r[f"{c}_{G}"] = d.get(c)
                    vals = [v for v in (r.get(f"{c}_{G}"), r.get(f"{c}_{X}")) if v is not None]
                    r[c] = sum(vals) / len(vals)
            vals = [v for v in (r.get(f"score_{G}"), r.get(f"score_{X}")) if v is not None]
            r["score"] = sum(vals) / len(vals)
            n += 1
            time.sleep(6)
        write_jsonl(path, rows)
        with (RESULTS / f"{name}_scores.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_KEYS[name], extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(name, "complétées :", n, "| manquantes restantes :", sum(r.get(f"score_{G}") is None for r in rows))


if __name__ == "__main__":
    main()
