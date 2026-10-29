"""Test de fumée : appelle un modèle peu coûteux si une clé est disponible.

Usage : python scripts/smoke_local.py [--model CHAINE_LITELLM]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.clients import MissingAPIKeyError, complete, log_path  # noqa: E402

# Ordre de préférence : (variable d'environnement, modèle LiteLLM peu coûteux)
CHEAP_MODELS = [
    ("OPENROUTER_API_KEY", "openrouter/openai/gpt-4o-mini"),
    ("OPENAI_API_KEY", "gpt-4o-mini"),
    ("ANTHROPIC_API_KEY", "anthropic/claude-3-5-haiku-latest"),
    ("GOOGLE_API_KEY", "gemini/gemini-1.5-flash"),
    ("XAI_API_KEY", "xai/grok-3-mini"),
]

HELP = """\
Aucune clé API trouvée.

1. cp .env.example .env
2. Remplis au moins une de ces variables dans .env :
   OPENROUTER_API_KEY (le plus simple : un compte, plein de modèles),
   OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, XAI_API_KEY
3. Fixe une limite de dépense mensuelle sur la console du fournisseur.
4. Relance : python scripts/smoke_local.py
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", help="chaîne de modèle LiteLLM à forcer")
    args = ap.parse_args()

    if args.model:
        model = args.model
    else:
        model = next((m for var, m in CHEAP_MODELS if os.getenv(var)), None)
        if model is None:
            print(HELP)
            return 1

    print(f"→ Appel de {model} …")
    try:
        r = complete(model, [{"role": "user", "content": "Réponds en une phrase : à quoi sert un journal d'appels LLM?"}],
                     max_tokens=60, temperature=0)
    except MissingAPIKeyError as e:
        print(f"✗ {e}")
        return 1
    print(f"✓ {r['text']}")
    print(f"  jetons : in={r['in_tokens']} out={r['out_tokens']}  latence={r['latency']:.2f}s")
    print(f"  journalisé dans {log_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
