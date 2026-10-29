# Notes internes : passerelle LLM pour l'équipe Data (8 personnes)

## Besoins
- Appeler OpenAI, Anthropic, Google, xAI et 1–2 modèles ouverts (Llama, Qwen) depuis Python.
- Journaliser chaque appel (coût, latence, jetons) dans notre propre stockage (conformité RGPD : les prompts contiennent parfois des données clients pseudonymisées ; hébergement UE souhaité).
- Fallback automatique si un fournisseur tombe.
- Budget : < 300 €/mois de frais de plateforme hors jetons.
- Une personne ops à 20 % pour maintenir l'outillage.

## LiteLLM (observé en interne, mars 2026)
- Bibliothèque Python open source (MIT) + proxy auto-hébergeable (Docker).
- Interface compatible OpenAI pour 100+ fournisseurs ; on utilise déjà `litellm.completion` dans llm-forge.
- Clés gérées chez nous ; les données ne transitent par aucun tiers en plus du fournisseur.
- Fallbacks, retries, budgets par clé virtuelle, logs vers Postgres/S3/Langfuse.
- Coût : gratuit en self-host ; version entreprise payante (SSO, audit) ~ prix sur devis.
- Inconvénients vus : mises à jour fréquentes qui cassent parfois des noms de modèles ; proxy à opérer (Postgres, Redis pour le rate limiting).

## OpenRouter (observé en interne, mars 2026)
- Service SaaS (US) : une seule clé API, une seule facture, 300+ modèles dont beaucoup de modèles ouverts hébergés par des tiers.
- API compatible OpenAI ; LiteLLM le supporte aussi comme fournisseur (`openrouter/...`).
- Routage automatique entre hébergeurs, fallback intégré.
- Marge d'environ 5 % sur l'achat de crédits ; pas de frais fixes.
- Données : transitent par OpenRouter puis par l'hébergeur choisi ; option pour exclure les fournisseurs qui entraînent sur les données ; pas d'hébergement UE garanti.
- Très pratique pour tester vite un nouveau modèle ouvert sans compte chez chaque fournisseur.
- Logs d'usage dans leur tableau de bord ; export via API.

## Contraintes de décision
- Décision attendue vendredi par la DSI ; recommandation d'une page max.
- Le DPO a déjà signalé que l'absence de garantie UE est bloquante pour les données clients, mais pas pour les tests sur données synthétiques.
