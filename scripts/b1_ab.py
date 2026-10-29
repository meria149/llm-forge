"""B1 — Exercice 1 : A/B brut (a) vs 6Q (b) vs brut + contexte (c), 5 tâches × 2 modèles × N répétitions.

Usage : python scripts/b1_ab.py [--reps 2]
Sorties : notebooks/b1_results/ab_runs.jsonl (prompts, sorties, notes des juges) + ab_scores.csv
"""

from __future__ import annotations

import argparse
import csv
import itertools
import time

from b1_common import MODELS, RESULTS, TASKS, build_prompt, call, judge_both, pmap, validate_extraction, write_jsonl


def run_one(job):
    task_id, variant, model, rep = job
    prompt = build_prompt(task_id, variant)
    r = call(model, prompt)
    text = r.get("text", "")
    row = dict(exp="ab", task=task_id, variant=variant, model=model, rep=rep,
               prompt_chars=len(prompt), in_tokens=r.get("in_tokens"), out_tokens=r.get("out_tokens"),
               latency=r.get("latency"), gen_error=r.get("error"), words=len(text.split()),
               prompt=prompt, output=text)
    row.update(judge_both(task_id, text))
    if task_id == "t5_extraire":
        v = validate_extraction(text)
        row.update(json_strict=v["strict_valid"], json_tolerant=v["tolerant_valid"], field_acc=v["field_acc"])
    print(f"{task_id:12s} {variant} {model:28s} rep{rep} score={row['score']}", flush=True)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    args = ap.parse_args()
    jobs = list(itertools.product(TASKS, "abc", MODELS, range(args.reps)))
    t0 = time.time()
    rows = pmap(run_one, jobs, workers=8)
    write_jsonl(RESULTS / "ab_runs.jsonl", rows)
    keys = ["task", "variant", "model", "rep", "score", "clarte", "completude", "format", "utilite",
            "score_gemini-3.5-flash-lite", "score_grok-3-mini", "words", "in_tokens", "out_tokens",
            "latency", "json_strict", "json_tolerant", "field_acc", "gen_error"]
    with (RESULTS / "ab_scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} lignes en {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
