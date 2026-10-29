# data/

Données **locales**, jamais commitées (voir `.gitignore`).

- `calls.jsonl` : journal local de chaque appel fait via `forge.clients.complete`
  (une ligne JSON par appel : horodatage, modèle, latence, jetons, empreinte du prompt,
  messages, sortie, paramètres). Créé automatiquement au premier appel.

Seuls ce README et `.gitkeep` sont suivis par git.
