# Phase 1 — Cadrage produit

**Statut :** terminée

**Livrable :** Product brief validé par l'équipe

**Dépendance suivante :** Phase 2 — Données

## 1. Objectif de la phase

Figer ce que le produit doit résoudre, pour qui, avec quelles entrées et quelles sorties, avant de produire les données ou d'implémenter le moteur de recommandation.

À la fin de cette phase, l'équipe doit partager une définition commune du MVP et pouvoir décider si une fonctionnalité appartient ou non à la première version.

## 2. Problème utilisateur

Les investisseurs VC doivent explorer de nombreuses opportunités et tendances dans des secteurs variés. Les informations sont dispersées et le premier tri est chronophage. Une recherche trop large produit beaucoup de bruit ; une recherche trop étroite risque de masquer des opportunités pertinentes.

Le produit doit aider un VC à répondre à la question :

> Quelles idées de startups correspondent le mieux à mon domaine et à ma thèse d'investissement, et pourquoi méritent-elles mon attention ?

Le produit assiste l'exploration et la priorisation. Il ne remplace pas la due diligence et ne prend aucune décision d'investissement.

## 3. Persona principal — validé

### VC Associate / Analyst

- travaille dans un fonds seed ou early stage ;
- recherche de nouvelles opportunités dans un ou plusieurs domaines ;
- doit préparer une première sélection pour l'équipe d'investissement ;
- dispose de peu de temps pour analyser chaque piste ;
- souhaite comprendre pourquoi une opportunité est recommandée ;
- doit pouvoir vérifier les informations et identifier rapidement les risques.

### Job-to-be-done

> Lorsque je recherche des opportunités dans un secteur, je veux obtenir rapidement une sélection pertinente et expliquée afin de décider quelles idées méritent une analyse plus approfondie.

## 4. Proposition de valeur

Le **VC Startup Opportunity Finder** transforme une thèse d'investissement en une sélection adaptative d'idées de startups pertinentes, classées et expliquées.

La valeur apportée repose sur quatre éléments :

1. **personnalisation** selon les préférences du VC ;
2. **gain de temps** grâce au filtrage et au classement ;
3. **explicabilité** avec raisons, risques et questions à vérifier ;
4. **traçabilité** : les recommandations restent fondées sur les données disponibles.

## 5. Entrées du MVP

### Champ obligatoire

| Champ | Type | Exemple |
|---|---|---|
| Domaine | Liste contrôlée | `climate-tech` |

### Champs facultatifs validés pour la V1

| Champ | Type | Exemple |
|---|---|---|
| Stade | Liste contrôlée | `pre-seed` |
| Géographie | Liste contrôlée | `Europe` |
| Business model | Liste contrôlée | `B2B SaaS` |
| Appétence au risque | Faible / moyenne / forte | `medium` |
| Mots-clés | Liste de textes | `energy`, `buildings` |
| Langue de restitution | Français / anglais | `fr` |

Un champ facultatif vide ne doit jamais éliminer une idée.

La langue sélectionnée modifie les textes de l'interface et les explications générées, mais jamais les filtres, les notes ou le classement. L'anglais est utilisé par défaut si aucune préférence n'est fournie.

## 6. Sorties du MVP

Le nombre de recommandations dépend du nombre d'idées compatibles après filtrage :

```python
if candidate_count <= 50:
    result_count = min(5, candidate_count)
else:
    result_count = min(50, ceil(candidate_count * 0.10))
```

La V1 retourne donc au maximum cinq résultats tant que le catalogue filtré contient 50 idées ou moins. Au-delà, elle retourne le top 10 %, avec un plafond absolu de 50 résultats. L'interface affiche d'abord les cinq meilleures recommandations et permet d'ouvrir la shortlist complète.

Chaque fiche contient :

- le rang et le score total ;
- le nom et le résumé de l'idée ;
- le domaine et le sous-domaine ;
- les critères correspondant à la thèse du VC ;
- les raisons de la recommandation ;
- les principaux risques ;
- les informations manquantes ;
- les questions à vérifier avant une analyse plus approfondie.

Si moins de cinq idées satisfont les filtres, le produit affiche uniquement les résultats valides et explique pourquoi la liste est incomplète.

### Grille de scoring validée

| Critère | Maximum |
|---|---:|
| Adéquation à la thèse du VC | 25 |
| Pertinence du problème traité | 20 |
| Potentiel de marché | 20 |
| Différenciation | 15 |
| Faisabilité | 10 |
| Cohérence du business model | 10 |

Le LLM produit les notes par critère avec leurs justifications. Le score total sur 100 est systématiquement recalculé dans le code afin d'éviter tout total incohérent.

## 7. Parcours utilisateur du MVP

```text
Choisir un domaine
        ↓
Préciser des préférences facultatives
        ↓
Lancer la recherche
        ↓
Filtrer et analyser les idées compatibles
        ↓
Afficher la sélection expliquée
        ↓
Consulter une fiche ou modifier les critères
```

