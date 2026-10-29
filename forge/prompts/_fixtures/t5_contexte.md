Contexte de la demande (notes en vrac) :
- Je dois charger les projets de cette page dans notre tableur de suivi via un script Python qui valide avec Pydantic ; si le JSON ne parse pas, le script plante.
- Un objet par projet, clé racine "projets". Champs : nom, responsable (nom sans titre Dr/M./Mme), statut parmi en_cours / en_pause / termine, budget_alloue_eur et budget_consomme_eur (entiers, en euros), etp (nombre), prochain_jalon (texte ou null), date_prochain_jalon (AAAA-MM-JJ ou null si pas de date précise), risque_principal (texte ou null si aucun).
- Ignorer les en-têtes de page répétés et les frais transverses. JSON seulement, rien d'autre, c'est lu par une machine.
