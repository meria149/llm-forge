"""B1 — Exercice 2 : ablation du prompt 6Q, un élément retiré à la fois.

Tâches : t1_resume (marge de progression au juge + contraintes mesurables : ≤ 200 mots, copie de l'exemple)
et t5_extraire (métriques objectives : JSON strict, exactitude des champs). t3/t4 saturent à 5/5 au juge.
Usage : python scripts/b1_ablation.py [--reps 4]
"""

from __future__ import annotations

import argparse
import csv
import difflib
import itertools
import re

from b1_common import MODELS, RESULTS, build_prompt, call, judge_both, pmap, validate_extraction, write_jsonl

ELEMENTS = ["(complet)", "Rôle", "Contraintes", "Exemple", "Format", "Critère de réussite"]
ABL_TASKS = ["t1_resume", "t5_extraire"]
EXEMPLE_T1 = ("Prototype justifié seulement si nos contextes dépassent 16k jetons ; "
              "attendre le noyau CUDA avant de mesurer la latence.")


def copie_exemple(text: str) -> float:
    """Similarité max entre l'exemple de verdict et une ligne de la sortie (0–1)."""
    lines = [re.sub(r"[*_#>]", "", ln) for ln in text.splitlines() if ln.strip()]
    return max((difflib.SequenceMatcher(None, EXEMPLE_T1.lower(), ln.lower()).ratio() for ln in lines), default=0.0)


def run_one(job):
    task_id, element, model, rep = job
    drop = () if element == "(complet)" else (element,)
    prompt = build_prompt(task_id, "b", drop=drop)
    r = call(model, prompt)
    text = r.get("text", "")
    row = dict(exp="ablation", task=task_id, retire=element, model=model, rep=rep, prompt_chars=len(prompt),
               out_tokens=r.get("out_tokens"), gen_error=r.get("error"), words=len(text.split()),
               prompt=prompt, output=text)
    row.update(judge_both(task_id, text))
    if task_id == "t1_resume":
        row["respect_200_mots"] = len(text.split()) <= 200
        row["copie_exemple"] = round(copie_exemple(text), 3)
    else:
        v = validate_extraction(text)
        row.update(json_strict=v["strict_valid"], json_tolerant=v["tolerant_valid"], field_acc=v["field_acc"])
    print(f"{task_id:12s} -{element:22s} {model:28s} rep{rep} score={row['score']}", flush=True)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=4)
    args = ap.parse_args()
    jobs = list(itertools.product(ABL_TASKS, ELEMENTS, MODELS, range(args.reps)))
    rows = pmap(run_one, jobs, workers=8)
    write_jsonl(RESULTS / "ablation_runs.jsonl", rows)
    keys = ["task", "retire", "model", "rep", "score", "clarte", "completude", "format", "utilite", "words",
            "respect_200_mots", "copie_exemple", "json_strict", "json_tolerant", "field_acc", "prompt_chars", "gen_error"]
    with (RESULTS / "ablation_scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "lignes")


if __name__ == "__main__":
    main()
