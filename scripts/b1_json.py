"""B1 — Exercice 3 : JSON + Pydantic sur la tâche d'extraction (t5), 20 runs par condition.

Conditions (10 runs gpt-4o-mini + 10 runs claude-haiku-4-5, température 0.7) :
  v1          : gabarit extraire-json v1 seul (consigne « pas de bloc de code »)
  v1+prefill  : même gabarit ; pour Anthropic, le tour assistant est pré-rempli par « { »
                (la sortie validée = « { » + texte). gpt-4o-mini inchangé.
Validité = `RapportProjets.model_validate_json(sortie)` sans aucun nettoyage (« strict »).
On rapporte aussi « tolérant » (bloc ```json retiré) et l'exactitude des champs vs vérité terrain.
"""

from __future__ import annotations

import csv
import itertools

import forge.clients as clients
from b1_common import RESULTS, build_prompt, pmap, validate_extraction, write_jsonl

MODELS = ["gpt-4o-mini", "anthropic/claude-haiku-4-5"]
CONDITIONS = ["v1", "v1+prefill"]
N_PER_MODEL = 10


def run_one(job):
    cond, model, rep = job
    prompt = build_prompt("t5_extraire", "b")
    msgs = [{"role": "user", "content": prompt}]
    prefill = cond == "v1+prefill" and model.startswith("anthropic/")
    if prefill:
        msgs.append({"role": "assistant", "content": "{"})
    err = None
    try:
        r = clients.complete(model, msgs, max_tokens=1600, temperature=0.7)
        text = r["text"]
    except Exception as e:  # noqa: BLE001
        text, err = "", f"{type(e).__name__}: {e}"
    if prefill and not text.lstrip().startswith("{"):
        text = "{" + text
    v = validate_extraction(text)
    print(f"{cond:11s} {model:28s} rep{rep} strict={v['strict_valid']} acc={v['field_acc']}", flush=True)
    return dict(exp="json", condition=cond, model=model, rep=rep, prefill=prefill, gen_error=err,
                strict_valid=v["strict_valid"], tolerant_valid=v["tolerant_valid"], field_acc=v["field_acc"],
                n_projets=v.get("n_projets"), validation_error=v["error"], output=text)


def main() -> None:
    jobs = list(itertools.product(CONDITIONS, MODELS, range(N_PER_MODEL)))
    rows = pmap(run_one, jobs, workers=8)
    write_jsonl(RESULTS / "json_runs.jsonl", rows)
    keys = ["condition", "model", "rep", "prefill", "strict_valid", "tolerant_valid", "field_acc", "n_projets",
            "validation_error", "gen_error"]
    with (RESULTS / "json_scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    for cond in CONDITIONS:
        sub = [r for r in rows if r["condition"] == cond]
        ok = sum(r["strict_valid"] for r in sub)
        print(f"{cond}: JSON strict valide {ok}/{len(sub)} = {ok / len(sub):.0%} ; "
              f"tolérant {sum(r['tolerant_valid'] for r in sub)}/{len(sub)}")


if __name__ == "__main__":
    main()
