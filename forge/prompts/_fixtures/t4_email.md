# Contexte : incident et demande à envoyer

- Expéditeur : Mériadec Finoude, lead tech de l'équipe Plateforme Data.
- Destinataire : Claire Vasseur, responsable SRE chez notre hébergeur cloud (relation cordiale, vouvoiement).
- Incident : le mardi 27 octobre 2026, entre 14h05 et 15h40 (heure de Paris), notre cluster Kubernetes `prod-eu-1` a perdu 3 nœuds sur 8 dans la zone eu-west-3b. Les pods de l'API de scoring ont été replanifiés mais 2 volumes persistants (PV) sont restés bloqués en état "Attaching" pendant 82 minutes.
- Impact : 18 % des requêtes API en erreur 503 pendant 1h35 ; SLA client à 99,9 % mensuel désormais menacé (budget d'erreur consommé à 74 %).
- Ticket hébergeur : #INC-48213, ouvert à 14h12, première réponse à 15h55 (après résolution).
- Ce qu'on demande : (1) un post-mortem écrit côté hébergeur d'ici le 6 novembre ; (2) l'explication du blocage "Attaching" des volumes ; (3) savoir si un crédit SLA est applicable ; (4) un appel de 30 min la semaine prochaine (dispo : mardi 3/11 10h–12h ou jeudi 5/11 14h–17h).
- Ce qu'on a déjà fait de notre côté : ajout d'une anti-affinité de zone, alerte sur PV > 5 min en "Attaching".
- Ton souhaité : ferme mais collaboratif, factuel, pas d'accusation ; max ~200 mots.
