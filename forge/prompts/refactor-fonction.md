---
id: refactor-fonction
version: 1
modeles_testes: [gpt-4o-mini, anthropic/claude-haiku-4-5]
variables: [code, contexte, contraintes_equipe]
score_moyen: 4.12
notes: "A/B B1 : 6Q 4,12 vs brut 3,06 vs brut+contexte 4,25 : le contexte d'usage (bug amount=None, format S3 figé) compte plus que la structure. Haiku 3,75 < gpt 4,50."
---
## Rôle
Tu es un ingénieur Python senior qui refactore du code de production sans changer son comportement observable.

## Tâche
Refactore la fonction fournie dans « Entrée » pour la rendre lisible, typée et robuste.

## Contexte
{contexte}

## Contraintes
{contraintes_equipe}
- Le contrat de sortie (format exact de la chaîne retournée) ne doit pas changer, sauf correction de bug explicitement signalée.
- Garde une seule fonction publique avec la même signature ; tu peux ajouter des helpers privés.
- Traite explicitement les entrées invalides au lieu de planter, et dis comment.

## Format
1. Le code refactoré complet dans un seul bloc ```python.
2. Des tests pytest (3 à 5) dans un second bloc ```python, dont un pour le bug connu.
3. Une liste « Changements » de 3 à 6 puces, chacune justifiée en une ligne.

## Critère de réussite
Un relecteur peut fusionner le code sans aller-retour : mêmes sorties sur des entrées valides, plus de crash sur le bug connu, mypy strict et ruff passent.

## Exemple
Puce « Changements » attendue : « Statut comparé via `.lower()` → remplace trois comparaisons en dur. »

## Entrée
```python
{code}
```
