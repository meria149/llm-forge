"""Génère notebooks/b1_ab.ipynb (analyse des résultats pré-calculés ; aucun appel API)."""

import pathlib

import nbformat as nbf

ROOT = pathlib.Path(__file__).resolve().parent.parent
nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = []

cells.append(md("""# B1 : Prompt craft I : intention, contexte, format

**Objectif du bloc :** écrire des prompts qui marchent du premier coup sur des tâches réelles, et savoir *pourquoi* ils marchent.

Ce notebook **relit les résultats pré-calculés** (`notebooks/b1_results/`). Les expériences ont été réellement exécutées via l'API
(`forge.clients.complete`, journal local dans `data/calls.jsonl`) par les scripts :

| Script | Expérience | Sortie |
|---|---|---|
| `scripts/b1_ab.py` | A/B (a) brut · (b) 6Q · (c) brut + contexte : 5 tâches × 2 modèles × 2 répétitions | `ab_runs.jsonl`, `ab_scores.csv` |
| `scripts/b1_ablation.py` | Ablation du prompt 6Q (un élément retiré à la fois) : 2 tâches × 6 variantes × 2 modèles × 4 rép. | `ablation_*.{jsonl,csv}` |
| `scripts/b1_json.py` | JSON + Pydantic, 20 runs par condition | `json_*.{jsonl,csv}` |
| `scripts/b1_library_smoke.py` | Test réel des 5 gabarits annexes | `library_*.{jsonl,csv}` |
| `scripts/b1_rejudge.py` | Complète les notes du juge Gemini perdues sur quota 429 | (réécrit les fichiers ci-dessus) |

**Modèles testés :** `gpt-4o-mini`, `anthropic/claude-haiku-4-5` (température 0,7, `max_tokens` 1600).
**Juges :** `gemini/gemini-3.5-flash-lite` et `xai/grok-3-mini` (température 0), d'autres familles que les modèles testés, pour limiter l'auto-préférence.
Grille courte (1–5) : clarté, complétude, respect du format, utilité ; le juge reçoit le **besoin réel** (contexte complet), même quand le prompt évalué ne le contenait pas.
Score = moyenne des 4 critères, puis moyenne des 2 juges.

Fixtures (fictives mais riches, commitées) : `forge/prompts/_fixtures/`. Pour tout relancer (~0,7 $) :
```bash
source .venv/bin/activate && cd scripts
python b1_ab.py && python b1_ablation.py && python b1_json.py && python b1_library_smoke.py && python b1_rejudge.py
```"""))

cells.append(code("""import pathlib, sys
import pandas as pd
pd.set_option("display.precision", 2)
ROOT = pathlib.Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
R = ROOT / "notebooks" / "b1_results"
ab = pd.read_csv(R / "ab_scores.csv")
abl = pd.read_csv(R / "ablation_scores.csv")
js = pd.read_csv(R / "json_scores.csv")
lib = pd.read_csv(R / "library_scores.csv")
G, X = "score_gemini-3.5-flash-lite", "score_grok-3-mini"
print(len(ab), "runs A/B ;", len(abl), "runs d'ablation ;", len(js), "runs JSON ;", len(lib), "runs bibliothèque")
print("Notes manquantes :", int(ab[[G, X]].isna().sum().sum() + abl[[G, X]].isna().sum().sum()))"""))

cells.append(md("""## 1. A/B : (a) brut · (b) « 6 questions » · (c) brut + contexte complet

Les 5 tâches : résumer un papier (`t1`), refactorer une fonction (`t2`), comparer LiteLLM et OpenRouter (`t3`),
rédiger un courriel d'incident (`t4`), extraire des données d'un rapport (`t5`).

- **(a)** une ligne tapée en 30 s, typos comprises (+ l'artefact quand la tâche en a un : papier, code, rapport) ;
- **(b)** gabarit `forge/prompts/<id>.md` : Rôle · Tâche · Contexte · Contraintes · Format · Critère (+ un exemple) ;
- **(c)** le prompt (a) + les notes de contexte collées telles quelles, sans structure."""))

cells.append(code("""from b1_common import build_prompt, TASKS
pd.DataFrame({v: {t: len(build_prompt(t, v)) for t in TASKS} for v in "abc"}).rename_axis("longueur du prompt (car.)")"""))

cells.append(code("""print("Moyenne par modèle et variante (2 juges)")
display(ab.pivot_table(index="model", columns="variant", values="score", margins=True, margins_name="tous"))
print("Moyenne par tâche et variante")
display(ab.pivot_table(index="task", columns="variant", values="score"))"""))

cells.append(code("""pt = ab.pivot_table(index=["task", "model"], columns="variant", values="score")
pt["b-a"] = pt.b - pt.a; pt["c-b"] = pt.c - pt.b
display(pt)
print(f"b > a dans {(pt.b > pt.a).sum()}/10 cellules ; c ≥ b dans {(pt.c >= pt.b).sum()}/10 cellules")
print("Écart-type intra-variante :", ab.groupby("variant").score.std().round(2).to_dict())"""))

