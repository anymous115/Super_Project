# Phase 1 — Cadrage produit

**Statut :** à revalider — voir §12
**Livrable :** product brief validé par l'équipe
**Dépendance suivante :** Phase 2 — Données

> **Historique.** Ce brief a d'abord été rédigé pour une variante « VC Startup Opportunity Finder » (catalogue d'idées interrogé par le VC). L'équipe a retenu le sens inverse : le **tri de pitchs entrants**.
>
> Le document est adapté, pas refait. Le persona, la table des risques, la configuration LLM, la sélection adaptative et le bilinguisme sont **conservés tels quels**. Ce qui change est signalé au §12, avec les cases à revalider.

## 1. Objectif de la phase

Figer ce que le produit résout, pour qui, avec quelles entrées et quelles sorties, avant de produire les données ou d'implémenter le moteur.

À la fin de cette phase, l'équipe partage une définition commune du MVP et peut décider si une fonctionnalité appartient ou non à la première version.

## 2. Problème utilisateur

Un fonds reçoit des centaines de pitchs par mois, dispersés entre email, Telegram et messages directs. La majorité ne sera jamais lue, et l'ordre de lecture dépend surtout du hasard : qui a écrit le plus récemment, qui a un contact commun, qui a le meilleur objet de mail.

Le produit doit aider un VC à répondre à :

> Parmi tout ce que j'ai reçu, qu'est-ce qui mérite mon attention en priorité, et pourquoi ?

Le produit assiste le tri et la priorisation. Il ne remplace ni la due diligence ni la décision d'investissement.

## 3. Persona

### Principal — VC Associate / Analyst *(inchangé)*

- travaille dans un fonds seed ou early stage ;
- doit préparer une première sélection pour l'équipe d'investissement ;
- dispose de peu de temps pour analyser chaque piste ;
- souhaite comprendre pourquoi un dossier est remonté ;
- doit pouvoir vérifier les informations et identifier rapidement les risques.

**Job-to-be-done** — revu pour le flux entrant :

> Lorsque des pitchs arrivent en continu, je veux que les meilleurs remontent en haut de ma file avec une justification vérifiable, afin de décider lesquels méritent une analyse approfondie.

### Secondaire — le fondateur qui soumet

Nouveau dans cette version, puisque le flux est entrant.

- envoie son dossier par le canal qui lui est le plus naturel ;
- ne connaît pas la grille d'évaluation ;
- attend au minimum un accusé de réception.

## 4. Proposition de valeur

Le produit transforme un flux désordonné de pitchs en une file triée et expliquée.

1. **centralisation** — un seul endroit pour plusieurs canaux ;
2. **équité de traitement** — la même grille appliquée à tous les dossiers, pas seulement à ceux qui viennent d'un contact ;
3. **gain de temps** — le haut du panier remonte seul ;
4. **traçabilité** — chaque note est justifiée par un extrait du pitch.

Le point 2 est le plus défendable devant un jury : aujourd'hui, un dossier sans introduction chaude n'est souvent pas lu du tout.

## 5. Entrées du MVP

### Soumission d'un pitch

| Champ | Type | Exemple |
|---|---|---|
| Canal | `telegram` / `email` | `telegram` |
| Texte | Texte libre | contenu du message |
| Pièces jointes | Liste de fichiers | `deck.pdf` |
| Liens | Liste d'URL | `https://…` |

Les canaux Instagram et X sont documentés mais hors périmètre — App Review Meta et API payante.

### Préférences du VC pour la file

| Champ | Type | Exemple |
|---|---|---|
| Secteur | Liste contrôlée | `climate-tech` |
| Stade | Liste contrôlée | `pre-seed` |
| Géographie | Liste contrôlée | `Europe` |
| Business model | Liste contrôlée | `B2B SaaS` |
| Langue de restitution | Français / anglais | `fr` |

Un champ vide ne filtre rien.

> **Le filtrage et le scoring sont deux étages distincts.** Le score d'un pitch ne dépend jamais des préférences du VC : le même dossier obtient la même note pour tout le monde. Les préférences filtrent la file, elles ne modifient pas la notation.
>
> C'est pourquoi le critère « adéquation à la thèse » de la version précédente n'a plus de place dans la grille : il n'y a pas de requête à laquelle se comparer au moment de noter. Il réapparaîtra à l'étage filtrage, alimenté par l'extraction de profil (issue #3).

