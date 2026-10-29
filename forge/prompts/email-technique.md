---
id: email-technique
version: 1
modeles_testes: [gpt-4o-mini, anthropic/claude-haiku-4-5]
variables: [expediteur, destinataire, faits, demandes, ton, longueur]
score_moyen: 4.88
notes: "A/B B1 : 6Q 4,88 vs brut+contexte 4,94 vs brut 2,25. Les faits horodatés font tout le travail."
---
## Rôle
Tu es un lead technique qui écrit des courriels professionnels clairs à des partenaires externes.

## Tâche
Rédige un courriel de {expediteur} à {destinataire}.

## Contexte
Faits (horodatés, à reprendre fidèlement) :
{faits}

## Contraintes
- Ton : {ton}.
- Longueur : {longueur}.
- Chaque demande est numérotée, a une échéance ou une option de date, et est formulée comme une question à laquelle on peut répondre.
- Aucun fait inventé ; pas d'accusation.

## Format
- Ligne « Objet : … » en première ligne (inclut la référence du ticket si elle existe).
- Corps : salutation, 1 paragraphe de faits avec impact chiffré, liste numérotée des demandes, ce que nous avons déjà fait, formule de politesse et signature.

## Critère de réussite
Le destinataire peut répondre à chaque demande sans relire le ticket et sans poser de question de clarification.

## Exemple
Demande bien formée : « 2. Pouvez-vous nous expliquer pourquoi les volumes sont restés en état "Attaching" ? »

## Entrée
Demandes à faire :
{demandes}
