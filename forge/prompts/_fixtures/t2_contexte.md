Contexte de la demande (notes en vrac) :
- Fonction héritée dans utils/report.py, appelée par le job nocturne de facturation.
- d = liste de factures (dicts) lues depuis l'API interne type Stripe, environ 50 000 par nuit ; t = mois "AAAA-MM" optionnel pour filtrer ; f = appliquer la TVA 20 % (France).
- Le résultat (chaîne JSON) est écrit tel quel dans S3 et lu par un tableau de bord : le format de sortie NE DOIT PAS changer.
- Équipe : Python 3.11, mypy strict, ruff ; pas de nouvelles dépendances.
- Bug connu : certaines factures ont amount = None → crash TypeError la nuit. Il faut que ça ne plante plus.
- J'aimerais le code + quelques tests pytest + une liste courte de ce qui a changé et pourquoi.
