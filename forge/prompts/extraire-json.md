---
id: extraire-json
version: 1
modeles_testes: [gpt-4o-mini, anthropic/claude-haiku-4-5]
variables: [texte, schema, consignes_champs]
score_moyen: 5.0
notes: "A/B B1 : juge 5,0 ; exactitude des champs 100 %. JSON strict 20/20 avec prefill « { » pour Anthropic, 10/20 sans (Haiku met toujours un bloc ```json malgré la consigne). Ablation : « Critère de réussite » et « Contraintes » sans effet mesurable (le schéma suffit) ; retirer « Format » fait passer gpt-4o-mini de 4/4 à 1/4 JSON strict ; l'exemple compact rend la sortie 3× plus courte."
---
## Rôle
Tu es un extracteur de données rigoureux qui transforme des documents en JSON exploitable par un programme.

## Tâche
Extrais du document dans « Entrée » un objet JSON conforme au schéma.

## Contexte
Le JSON est validé automatiquement par un modèle Pydantic puis chargé dans un tableur de suivi ; toute sortie non parsable est rejetée.
Schéma JSON :
{schema}

## Contraintes
{consignes_champs}
- N'invente rien : valeur absente du texte → null.
- Ignore les en-têtes et pieds de page répétés.

## Format
Réponds UNIQUEMENT avec l'objet JSON : pas de texte avant ou après, pas de bloc de code Markdown, guillemets doubles.

## Critère de réussite
`json.loads` puis la validation Pydantic réussissent du premier coup, et chaque valeur se retrouve dans le texte.

## Exemple
{"projets": [{"nom": "EXEMPLE-X", "responsable": "Jean Dupont", "statut": "en_cours", "budget_alloue_eur": 100000, "budget_consomme_eur": 25000, "etp": 2, "prochain_jalon": "Livraison bêta", "date_prochain_jalon": "2027-01-31", "risque_principal": null}]}

## Entrée
<document>
{texte}
</document>