La langue modifie les textes de l'interface et les explications générées, jamais les notes ni le classement. L'anglais est la valeur par défaut.

## 6. Sorties du MVP

### Sélection adaptative *(conservée)*

```python
if candidate_count <= 50:
    result_count = min(5, candidate_count)
else:
    result_count = min(50, ceil(candidate_count * 0.10))
```

Cinq dossiers tant que la file contient 50 pitchs ou moins, puis le top 10 %, plafonné à 50. L'interface affiche d'abord les cinq premiers et permet d'ouvrir la liste complète.

Le plafond évite qu'un fonds recevant 2 000 pitchs se retrouve avec 200 dossiers remontés — soit exactement le problème de départ.

Si moins de cinq pitchs satisfont les filtres, le produit affiche les résultats valides et explique pourquoi la liste est incomplète.

### Grille de scoring — **modifiée**

| Critère | Poids |
|---|---:|
| Équipe | 20 |
| Marché | 25 |
| Produit | 15 |
| Traction | 25 |
| Business model | 15 |

Grille d'évaluation de dossier, et non de correspondance à une requête. C'est celle sur laquelle repose la calibration des 50 pitchs ([`docs/CALIBRATION_GRID.md`](../../docs/CALIBRATION_GRID.md)).

Le LLM produit les notes par critère avec leurs justifications. **Le total sur 100 est systématiquement recalculé dans le code.**

### Fiche d'un dossier

Rang et score · nom et résumé · secteur · notes par critère · forces · risques · informations manquantes · extraits du pitch justifiant chaque note · canal d'origine.

## 7. Parcours utilisateur

```text
FONDATEUR                          VC
    │                               │
 envoie son pitch                   │
 (Telegram / email)                 │
    │                               │
 accusé de réception                │
    │                               │
    └──► extraction ──► scoring ──► file triée
                                    │
                            consulte une fiche
                                    │
                            ajuste ses filtres
```

## 8. Fonctionnalités incluses

- ingestion Telegram et email, événement normalisé commun ;
- extraction depuis texte, PDF et lien ;
- analyse structurée validée par Pydantic ;
- scoring sur 100 recalculé dans le code ;
- classement et sélection adaptative ;
- explications, risques, informations manquantes et extraits justificatifs ;
- défense contre les instructions contenues dans les pitchs ;
- gestion des files vides et des erreurs LLM ;
- tracing Langfuse ;
- restitution bilingue français / anglais ;
- démonstration dans le notebook ;
- interface Streamlit après validation du pipeline.

## 9. Hors périmètre

- comptes utilisateurs et authentification ;
- paiement ou abonnement ;
- connecteurs Instagram, X et LinkedIn ;
- recommandation financière ou prédiction de rendement ;
- scraping de plateformes privées ;
- traitement de decks réels ou confidentiels ;
- base de données de production ;
- prise de contact automatique avec une startup.

### Évolutions envisagées

