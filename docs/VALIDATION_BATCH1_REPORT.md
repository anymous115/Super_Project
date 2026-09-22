# Rapport de contrôle — lot 1 (P001 à P006)

**Date du contrôle : 22 septembre 2026**

**Branche : `data/pitches-batch-1`**

**Portée : contrôles mécaniques et vérification de l'existence des preuves, sans réévaluation des notes cibles.**

Ce rapport prépare la décision humaine demandée dans l'issue #8. Il ne valide pas les
pitchs à la place du relecteur : aucun score cible n'a été modifié et les six champs
`review_status` restent à `drafted`.

## Résultat synthétique

- les six pitchs respectent le plafond de 800 mots ;
- P004 ne contient aucun chiffre de revenu ;
- aucune coordonnée personnelle n'a été détectée ;
- les preuves factuelles citées dans `VALIDATION_BATCH1.md` existent dans les textes ;
- quatre formulations qualitatives de la fiche sont des interprétations et non des
  affirmations littérales des pitchs ;
- `python3 scripts/build_calibration.py` passe et tous les invariants sont respectés ;
- aucune décision n'a été prise sur P005 contre P006 ni sur le modèle frontier.

## 1. Contrôles mécaniques

### Longueur

| Pitch | Société | Nombre de mots | Plafond respecté |
|---|---|---:|:---:|
| P001 | Pyrolane | 558 | oui |
| P002 | Minth | 516 | oui |
| P003 | Vessa | 574 | oui |
| P004 | Boardwise | 534 | oui |
| P005 | Driftwatch | 553 | oui |
| P006 | Remorq | 560 | oui |

Le comptage correspond à celui de `scripts/build_calibration.py`.

### Information volontairement absente dans P004

Le flag ␀ est respecté : aucun montant de revenu, ARR, MRR, chiffre d'affaires ou
volume facturé n'apparaît dans P004.

Les montants présents ne sont pas des revenus :

- `$2.1B` décrit la taille du marché ;
- `$90 per seat per month` est un prix catalogue ;
- `$9M` est le montant de la levée recherchée.

Le texte mentionne trois pilotes payants, mais ne donne aucun revenu associé.

### Identités et coordonnées

Aucune adresse e-mail, URL personnelle ou professionnelle, numéro de téléphone ou
autre coordonnée n'a été détecté dans les six `pitch_text`.

Les recherches publiques effectuées sur les paires nom/société n'ont fait ressortir
aucune association entre les douze noms du corpus et les six sociétés fictives.
Ce contrôle ne constitue cependant pas une preuve exhaustive qu'aucun homonyme réel
n'existe.

Limite importante : `source_url` et `accessed_at` sont vides pour P001 à P006. On ne
peut donc pas vérifier automatiquement, source par source, que chaque nom de fondateur
a bien été remplacé. Ces champs vides constituent un écart par rapport à la checklist
de `PITCH_TEMPLATE.md`.

### Génération et invariants

Commande exécutée :

```bash
python3 scripts/build_calibration.py
```

Résultat : succès, avec 50 pitchs, 12 forts, 26 moyens, 12 faibles, 21 secteurs et la
coupure P005 (79) / P006 (78). Le script indique `invariants respectés` et laisse
`data/pitches.jsonl` intact.

## 2. Vérification des preuves citées

La colonne « Résultat » répond uniquement à deux questions : la preuve est-elle dans
le pitch, et dit-elle bien ce que la fiche lui attribue ? Elle ne juge pas la note.

### P001 — Pyrolane

| Critère | Résultat |
|---|---|
| Équipe | **Oui, exact.** Les 12 ans, le top-3, les 3 ans sur un reformeur de 400 t/jour, les 2 usines et les 3 brevets sur le *carbon deposition control* sont présents. |
| Marché | **Oui, exact.** `€140B`, segment de `€19B`, pénalités supérieures à `€80/t` et coût livré inférieur à l'hydrogène gris avant comptabilité carbone. |
| Produit | **Oui, exact.** `14 kWh/kg` contre `50–55`, activité au-delà de 900 h contre 200 h et quatre brevets accordés. |
| Traction | **Oui, exact.** Depuis mars, 1 400 h, 62 kg/jour à 99,7 %, deux offtakes non contraignants, €4,2 M de subventions et pré-revenu hydrogène. |
| Business model | **Oui, exact.** Deux revenus et carbone solide couvrant environ 30 % du coût, avec la phrase sur l'économie sans subvention. |

### P002 — Minth

