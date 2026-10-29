"""Bloc B1 : définitions partagées (tâches, variantes a/b/c, juge LLM, schéma Pydantic).

Les fixtures (contenu fictif mais réaliste) sont sous forge/prompts/_fixtures/ (commitées)
pour que tout soit reproductible ; data/ reste local et ignoré.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import forge.clients as clients  # noqa: E402
from forge.prompts import load_prompt  # noqa: E402

FIX = ROOT / "forge" / "prompts" / "_fixtures"
RESULTS = ROOT / "notebooks" / "b1_results"
RESULTS.mkdir(parents=True, exist_ok=True)

MODELS = ["gpt-4o-mini", "anthropic/claude-haiku-4-5"]
JUDGES = ["gemini/gemini-3.5-flash-lite", "xai/grok-3-mini"]

# Écritures concurrentes dans data/calls.jsonl : on sérialise.
_lock = threading.Lock()
_orig_write = clients._write_log


def _locked_write(rec: dict) -> None:
    with _lock:
        _orig_write(rec)


clients._write_log = _locked_write


def fx(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def call(model: str, prompt: str, max_tokens: int = 1600, temperature: float = 0.7, retries: int = 2) -> dict:
    last: Exception | None = None
    for _ in range(retries + 1):
        try:
            return clients.complete(model, [{"role": "user", "content": prompt}],
                                    max_tokens=max_tokens, temperature=temperature)
        except clients.MissingAPIKeyError:
            raise
        except Exception as e:  # noqa: BLE001
            last = e
    return {"text": "", "error": f"{type(last).__name__}: {last}", "in_tokens": None, "out_tokens": None, "latency": None}


def pmap(fn, items, workers: int = 6):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))


# ---------------------------------------------------------------------------
# Tâches : (a) brut 30 s, (b) 6Q (gabarit forge/prompts), (c) brut + contexte collé
# ---------------------------------------------------------------------------
PAPIER = fx("t1_papier.md")
CODE = fx("t2_code.py")
NOTES_OUTILS = fx("t3_outils.md")
CTX_EMAIL = fx("t4_email.md")
RAPPORT = fx("t5_rapport.txt")

SCHEMA_TXT = """{
  "projets": [
    {
      "nom": "string (ex. ORION-NLP)",
      "responsable": "string, nom sans titre (Dr, M., Mme)",
      "statut": "en_cours | en_pause | termine",
      "budget_alloue_eur": "entier",
      "budget_consomme_eur": "entier",
      "etp": "nombre",
      "prochain_jalon": "string ou null",
      "date_prochain_jalon": "AAAA-MM-JJ ou null si pas de date précise",
      "risque_principal": "string ou null si aucun"
    }
  ]
}"""

CONSIGNES_CHAMPS = """- Un objet par projet, dans l'ordre du document.
- Montants en euros, entiers, sans séparateur ni unité (420 000 EUR → 420000).
- `statut` : uniquement en_cours, en_pause ou termine.
- `date_prochain_jalon` : AAAA-MM-JJ ; une date vague (« T1 2027, non confirmée ») → null.
- « Aucun risque signalé » → risque_principal null."""

TASKS: dict[str, dict[str, Any]] = {
    "t1_resume": {
        "label": "Résumer un papier technique",
        "template": "resume-papier",
        "raw": "resume moi ce papier stp, les points importants\n\n" + PAPIER,
        "context": fx("t1_contexte.md"),
        "vars": dict(
            texte=PAPIER,
            public="équipe ML Infra (5 ingénieurs) qui sert Llama-3.1-70B en interne, contextes de 32k à 128k jetons, 4×H100, batch moyen 4",
            objectif="décider s'il faut prototyper SPARQ au T1 2027 ou attendre",
            longueur="200 mots",
        ),
    },
    "t2_refactor": {
        "label": "Refactorer une fonction Python",
        "template": "refactor-fonction",
        "raw": "tu peux refactor cette fonction python stp elle est moche\n\n" + CODE,
        "context": fx("t2_contexte.md"),
        "vars": dict(
            code=CODE.strip(),
            contexte=("Fonction héritée `utils/report.py::proc`, appelée par le job nocturne de facturation "
                      "(~50 000 factures/nuit venant d'une API interne type Stripe). `d` = liste de factures (dicts), "
                      "`t` = mois « AAAA-MM » optionnel, `f` = appliquer la TVA 20 %. La chaîne JSON retournée est écrite "
                      "telle quelle dans S3 et lue par un tableau de bord. Bug connu : `amount = None` sur certaines "
                      "factures → TypeError la nuit."),
            contraintes_equipe="- Python 3.11, mypy strict, ruff ; aucune nouvelle dépendance.",
        ),
    },
    "t3_comparer": {
        "label": "Comparer deux outils (LiteLLM vs OpenRouter)",
        "template": "comparer-outils",
        "raw": "compare litellm et openrouter, lequel on prend ?",
        "context": NOTES_OUTILS,
        "vars": dict(outil_a="LiteLLM", outil_b="OpenRouter", notes=NOTES_OUTILS,
                     decideur="la DSI, décision vendredi, recommandation d'une page"),
    },
    "t4_email": {
        "label": "Rédiger un courriel technique",
        "template": "email-technique",
        "raw": ("ecris un mail a claire vasseur (sre chez l'hebergeur) pour l'incident de mardi sur le cluster, "
                "des volumes sont restés bloqués, on veut un post mortem"),
        "context": CTX_EMAIL,
        "vars": dict(
            expediteur="Mériadec Finoude, lead tech Plateforme Data",
            destinataire="Claire Vasseur, responsable SRE chez notre hébergeur cloud (relation cordiale, vouvoiement)",
            faits=("- Mardi 27/10/2026, 14h05–15h40 (Paris) : cluster Kubernetes `prod-eu-1`, perte de 3 nœuds sur 8 en zone eu-west-3b.\n"
                   "- Pods de l'API de scoring replanifiés, mais 2 volumes persistants bloqués en « Attaching » pendant 82 min.\n"
                   "- Impact : 18 % de requêtes en 503 pendant 1h35 ; budget d'erreur du SLA 99,9 % mensuel consommé à 74 %.\n"
                   "- Ticket #INC-48213 ouvert à 14h12 ; première réponse à 15h55, après résolution.\n"
                   "- Déjà fait chez nous : anti-affinité de zone, alerte sur PV > 5 min en « Attaching »."),
            demandes=("1. Post-mortem écrit d'ici le 6 novembre.\n2. Explication du blocage « Attaching ».\n"
                      "3. Crédit SLA applicable ?\n4. Appel de 30 min : mardi 3/11 10h–12h ou jeudi 5/11 14h–17h."),
            ton="ferme mais collaboratif, factuel, sans accusation",
            longueur="environ 200 mots (250 max)",
        ),
    },
    "t5_extraire": {
        "label": "Extraire des données structurées d'un rapport",
        "template": "extraire-json",
        "raw": "extrait les données des projets en json\n\n" + RAPPORT,
        "context": fx("t5_contexte.md"),
        "vars": dict(texte=RAPPORT, schema=SCHEMA_TXT, consignes_champs=CONSIGNES_CHAMPS),
    },
}

# Ce que le juge sait du « besoin réel » (identique pour les 3 variantes).
ARTEFACT_FOR_JUDGE = {
    "t1_resume": PAPIER,
    "t2_refactor": CODE,
    "t3_comparer": "",
    "t4_email": "",
    "t5_extraire": RAPPORT,
}


def build_prompt(task_id: str, variant: str, drop: tuple[str, ...] = ()) -> str:
    t = TASKS[task_id]
    if variant == "a":
        return t["raw"]
    if variant == "c":
        return t["raw"] + "\n\n" + t["context"]
    if variant == "b":
        return load_prompt(t["template"]).render(drop=drop, **t["vars"])
    raise ValueError(variant)


# ---------------------------------------------------------------------------
# Juge LLM (grille courte, 1–5) — deux juges d'autres familles que les modèles testés
# ---------------------------------------------------------------------------
JUDGE_TMPL = """Tu es un évaluateur exigeant et cohérent. Tu notes la RÉPONSE d'un assistant à une demande.

