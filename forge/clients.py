"""Wrapper unifié multi-fournisseurs, avec journalisation de chaque appel (bloc B0).

Usage :
    from forge.clients import complete
    r = complete("openrouter/openai/gpt-4o-mini", [{"role": "user", "content": "Salut"}])
    r["text"], r["in_tokens"], r["out_tokens"]

`model` est une chaîne de modèle LiteLLM, par ex. :
    "gpt-4o-mini", "anthropic/claude-3-5-haiku-latest", "gemini/gemini-1.5-flash",
    "xai/grok-2-latest", "openrouter/meta-llama/llama-3.1-8b-instruct".

Chaque appel (réussi ou non) ajoute une ligne JSON dans data/calls.jsonl
(ou dans le chemin donné par la variable d'environnement FORGE_LOG_PATH).
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from typing import Any

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Charge le .env du repo (sans écraser les variables déjà définies), puis celui du cwd.
load_dotenv(ROOT / ".env")
load_dotenv()

# LiteLLM attend GEMINI_API_KEY pour les modèles "gemini/..." : on réutilise GOOGLE_API_KEY.
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]


class MissingAPIKeyError(RuntimeError):
    """Aucune clé API utilisable pour le fournisseur du modèle demandé."""


def log_path() -> pathlib.Path:
    """Chemin du journal JSONL (FORGE_LOG_PATH ou <repo>/data/calls.jsonl)."""
    env = os.getenv("FORGE_LOG_PATH")
    return pathlib.Path(env) if env else ROOT / "data" / "calls.jsonl"


def prompt_hash(messages: list[dict]) -> str:
    payload = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]


def _missing_key_message(model: str, missing: list[str] | None = None) -> str:
    keys = ", ".join(missing) if missing else "la clé du fournisseur"
    return (
        f"Aucune clé API disponible pour le modèle '{model}' (manquant : {keys}). "
        "Copie .env.example vers .env à la racine de llm-forge et remplis la clé "
        "correspondante (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, "
        "XAI_API_KEY ou OPENROUTER_API_KEY)."
    )


def _dispatch(model: str, messages: list[dict], **kw: Any) -> dict:
    """Appelle le modèle via LiteLLM et normalise la réponse."""
    import litellm  # import paresseux : l'import de litellm est lent

    # Vérification préalable des clés (évite un message d'erreur cryptique).
    try:
        env = litellm.validate_environment(model=model)
    except Exception:  # fournisseur inconnu de validate_environment : on laisse litellm décider
        env = {"keys_in_environment": True, "missing_keys": []}
    if not env.get("keys_in_environment", True) and not kw.get("api_key"):
        raise MissingAPIKeyError(_missing_key_message(model, env.get("missing_keys")))

    try:
        resp = litellm.completion(model=model, messages=messages, **kw)
    except litellm.AuthenticationError as e:
        raise MissingAPIKeyError(_missing_key_message(model) + f" Détail : {e}") from e

    usage = getattr(resp, "usage", None)
    return {
        "text": resp.choices[0].message.content or "",
        "in_tokens": getattr(usage, "prompt_tokens", None),
        "out_tokens": getattr(usage, "completion_tokens", None),
        "model_resolved": getattr(resp, "model", None),
    }


def _write_log(rec: dict) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def complete(model: str, messages: list[dict], **kw: Any) -> dict:
    """Appelle `model` (chaîne LiteLLM) avec `messages` et journalise l'appel.

    Retourne un dict : {"text", "in_tokens", "out_tokens", "latency", "model", "model_resolved"}.
    Lève MissingAPIKeyError si la clé du fournisseur est absente ou refusée.
    Les autres erreurs sont journalisées puis relancées.
    """
    t0 = time.time()
    rec: dict[str, Any] = {
        "ts": t0,
        "model": model,
        "prompt_hash": prompt_hash(messages),
        "messages": messages,
        # on ne journalise jamais une clé passée en paramètre
        "meta": {k: v for k, v in kw.items() if k not in {"api_key"}},
    }
    try:
        out = _dispatch(model, messages, **kw)
    except Exception as e:
        rec.update(latency=time.time() - t0, error=f"{type(e).__name__}: {e}")
        _write_log(rec)
        raise
    latency = time.time() - t0
    rec.update(
        latency=latency,
        in_tokens=out.get("in_tokens"),
        out_tokens=out.get("out_tokens"),
        model_resolved=out.get("model_resolved"),
        output=out["text"],
    )
    _write_log(rec)
    return {**out, "latency": latency, "model": model}


__all__ = ["complete", "MissingAPIKeyError", "log_path", "prompt_hash"]
