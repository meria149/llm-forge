# llm-forge

Framework personnel pour **maîtriser les LLM dans un cadre métier** : choisir le bon modèle,
le piloter sur des tâches longues, mesurer la qualité de ses sorties et capitaliser ce qui marche.

## Intention

- **Un seul point d'entrée** (`forge.clients.complete`) pour appeler n'importe quel modèle
  (OpenAI, Anthropic, Google, xAI, OpenRouter, modèles ouverts) via LiteLLM.
- **Tout est journalisé** dans `data/calls.jsonl` : modèle, latence, jetons, empreinte du prompt, sortie.
- **Rien sans éval** : un prompt sans cas de test reste une opinion (harnais prévu en B10-B11).
- **Routage selon les forces de chaque modèle** (`forge/router.py`, bloc B4).
- **Agents et sessions longues** avec critères d'arrêt (`forge/agents/`, B5-B6).
- **Automatisation de la veille et de la recherche** vérifiable (`forge/research/`, B7-B8).
- **Gabarits de prompts versionnés** en Markdown avec front-matter YAML (`forge/prompts/`).
- **Hors périmètre, explicitement** : jailbreaks, prompts de « libération », contournement des
  garde-fous. On garde seulement la robustesse **défensive** (protéger *nos* agents contre le
  contenu non fiable).

## Démarrage rapide

```bash
uv venv && source .venv/bin/activate     # ou : python -m venv .venv
uv pip install -e ".[dev]"                # ou : pip install -e ".[dev]"
cp .env.example .env                      # puis remplir au moins une clé (jamais commitée)
python scripts/smoke_local.py             # appel test vers un modèle peu coûteux
pytest -q
```

```python
from forge.clients import complete
r = complete("openrouter/openai/gpt-4o-mini", [{"role": "user", "content": "Bonjour!"}])
print(r["text"], r["in_tokens"], r["out_tokens"])
```

## Arborescence

| Dossier | Rôle |
|---|---|
| `forge/` | Code du framework (clients, routeur, prompts, agents, recherche, évals) |
| `notebooks/` | Expériences A/B et explorations |
| `journal/` | Une entrée par bloc : `AAAA-MM-JJ-bN.md` |
| `data/` | Données locales (ignorées par git), dont `calls.jsonl` |
| `tests/` | Tests unitaires (sans appel réseau) |
| `scripts/` | Utilitaires (test de fumée, etc.) |

## Sécurité des clés

Les clés vivent uniquement dans `.env` (ignoré par git). Fixe une limite de dépense mensuelle
sur chaque console fournisseur.