| Critère | Résultat |
|---|---|
| Équipe | **Preuves factuelles présentes.** Huit ans dans les paiements, règlement dans 19 pays et deux produits passés en approbation. « Sans le relief qui ferait un 5 » est une appréciation de la fiche, pas une phrase du pitch. |
| Marché | **Oui, exact.** `$40T`, environ 40 000 entreprises et seuil de flux supérieur à `$20M/an`. |
| Produit | **Oui, exact.** Environ 10 jours contre 12 mois, conservation de la marque et de la politique de trésorerie, aucune primitive blockchain manipulée. |
| Traction | **Oui, exact.** 9 clients, `$2.1B` contre `$310M`, NRR 164 % et zéro déficit de réserve sur 14 attestations. |
| Business model | **Oui, exact.** 3 points de base, `$4,000/mois`, `$7.1M` annualisés, marge brute 71 % et coût marginal presque plat. |

### P003 — Vessa

| Critère | Résultat |
|---|---|
| Équipe | **Preuves factuelles présentes.** Opérations d'un groupe de 40 sites et direction d'une équipe grounding/retrieval. « Sans exploit » est une appréciation externe au texte. |
| Marché | **Oui, exact.** `$12B`, 31 000 organisations de 5 à 60 praticiens, avec la justification « large enough… small enough… ». |
| Produit | **Oui, exact.** Intégration au niveau de la prescription, certification sur trois EHR et reconnaissance explicite de la concurrence. |
| Traction | **Oui, exact.** 61 organisations, 840 praticiens, 17,4 % vers 11,9 %, 74 % sans humain et NRR 121 %. |
| Business model | **Oui, exact.** `$340/praticien/mois`, `$3.4M ARR`, marge 54 % vers 68 % et expansion par le nombre de praticiens. |

### P004 — Boardwise

| Critère | Résultat |
|---|---|
| Équipe | **Oui, exact.** Neuf ans, quatre comme firmware lead, plus de 40 M d'unités, pile de sondes de debug et ferme construite dans le garage avant incorporation. |
| Marché | **Oui, exact.** 1,4 M de développeurs, `$2.1B` et reconnaissance que ce marché est petit face au tooling logiciel général. |
| Produit | **Oui, exact.** Matériel réel, 23 familles, lecture des registres et barrière de 18 mois qui « does not look like AI ». |
| Traction | **Oui, exact.** 2 100 utilisateurs ayant lancé un build, 340 hebdomadaires et trois pilotes payants. L'absence de chiffre de revenu est réelle. |
| Business model | **Oui, exact.** `$90/siège/mois`, offre entreprise et formulation prudente sur un échantillon limité à trois pilotes. |

### P005 — Driftwatch

| Critère | Résultat |
|---|---|
| Équipe | **Oui, exact.** Le texte dit explicitement qu'aucun fondateur ne vient de la sécurité et que l'avantage est en ingénierie système, non en threat research. |
| Marché | **Oui, exact.** `$4.8B`, environ 20 % de croissance et marché décrit comme encombré et en consolidation. |
| Produit | **Oui, exact.** eBPF, sans sidecar ni changement de code, réduction de 80–90 %, détection de dérive et overhead publié inférieur à 1 %. |
| Traction | **Oui, exact.** 43 clients, quatre à plus de 10 000 conteneurs, `$2.8M ARR`, +9 %/mois et rétention logo 95 %. |
| Business model | **Oui, exact.** `$65k ACV`, marge 79 % et environ un cinquième des clients variant de plus de 20 % mensuellement. |

### P006 — Remorq

| Critère | Résultat |
|---|---|
| Équipe | **Oui, exact.** Neuf ans, 1 200 départs quotidiens, optimisation dans 11 pays et 18 mois de collaboration avant incorporation. |
| Marché | **Présent avec une nuance.** `€38B`, `€14B` et justification par la densité géographique sont explicites. Le caractère disputé est étayé par les incumbents et plateformes concurrentes ; le mot « mature » n'apparaît pas. |
| Produit | **Oui, exact.** Le texte dit ne pas revendiquer une technologie inattaquable et place l'avance dans la densité du carnet. |
| Traction | **Chiffres exacts.** `€4.1M`, +11 %/mois, 71 % de rétention et 84 % contre 63 %. « Volume absolu modeste » est une interprétation de la fiche, pas une affirmation du pitch. |
| Business model | **Oui, exact.** 14 % brut, 6,2 points après coûts, marge dite mince et non démontrée au-delà de trois corridors. |

### Nuances relevées

Quatre formulations qualitatives ne sont pas littérales, même si leurs éléments
factuels existent :