cells.append(code("""print("Robustesse : chaque juge séparément")
display(ab.groupby("variant")[[G, X]].mean())
print("Corrélation entre juges :", round(ab[[G, X]].corr().iloc[0, 1], 2))
print("Critères (moyenne des 2 juges)")
display(ab.groupby("variant")[["clarte", "completude", "format", "utilite", "words"]].mean())"""))

cells.append(md("""### Conclusion A/B

| | (a) brut | (b) 6Q | (c) brut + contexte |
|---|---|---|---|
| gpt-4o-mini | 2,33 | **4,61** | 4,50 |
| claude-haiku-4-5 | 2,81 | 4,66 | **4,71** |
| **Les deux** | **2,57** | **4,64** | **4,61** |

- **(b) > (a) : confirmé, largement** (+2,1 points, 10 cellules sur 10, et pour les deux juges séparément). Le gain vient de la **complétude** (2,1 → 4,7), du **format** (2,1 → 4,5) et de l'**utilité** (1,9 → 4,5), bien plus que de la clarté (4,2 → 4,9) : le brut est lisible mais il répond à côté du besoin.
- **(c) ≥ (b) : confirmé cellule par cellule (9/10), égalité en moyenne** (4,61 vs 4,64, écart dans le bruit, σ ≈ 0,5). Coller le contexte en vrac donne le même résultat que le prompt 6Q soigné : **le contexte fait le travail, pas la structure.**
- L'exception est instructive : `t1` × gpt-4o-mini, (c) 3,06 < (b) 3,81. Quand le besoin de format est noyé dans des notes en vrac (« 200 mots, en puces, avis clair »), gpt-4o-mini l'ignore et paraphrase l'abstract ; la section `Format` explicite le corrige. Haiku n'en a pas besoin (4,62 vs 4,56).
- Les tâches `t3`, `t4` et `t5` saturent à 5/5 en (b) et (c) : pour les départager, il faudra des critères objectifs (B10).
- Les typos du brut ne gênent pas les modèles ; c'est l'absence de contexte qui coûte."""))

cells.append(md("""## 2. Ablation : retirer un élément à la fois du prompt 6Q

Tâches retenues : `t1_resume` (seule tâche avec de la marge au juge, plus des contraintes mesurables : ≤ 200 mots, copie de l'exemple) et
`t5_extraire` (le meilleur prompt, 5/5, avec des métriques objectives : JSON strict, exactitude des champs).
4 répétitions × 2 modèles par variante. `copie_exemple` = similarité max (difflib) entre la phrase d'exemple et une ligne de la sortie."""))

cells.append(code("""t1 = abl[abl.task == "t1_resume"]
display(t1.pivot_table(index="retire", columns="model", values="score"))
display(t1.groupby(["retire", "model"])[["format", "words", "respect_200_mots", "copie_exemple"]].mean())
print("σ du score par cellule :")
display(t1.groupby(["retire", "model"]).score.std().unstack())"""))

cells.append(code("""t5 = abl[abl.task == "t5_extraire"]
display(t5.groupby(["retire", "model"])[["score", "json_strict", "json_tolerant", "field_acc", "words"]].mean())"""))

cells.append(md("""### Conclusion ablation

**Éléments prouvés inutiles (sur `t5_extraire`, le meilleur prompt) : `Critère de réussite` et `Contraintes`.**
Les retirer ne change **aucune** métrique sur 8 runs : score du juge 5,0, JSON strict identique (gpt 4/4, Haiku 0/4), exactitude des champs 100 %,
même longueur de sortie. Le schéma JSON (dans `Contexte`) porte déjà les règles des champs (« null si pas de date précise », énumération des statuts) :
les consignes de `Contraintes` faisaient doublon.

Ce qui compte vraiment :
- **`Format` est indispensable pour le JSON strict** : sans lui, gpt-4o-mini passe de 4/4 à 1/4 JSON parsable sans nettoyage (il rajoute un bloc ```json).
- **`Exemple` fixe la forme, pas le fond** : sur `t5`, l'exemple compact fait sortir gpt-4o-mini en JSON sur une ligne (36 mots contre 120 sans). Sur `t1`, il est **contre-productif** : gpt-4o-mini recopie la phrase d'exemple (similarité 0,76 → 0,38 sans exemple) et Haiku est **meilleur sans** (4,72 → 4,94, format 4,1 → 4,75). Mais gpt-4o-mini perd 0,6 point sans exemple : un exemple unique est un mauvais compromis → v2 avec 2–3 exemples variés (théorie du B1).
- **`Rôle` : effet faible et dans le bruit** sur `t1` (−0,03 pour Haiku, −0,25 pour gpt avec σ ≈ 0,4) ; sur `t5`, sans rôle, gpt-4o-mini fait des erreurs de champs (exactitude moyenne 0,92 au lieu de 1,0). Candidat « inutile » sur Haiku, à confirmer avec plus de runs.
- **`Format` et `Critère` comptent pour gpt-4o-mini sur `t1`** (−0,9 et −0,75), quasi pas pour Haiku : **l'utilité d'un élément dépend du modèle.**
- La contrainte de longueur « 200 mots » n'est **jamais** respectée par Haiku avec le prompt complet (0/8, ≈ 250 mots) : une limite en mots est un mauvais levier pour ce modèle."""))