## 8. Fonctionnalités incluses

- formulaire de recherche VC ;
- filtrage déterministe sur les critères explicites ;
- analyse structurée des idées présélectionnées ;
- scoring sur 100 calculé dans le code ;
- classement et génération d'une sélection adaptative ;
- explications, risques et questions à valider ;
- gestion des résultats vides et des erreurs LLM ;
- tracing Langfuse ;
- démonstration dans le notebook ;
- interface Streamlit après validation du pipeline.

## 9. Fonctionnalités hors périmètre

- comptes utilisateurs et authentification ;
- paiement ou abonnement ;
- recommandations financières automatisées ;
- prédiction du rendement d'un investissement ;
- scraping de plateformes privées ;
- traitement de données ou de decks confidentiels ;
- base de données de production en temps réel ;
- prise de contact automatique avec une startup.

### Évolution envisagée en V2

Connecter le produit à des canaux autorisés fournissant de vrais pitchs ou profils de startups. Cette évolution nécessitera de documenter les droits d'utilisation, la fraîcheur des données, la confidentialité et les règles de mise à jour.

## 10. Critères de succès validés pour la V1

| Critère | Seuil MVP proposé |
|---|---:|
| Respect des filtres obligatoires | 100 % |
| Sorties structurées valides | ≥ 95 % |
| Precision@5 sur les requêtes test | ≥ 70 % |
| Affirmations soutenues par les données | ≥ 90 % |
| Utilité des explications, évaluation humaine | ≥ 4/5 |
| Requêtes traitées sans erreur bloquante | ≥ 95 % |
| Latence médiane d'une recherche | ≤ 15 secondes |

Les tests d'acceptation doivent inclure des requêtes et des restitutions en français et en anglais.

Le MVP est réussi si le système fournit une sélection utile et explicable de manière répétable. Le nombre d'idées générées n'est pas, à lui seul, une mesure de qualité.

### Configuration LLM validée

- moteur d'exécution : Ollama local ;
- modèle initial : `deepseek-r1:8b` ;
- coût API attendu en local : 0 € ;
- sortie contrainte par un schéma Pydantic/JSON ;
- température : 0 pour favoriser la reproductibilité.

Le modèle pourra être remplacé s'il n'atteint pas les critères de succès, sans transformer le projet en benchmark de modèles.

## 11. Risques produit identifiés

| Risque | Réponse prévue |
|---|---|
| Idées génériques ou trop similaires | Déduplication et contrôle de diversité |
| Hallucination de données marché ou traction | Interdiction d'inventer et contrôle de groundedness |
| Score perçu comme une vérité objective | Afficher les critères, limites et preuves |
| Recommandations biaisées par le dataset | Couverture équilibrée et dataset card |
| Filtres trop stricts donnant zéro résultat | Message explicite et suggestion d'élargissement |
| Contenu malveillant dans les données | Considérer les idées comme données non fiables |
| Dataset synthétique peu représentatif | Revue humaine et limite documentée |

## 12. Décisions à valider en équipe

- [x] Le persona principal est un VC Associate / Analyst en fonds seed ou early stage.
- [x] Les six domaines de la V1 sont confirmés : climate tech, fintech, healthtech, edtech, retail/e-commerce et future of work/productivity.
- [x] La V1 recommande uniquement des idées fictives générées puis validées humainement ; les pitchs réels sont reportés à la V2.
- [x] Les champs facultatifs de la V1 sont le stade, la géographie, le business model, l'appétence au risque et les mots-clés.
- [x] La sélection contient jusqu'à 5 résultats pour 50 candidates ou moins, puis le top 10 % avec un plafond de 50 résultats.
- [x] La grille de scoring sur 100 et ses pondérations sont validées.
- [x] Les seuils de succès de la section 10 sont validés pour la V1.
- [x] La V1 est bilingue français/anglais avec un sélecteur de langue ; l'anglais est la valeur par défaut.
- [x] La V1 utilise Ollama local avec `deepseek-r1:8b` comme modèle initial.

## 13. Validation de la phase

La phase 1 est terminée lorsque :

- [x] le persona et le problème sont validés ;
- [x] les entrées et sorties du MVP sont figées ;
- [x] le parcours utilisateur est validé ;
- [x] le périmètre et le hors-périmètre sont acceptés ;
- [x] les critères de succès sont chiffrés ;
- [x] les décisions de la section précédente sont renseignées ;
- [x] un membre autre que l'auteur a relu le document ;
- [x] les décisions finales ont été reportées dans `docs/PROTOCOL.md`.

## 14. Prochaine étape après validation

Transmettre à la phase 2 :

1. la liste définitive des domaines ;
2. les champs obligatoires du dataset ;
3. les valeurs contrôlées utilisées par les filtres ;
4. la grille de scoring ;
5. les cas limites que les données doivent couvrir.

La génération complète des données ne doit commencer qu'après validation de ces éléments.
