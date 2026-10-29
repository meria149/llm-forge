# SPARQ : Sparse Retrieval-Augmented Quantized Inference for Long-Context LLMs
*Prépublication fictive — L. Marchetti, A. Okafor, Y. Tanaka (Institut Hélion, 2026)*

## Résumé
Les modèles de langage à long contexte (128k–1M jetons) souffrent d'un coût mémoire quadratique de l'attention et d'un cache clé-valeur (KV) qui croît linéairement avec la longueur. Nous proposons SPARQ, une méthode qui combine (1) une récupération éparse des blocs de cache KV pertinents via un index de signatures binaires de 64 bits par bloc de 256 jetons, et (2) une quantification adaptative du cache en 4 bits pour les blocs « froids » et 8 bits pour les blocs « chauds ». Sur LongBench-v3 et RULER-256k, SPARQ réduit la mémoire du cache KV de 71 % et la latence de décodage de 38 % par rapport à l'attention dense FP16, pour une perte moyenne de 0,9 point d'exactitude (de 62,4 à 61,5).

## 1. Motivation
Le cache KV d'un modèle de 70 B paramètres à 256k jetons occupe environ 80 Go en FP16, soit plus qu'un GPU H100. Les approches existantes — fenêtres glissantes (perte d'information lointaine), H2O (heuristique d'éviction par score d'attention cumulé), et quantification uniforme KIVI (2 bits, perte notable sur les tâches de récupération d'aiguille) — font chacune un compromis rigide.

## 2. Méthode
- **Signatures de blocs** : chaque bloc de 256 jetons reçoit une signature SimHash de 64 bits calculée sur la moyenne des clés de la couche 12. Coût : 0,02 % de la mémoire du cache.
- **Récupération** : à chaque pas de décodage, la requête courante est hachée ; on récupère les k = 32 blocs les plus proches (distance de Hamming) plus les 4 blocs les plus récents. L'attention n'est calculée que sur ces 36 blocs (~9 200 jetons).
- **Quantification adaptative** : un bloc récupéré ≥ 3 fois dans les 512 derniers pas est « chaud » (INT8), sinon « froid » (INT4 par groupe de 32, échelle FP16).
- **Re-calibration** : toutes les 4 096 étapes, les signatures sont recalculées pour les blocs chauds.

## 3. Expériences
Modèles : Llama-3.1-70B et Qwen2.5-32B. Matériel : 2×H100 80 Go.

| Méthode | Mémoire KV | Latence/jeton | LongBench-v3 | RULER-256k |
|---|---|---|---|---|
| Dense FP16 | 100 % | 100 % | 62,4 | 71,8 |
| H2O | 35 % | 70 % | 57,1 | 54,3 |
| KIVI-2bit | 14 % | 81 % | 59,8 | 63,0 |
| **SPARQ** | **29 %** | **62 %** | **61,5** | **70,2** |

Ablation : sans quantification adaptative (tout en INT4), RULER tombe à 66,1 ; sans les 4 blocs récents, LongBench tombe à 58,9 ; k = 16 au lieu de 32 réduit la latence de 9 % supplémentaires mais coûte 2,7 points sur RULER.

## 4. Limites
- Les signatures calculées sur une seule couche (12) peuvent manquer des dépendances propres aux couches profondes ; une variante multi-couches est laissée pour travaux futurs.
- Le gain de latence disparaît sous 16k jetons (surcoût d'indexation).
- Pas d'évaluation sur des tâches de code ni en batch > 8.
- Le noyau CUDA n'est pas encore publié ; les chiffres de latence viennent d'une implémentation Triton.

## 5. Conclusion
SPARQ montre qu'une récupération éparse bon marché, couplée à une précision adaptative, conserve 98,6 % de la qualité dense avec moins d'un tiers de la mémoire. Code annoncé sous licence Apache-2.0.