1. P002 équipe : « sans le relief qui ferait un 5 » ;
2. P003 équipe : « sans exploit » ;
3. P006 marché : « marché mature » ;
4. P006 traction : « volume absolu modeste ».

Ces observations ne changent aucune cible. Si elles sont jugées insuffisamment
étayées, le protocole impose de corriger le texte, pas la note.

## 3. Lecture en regard — P005 contre P006

Le texte canonique complet reste dans `data/pitches.jsonl`. Le tableau ci-dessous
aligne les éléments à comparer sans produire de verdict automatique.

| Section | P005 — Driftwatch | P006 — Remorq |
|---|---|---|
| Problème | Trop d'alertes statiques, peu reliées à ce qui s'exécute réellement. | Camions vides ou sous-remplis, groupage lent et générateur de dommages. |
| Solution | Observation runtime par eBPF, sans sidecar ni modification du code ; suppression de 80–90 % de la file et détection de dérive. | Mutualisation de palettes sans hub ; constitution en moins de deux minutes de routes à deux ou trois arrêts. |
| Marché | `$4.8B`, environ +20 %/an, marché encombré et en consolidation. | `€38B`, dont `€14B` sur les premières zones à forte densité. |
| Concurrence / avantage | Contexte runtime profond, corrélation scan/exécution, overhead publié inférieur à 1 %. | Technologie non inimitable ; avantage revendiqué par la densité du carnet sur les corridors. |
| Équipe | Deux ingénieurs plateforme sans passé sécurité ; deux spécialistes détection recrutés pour combler ce manque. | Neuf ans d'opérations groupage à 1 200 départs/jour et optimisation d'itinéraires dans 11 pays ; 18 mois de travail commun. |
| Traction | 43 clients ; `$2.8M ARR` ; +9 %/mois ; rétention logo 95 %. | `€4.1M` facturés ; +11 %/mois ; rétention 71 % ; remplissage 84 % contre 63 %. |
| Business model | `$65k ACV`, marge brute 79 % ; variabilité mensuelle supérieure à 20 % chez environ un cinquième des clients. | Take rate brut 14 %, 6,2 points après coûts ; marge mince et non démontrée au-delà de trois corridors. |
| Go-to-market | Open source puis conversion commerciale ; cycle de 11 à 20 semaines. | Vente directe ; cycle de 7 semaines ; CAC `€2,100`, remboursé en 4,5 mois. |
| Besoin de financement | `$14M` pour contenu de détection, threat research et certifications. | `€6M` pour trois corridors, opérations et industrialisation du matching. |

Question laissée au relecteur humain : **les deux dossiers sont-ils quasi
équivalents, avec Driftwatch très légèrement devant ?**

## 4. Modèles frontier candidats

Tarifs API standard par million de tokens, vérifiés le **22 septembre 2026**.
Aucun modèle Anthropic n'est proposé, puisque le corpus a été rédigé par Claude.

| Modèle | Entrée | Sortie | Coût estimé pour 450 appels | Remarque |
|---|---:|---:|---:|---|
| OpenAI `gpt-6-astra` | $10 | $50 | environ **$17.10** | Candidat plafond de qualité ; l'OpenAI Docs le présente comme son modèle le plus intelligent. |
| Google `gemini-3.1-pro-preview` | $2 | $12 | environ **$3.78** | Contrepoint inter-fournisseur ; l'identifiant et la date doivent être figés à cause du statut Preview. |
| xAI `grok-4.7` | $2 | $6 | environ **$2.70** | Modèle flagship xAI et option la moins chère des trois. |

Estimation calculée avec l'hypothèse de `CALIBRATION_GRID.md` : 810 k tokens
d'entrée et 180 k de sortie pour la part frontier, sans cache ni outils externes.
Pour Gemini, les tokens de raisonnement sont facturés comme tokens de sortie et
peuvent augmenter la consommation réelle.

Sources officielles, consultées le 22 septembre 2026 :

- [OpenAI — API pricing](https://developers.openai.com/api/docs/pricing) ;
- [OpenAI — latest model guide](https://developers.openai.com/api/docs/guides/latest-model) ;
- [Google — Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) ;
- [xAI — models and pricing](https://docs.x.ai/developers/models).

## 5. Décisions encore requises

L'issue ne peut pas être considérée comme validée tant que le responsable humain
n'a pas :

1. confirmé ou refusé que P005 et P006 sont quasi équivalents, avec P005 très
   légèrement devant ;
2. choisi le modèle frontier à documenter pour le benchmark.

Après ces décisions seulement, les six `review_status` pourront être passés de
`drafted` à `validated`, puis le générateur pourra être relancé.