cells.append(md("""## 3. Format JSON + Pydantic (tâche `t5_extraire`)

Schéma `RapportProjets` (Pydantic v2, `extra="forbid"`, `statut: Literal[...]`, `date_prochain_jalon: date | None`, montants `int`).
**Valide = `RapportProjets.model_validate_json(sortie_brute)`** sans aucun nettoyage. 20 runs par condition (10 gpt-4o-mini + 10 claude-haiku-4-5), température 0,7.

- `v1` : gabarit `extraire-json` seul (« pas de bloc de code Markdown ») ;
- `v1+prefill` : même gabarit ; pour Anthropic, le tour assistant est pré-rempli par `{` (technique documentée par Anthropic ; la sortie validée = `{` + texte)."""))

cells.append(code("""import inspect, b1_common
print(inspect.getsource(b1_common.Projet)); print(inspect.getsource(b1_common.RapportProjets))"""))

cells.append(code("""summary = js.groupby("condition").agg(runs=("strict_valid", "size"), json_strict=("strict_valid", "sum"),
                                     json_tolerant=("tolerant_valid", "sum"), exactitude_champs=("field_acc", "mean"))
summary["% strict"] = 100 * summary.json_strict / summary.runs
display(summary)
display(js.groupby(["condition", "model"])[["strict_valid", "tolerant_valid", "field_acc"]].mean())
print("Erreurs v1 (Haiku) :", js[(js.condition == "v1") & ~js.strict_valid].validation_error.str[:90].unique()[:2])"""))

cells.append(md("""### Conclusion JSON

- **`v1+prefill` : 20/20 JSON strict valide (100 %, cible ≥ 95 % atteinte)**, exactitude des champs 100 % vs vérité terrain (4 projets × 7 champs).
- `v1` seul : 10/20 (50 %). gpt-4o-mini 10/10 ; **claude-haiku-4-5 0/10 : il entoure toujours le JSON d'un bloc ```json malgré la consigne explicite.** Le contenu est parfait (20/20 après retrait du bloc).
- Leçon : la consigne « pas de bloc de code » ne suffit pas pour Haiku ; le **prefill `{`** (ou un parseur tolérant, ou le mode JSON natif) règle le problème à coût nul. En A/B, le brut (a) donnait 0/4 JSON exploitable : texte libre ou clés inventées."""))

cells.append(md("""## 4. Bibliothèque v1 : 10 gabarits `forge/prompts/*.md`

Les 5 gabarits de l'A/B sont les variantes (b). Les 5 gabarits annexes (A.3, A.4, A.5, A.6 adaptés + résumé de thread GitHub) ont été testés
en réel (2 modèles × 2 runs, même double juge)."""))

cells.append(code("""from forge.prompts import list_prompts
pd.DataFrame([{"id": p.id, "version": p.meta["version"], "variables": ", ".join(p.variables),
               "score_moyen": p.meta["score_moyen"], "sections": " · ".join(p.section_names())} for p in list_prompts()])"""))

cells.append(code("""display(lib.pivot_table(index="template", columns="model", values="score", margins=True, margins_name="moyenne"))
print("JSON valide scoring-pertinence :", int(lib.json_valid.sum()), "/", int(lib.json_valid.notna().sum()))
print("Consigne injectée reprise dans le résumé de thread :", lib.dropna(subset=["injection_reprise"]).groupby("model").injection_reprise.sum().to_dict())"""))

cells.append(md("""## 5. Synthèse et limites

**Hypothèse (c) ≥ (b) > (a) : confirmée.** b > a très nettement (+2,1) ; c ≈ b (égalité, c ≥ b dans 9 cellules sur 10).
**Élément inutile :** `Critère de réussite` (et `Contraintes`, redondantes avec le schéma) sur l'extraction ; `Exemple` unique nuisible sur le résumé pour Haiku.
**JSON :** 20/20 (100 %) avec prefill, 10/20 sans.

Limites (à garder en tête avant d'en faire des règles) :
- Petits échantillons (2 rép. par cellule en A/B, 4 en ablation) : seuls les écarts > ~0,5 sont lisibles.
- Juges LLM : Gemini note ~0,3–0,7 plus haut que Grok, mais les deux classent les variantes pareil (r = 0,9). Le juge voit le besoin réel, ce qui pénalise (a) *par construction* : c'est voulu (on mesure l'utilité pour l'utilisateur).
- Effet plafond sur `t3`/`t4`/`t5` : il faudra des cas plus durs et des critères objectifs (B10).
- Fixtures fictives écrites pour l'exercice : les vraies tâches de la semaine seront plus bruitées."""))

nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = ROOT / "notebooks" / "b1_ab.ipynb"
nbf.write(nb, out)
print("écrit", out)