**Extraction de profil** (issue #3) — produire une fiche structurée par pitch. C'est ce qui alimenterait un filtrage par thèse d'investissement, et ce qui permet la déduplication dès que deux canaux tournent en parallèle.

**Catalogue explorable** — une fois l'extraction en place, la file de pitchs devient interrogeable par thèse, ce qui rejoint la proposition Opportunity Finder mais sur un corpus réel au lieu d'un catalogue inventé.

## 10. Critères de succès pour la V1

| Critère | Seuil MVP |
|---|---:|
| Sorties structurées valides | ≥ 95 % |
| MAE sur le score total | ≤ 10 points |
| Corrélation de Spearman sur les 50 pitchs | ≥ 0,75 |
| Chevauchement du top 5 avec la référence | ≥ 60 % |
| Affirmations soutenues par le pitch | ≥ 90 % |
| Réussite des injections après défense V2 | 0 % |
| Pitchs traités sans erreur bloquante | ≥ 95 % |
| Latence médiane par pitch | ≤ 15 secondes |

Les tests d'acceptation incluent des pitchs et des restitutions en français et en anglais.

Le MVP est réussi si la file remonte de façon répétable les dossiers que des humains auraient retenus. Le volume traité n'est pas, à lui seul, une mesure de qualité.

### Configuration LLM *(conservée)*

- moteur local : Ollama ;
- modèle initial : **`deepseek-r1:8b`** ;
- coût en local : 0 € ;
- sortie contrainte par schéma Pydantic ;
- température : 0.

Le modèle peut être remplacé s'il n'atteint pas les critères. La comparaison avec un modèle frontier reste au programme — c'est le volet P8 du cours — mais elle sert à décider ce qu'on met en production, pas à produire un benchmark pour lui-même.

## 11. Risques produit *(conservés, un ajout)*

| Risque | Réponse prévue |
|---|---|
| Hallucination de traction ou de taille de marché | Interdiction d'inventer, contrôle de groundedness |
| Score perçu comme une vérité objective | Afficher critères, limites et preuves |
| Recommandations biaisées par le dataset | Couverture équilibrée, dataset card |
| File vide après filtrage | Message explicite et suggestion d'élargissement |
| Contenu malveillant dans un pitch | Pitch traité comme donnée non fiable, défense V2 |
| Dataset fictif peu représentatif | Revue humaine, limite documentée |
| **Pitch illisible ou PDF corrompu** | Échec enregistré, jamais corrigé silencieusement |

Le sixième risque change de nature par rapport à la version précédente : le contenu ne vient plus de nous mais d'inconnus, par des canaux ouverts. La défense contre l'injection n'est plus théorique.

## 12. Décisions à valider en équipe

### Reprises de la version précédente

- [x] Le persona principal est un VC Associate / Analyst en fonds seed ou early stage.
- [x] La sélection contient jusqu'à 5 résultats pour 50 candidates ou moins, puis le top 10 % plafonné à 50.
- [x] La V1 est bilingue français / anglais, l'anglais par défaut.
- [x] **Le corpus des 50 pitchs est rédigé en anglais.** Le bilinguisme porte sur la restitution, pas sur l'entrée : un corpus mélangé ajouterait une variable non contrôlée.
- [x] La V1 utilise Ollama local avec `deepseek-r1:8b` comme modèle initial.
- [x] **Le modèle frontier du benchmark est `gpt-6-astra`.** Choisi sur l'axe qualité et non sur le prix — l'écart entre candidats représente ~14 $ sur tout le benchmark. Aucun modèle Anthropic n'est éligible puisque Claude rédige le corpus.
- [x] Le score total est recalculé dans le code.

### Modifiées — à revalider

- [ ] **Sens du flux** : pitchs entrants soumis par des fondateurs, et non catalogue d'idées exploré par le VC.
- [ ] **Grille de scoring** : 5 critères (équipe, marché, produit, traction, business model) au lieu de 6. « Adéquation à la thèse » passe à l'étage filtrage.
- [ ] **Données** : 50 pitchs calibrés au lieu de 60 idées sur 6 domaines. 37 dérivés de sociétés réelles, 13 synthétiques.
- [ ] **Canaux d'ingestion V1** : Telegram et email.
- [ ] **Charge d'annotation** : 100 évaluations, 25 par personne. C'est le poste le plus lourd du projet.

## 13. Validation de la phase

- [x] le persona et le problème sont validés ;
- [x] le parcours utilisateur est validé ;
- [x] les critères de succès sont chiffrés ;
- [ ] les entrées et sorties du MVP sont figées — dépend des cases du §12 ;
- [ ] le périmètre et le hors-périmètre sont acceptés ;
- [ ] les décisions modifiées sont tranchées ;
- [ ] un membre autre que l'auteur a relu cette version ;
- [x] les décisions retenues sont reportées dans `docs/PROTOCOL.md`.

## 14. Prochaine étape

Transmettre à la phase 2 :

1. la grille de scoring et ses pondérations ;
2. la règle de sélection adaptative ;
3. le volume et la calibration du jeu de données ;
4. les cas limites que les données doivent couvrir — injections, cas ambigus, informations absentes ;
5. la répartition de la rédaction et de l'annotation.

Les points 1 à 4 sont déjà instruits dans [`docs/CALIBRATION_GRID.md`](../../docs/CALIBRATION_GRID.md) et [`docs/SOURCING_CANDIDATES.md`](../../docs/SOURCING_CANDIDATES.md). La rédaction ne commence qu'une fois les cases du §12 tranchées.
