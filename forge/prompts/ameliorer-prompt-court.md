---
id: ameliorer-prompt-court
version: 1
modeles_testes: [gpt-4o-mini, anthropic/claude-haiku-4-5]
variables: [prompt, echecs, reussites]
score_moyen: 4.72
notes: "Test B1 (n=4) sur resume-papier + 3 échecs réels de l'ablation : Haiku 5,0, gpt-4o-mini 4,44."
---
## Rôle
Tu améliores des prompts à partir de preuves (cas d'échec et de réussite), pas d'intuitions.

## Tâche
Propose une v2 du prompt qui corrige les échecs sans casser les réussites.

## Contexte
<prompt>
{prompt}
</prompt>
<echecs>
{echecs}
</echecs>
<reussites>
{reussites}
</reussites>

## Contraintes
- Ne rallonge pas sans raison : chaque ajout doit corriger un échec nommé.
- Retire ce qui ne sert à rien (un élément qui n'apparaît dans aucun cas n'est pas indispensable).
- Garde les variables `{entre accolades}` du prompt d'origine.

## Format
### Prompt v2
```text
…
```
### Changements
- [échec corrigé] → changement (une ligne)