Le demandeur avait le BESOIN RÉEL ci-dessous (l'assistant ne l'a peut-être pas reçu en entier : note quand même par rapport à ce besoin réel, c'est ce qui compte pour l'utilisateur).

<tache>{label}</tache>
<besoin_reel>
{context}
</besoin_reel>
<source>
{artefact}
</source>
<reponse>
{answer}
</reponse>

Grille (entiers de 1 à 5) :
- clarte : 5 = immédiatement lisible et bien structurée ; 1 = confuse.
- completude : 5 = couvre tout ce que le besoin réel demande, sans erreur factuelle par rapport à la source ; 1 = manque l'essentiel ou contient des erreurs.
- format : 5 = respecte exactement la forme attendue par le besoin réel (longueur, structure, langue, JSON pur si demandé) ; 1 = forme inadaptée.
- utilite : 5 = directement utilisable par le demandeur sans retouche ; 1 = inutilisable.

Réponds UNIQUEMENT avec ce JSON, sans bloc de code :
{{"clarte": n, "completude": n, "format": n, "utilite": n, "justification": "une phrase"}}"""

CRITERIA = ["clarte", "completude", "format", "utilite"]


def _first_json_obj(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def judge(task_id: str, answer: str, judge_model: str) -> dict:
    t = TASKS[task_id]
    prompt = JUDGE_TMPL.format(label=t["label"], context=t["context"],
                               artefact=ARTEFACT_FOR_JUDGE[task_id] or "(pas de source séparée)",
                               answer=answer or "(réponse vide)")
    max_tokens = 3000 if "grok" in judge_model else 400
    for _ in range(3):
        r = call(judge_model, prompt, max_tokens=max_tokens, temperature=0)
        d = _first_json_obj(r.get("text", ""))
        if d and all(isinstance(d.get(c), (int, float)) for c in CRITERIA):
            d["score"] = sum(d[c] for c in CRITERIA) / len(CRITERIA)
            d["judge"] = judge_model
            return d
    return {"judge": judge_model, "score": None, "error": "juge illisible"}


def judge_both(task_id: str, answer: str) -> dict:
    js = [judge(task_id, answer, jm) for jm in JUDGES]
    scores = [j["score"] for j in js if j.get("score") is not None]
    out: dict[str, Any] = {"score": sum(scores) / len(scores) if scores else None}
    for j in js:
        short = j["judge"].split("/")[-1]
        out[f"score_{short}"] = j.get("score")
        for c in CRITERIA:
            out[f"{c}_{short}"] = j.get(c)
        out[f"justif_{short}"] = j.get("justification")
    for c in CRITERIA:
        vals = [j.get(c) for j in js if j.get(c) is not None]
        out[c] = sum(vals) / len(vals) if vals else None
    return out


# ---------------------------------------------------------------------------
# Extraction : schéma Pydantic + vérité terrain
# ---------------------------------------------------------------------------
class Projet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nom: str
    responsable: str
    statut: Literal["en_cours", "en_pause", "termine"]
    budget_alloue_eur: int = Field(ge=0)
    budget_consomme_eur: int = Field(ge=0)
    etp: float = Field(ge=0)
    prochain_jalon: str | None
    date_prochain_jalon: date | None
    risque_principal: str | None


class RapportProjets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projets: list[Projet] = Field(min_length=1)


GOLD = [
    dict(nom="ORION-NLP", responsable="Inès Barral", statut="en_cours", budget_alloue_eur=420000,
         budget_consomme_eur=287500, etp=6, date_prochain_jalon="2026-12-15", risque_null=False),
    dict(nom="ORION-VISION", responsable="Tomasz Wierzbicki", statut="en_pause", budget_alloue_eur=610000,
         budget_consomme_eur=198000, etp=4, date_prochain_jalon=None, risque_null=False),
    dict(nom="ORION-EDGE", responsable="Amara Diallo", statut="termine", budget_alloue_eur=150000,
         budget_consomme_eur=162300, etp=2, date_prochain_jalon=None, risque_null=True),
    dict(nom="ORION-SAFE", responsable="Lucie Fontaine", statut="en_cours", budget_alloue_eur=95000,
         budget_consomme_eur=41200, etp=1.5, date_prochain_jalon="2026-11-20", risque_null=False),
]


def _n(s: Any) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def validate_extraction(text: str) -> dict:
    """strict = le texte brut parse + valide ; tolerant = après retrait d'un bloc ```json."""
    res: dict[str, Any] = {"strict_valid": False, "tolerant_valid": False, "field_acc": None, "error": None}
    obj = None
    try:
        obj = RapportProjets.model_validate_json(text.strip())
        res["strict_valid"] = res["tolerant_valid"] = True
    except ValidationError as e:
        res["error"] = str(e).splitlines()[0][:200]
        stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        try:
            obj = RapportProjets.model_validate_json(stripped)
            res["tolerant_valid"] = True
        except ValidationError as e2:
            res["error"] = str(e2).splitlines()[0][:200] + " | " + str(e2).splitlines()[-1][:200]
    if obj is not None:
        ok = tot = 0
        by_name = {_n(p.nom): p for p in obj.projets}
        for g in GOLD:
            p = by_name.get(_n(g["nom"]))
            checks = 7
            tot += checks
            if p is None:
                continue
            ok += _n(p.responsable) == _n(g["responsable"])
            ok += p.statut == g["statut"]
            ok += p.budget_alloue_eur == g["budget_alloue_eur"]
            ok += p.budget_consomme_eur == g["budget_consomme_eur"]
            ok += abs(p.etp - g["etp"]) < 1e-9
            ok += (str(p.date_prochain_jalon) if p.date_prochain_jalon else None) == g["date_prochain_jalon"]
            ok += (p.risque_principal is None) == g["risque_null"]
        res["field_acc"] = ok / tot
        res["n_projets"] = len(obj.projets)
    return res


def write_jsonl(path: pathlib.Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
