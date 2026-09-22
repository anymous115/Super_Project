# Protocole opérationnel — VC Startup Opportunity Finder

![Roadmap visuelle du projet](PROJECT_ROADMAP.png)

## 1. Vision du produit

Construire un outil fonctionnel qui aide un investisseur en venture capital à découvrir les idées de startups les plus pertinentes pour un domaine donné.

Le VC renseigne au minimum un secteur (`climate tech`, `fintech`, `healthtech`, etc.). Il peut ensuite préciser sa thèse d'investissement : stade, zone géographique, modèle économique, niveau de risque ou mots-clés. L'outil recherche les opportunités compatibles dans un catalogue, les analyse, les classe et présente une **sélection argumentée**.

La question centrale n'est donc plus « quel modèle est le meilleur ? », mais :

> **Comment transformer des données sur des idées de startups en recommandations utiles, explicables et personnalisées pour un VC ?**

Le nom historique du notebook `08_quality_vs_cost_benchmark.ipynb` est conservé pour garder le lien avec le projet 8 du cours. Son contenu devient le notebook principal de conception, d'expérimentation et de démonstration du produit.

## 2. Périmètre du MVP

### Inclus

- un jeu de données documenté d'idées de startups ;
- un formulaire décrivant la recherche du VC ;
- un filtrage par domaine et préférences ;
- une analyse structurée de chaque idée ;
- un score et un classement reproductibles ;
- une sélection adaptative accompagnée de justifications, risques et informations manquantes ;
- une évaluation de la qualité des recommandations ;
- le tracing des appels LLM avec Langfuse ;
- une interface simple, de préférence avec Streamlit ;
- un notebook exécutable de bout en bout.

### Hors périmètre de la première version

- recommander de vrais investissements ou promettre un rendement ;
- automatiser une décision d'investissement sans validation humaine ;
- scraper des plateformes privées ou contourner leurs conditions d'utilisation ;
- traiter des decks confidentiels sans autorisation ;
- créer une plateforme complète avec comptes, paiement et base de données de production.

## 3. Parcours utilisateur cible

1. Le VC sélectionne un domaine.
2. Il précise éventuellement son stade, sa géographie, son business model, son appétence au risque, ses mots-clés et la langue de restitution.
3. Le système filtre les idées non pertinentes.
4. Il analyse et score les candidates restantes avec une grille commune.
5. Il classe les idées et retourne une sélection dont la taille dépend du nombre de candidates compatibles.
6. Pour chaque recommandation, l'interface affiche le concept, les raisons du classement, les principaux risques et les informations à vérifier.
7. Le VC peut ouvrir une fiche détaillée ou modifier ses critères.

Le produit est un outil d'aide à l'exploration. Le score ne remplace jamais la due diligence d'un investisseur.

## 4. Entrées et sorties fonctionnelles

### Entrée minimale

```json
{
  "domain": "climate-tech"
}
```

### Entrée enrichie

```json
{
  "domain": "climate-tech",
  "stage": "pre-seed",
  "geography": "Europe",
  "business_model": "B2B SaaS",
  "risk_appetite": "medium",
  "keywords": ["energy", "buildings"],
  "language": "fr"
}
```

La langue de restitution accepte `fr` ou `en` et vaut `en` par défaut. Elle modifie l'interface et les explications, jamais les filtres, les scores ou le classement.

### Sortie d'une recommandation

```json
{
  "idea_id": "IDEA-001",
  "rank": 1,
  "name": "Building Energy Copilot",
  "domain": "climate-tech",
  "one_liner": "Un copilote qui réduit la consommation énergétique des bâtiments tertiaires.",
  "fit_score": 86,
  "scores": {
    "thesis_fit": 19,
    "problem_relevance": 17,
    "market_potential": 18,
    "differentiation": 14,
    "feasibility": 10,
    "business_model": 8
  },
  "why_recommended": ["..."],
  "risks": ["..."],
  "questions_to_validate": ["..."]
}
```

## 5. Stratégie de données

### 5.1 Baseline recommandée

Créer un dataset seed de **60 idées fictives**, avec 10 idées dans chacun de six domaines : climate tech, fintech, healthtech, edtech, retail/e-commerce et future of work/productivity.

Ce volume permet de construire et démontrer le produit sans dépendre immédiatement d'une API payante ou de données confidentielles. Il ne suffit pas à prouver une performance de production ; cette limite doit apparaître dans la présentation finale.

### 5.2 Sources autorisées

Les idées peuvent provenir de deux voies clairement identifiées dans les métadonnées :

1. **génération synthétique** avec un LLM, suivie d'une revue humaine ;
2. **sources publiques autorisées**, avec URL, date d'accès et licence ou conditions de réutilisation documentées.

Ne jamais présenter une idée synthétique comme une entreprise réelle. Ne pas copier de données privées, de coordonnées personnelles ou de contenus protégés sans autorisation.

La V1 utilise uniquement des idées fictives générées puis validées humainement. La connexion à des sources autorisées de pitchs ou profils réels est reportée à la V2.

### 5.3 Schéma d'une idée

Chaque ligne de `data/startup_ideas.jsonl` doit contenir :

```json
{
  "idea_id": "IDEA-001",
  "name": "Nom fictif",
  "domain": "climate-tech",
  "subdomain": "building-energy",
  "problem": "Problème observé",
  "solution": "Solution proposée",
  "target_customers": ["property managers"],
  "geography": ["Europe"],
  "stage": "idea",
  "business_model": "B2B SaaS",
  "technology": ["AI", "IoT"],
  "market_signals": ["..."],
  "differentiators": ["..."],
  "risks": ["..."],
  "source_type": "synthetic",
  "source_url": null,
  "review_status": "human_validated"
}
```

### 5.4 Protocole de génération et de contrôle

1. Générer un premier lot par domaine avec un prompt versionné.
2. Valider le JSON automatiquement.
3. Dédupliquer les idées par similarité sémantique et revue humaine.
4. Vérifier la cohérence domaine/problème/solution/business model.
5. Supprimer les affirmations chiffrées non sourcées.
6. Faire relire chaque idée par au moins un autre membre.
7. Figer la version `data-v1` avant l'évaluation finale.

Critères d'acceptation : 60 lignes valides, 6 domaines couverts, aucun doublon manifeste, aucune donnée confidentielle et 100 % des lignes revues humainement.

## 6. Moteur de recommandation

Le MVP adopte une approche hybride, plus fiable qu'un simple prompt demandant « donne-moi les meilleures idées ».

### Étape A — Filtrage déterministe

Filtrer le catalogue sur les critères explicites : domaine, géographie, stade et business model. L'appétence au risque et les mots-clés participent ensuite à la pertinence. Un critère non renseigné ne doit pas éliminer une idée.

### Étape B — Présélection par pertinence

Calculer une pertinence entre la requête et les idées. Pour la première version, une méthode simple et explicable est acceptable : correspondance des champs et mots-clés. Une recherche par embeddings pourra être ajoutée ensuite si elle améliore les résultats.

### Étape C — Analyse structurée par le LLM

Le LLM analyse uniquement les candidates présélectionnées et retourne un schéma Pydantic validé. Il doit utiliser les données fournies, signaler les informations absentes et ne pas inventer de traction ou de taille de marché.

### Étape D — Score final calculé dans le code

| Critère | Maximum | Rôle |
|---|---:|---|
| Adéquation à la thèse du VC | 25 | Correspondance avec les critères exprimés |
| Pertinence du problème | 20 | Importance et clarté du besoin traité |
| Potentiel de marché | 20 | Ampleur plausible de l'opportunité, sans chiffres inventés |
| Différenciation | 15 | Originalité et avantage défendable |
| Faisabilité | 10 | Réalisme technologique et opérationnel |
| Business model | 10 | Cohérence de la monétisation |

Le total sur 100 est recalculé dans le code, jamais accepté aveuglément depuis la réponse du modèle. En cas d'égalité, départager par `thesis_fit`, puis `problem_relevance`, puis `idea_id`.

### Étape E — Taille et explication de la sélection

La taille est calculée sur le nombre de candidates après filtrage :

```python
if candidate_count <= 50:
    result_count = min(5, candidate_count)
else:
    result_count = min(50, ceil(candidate_count * 0.10))
```

L'interface affiche les cinq premières recommandations, puis permet d'ouvrir la shortlist complète. Le plafond de 50 évite une liste inutilisable lorsque le catalogue devient très grand.

Chaque recommandation doit être traçable vers les champs de l'idée et les critères du VC. Une recommandation non justifiée ou fondée sur une information absente est considérée comme invalide.

## 7. Prompting et sorties structurées

Conserver au minimum trois versions de prompt afin de montrer une démarche de prompt engineering :

- **V0 — baseline** : demande simple de classement ;
- **V1 — structurée** : rôle, grille, schéma de sortie et interdiction d'inventer ;
- **V2 — produit** : personnalisation par thèse VC, preuves, risques, questions de validation et protection contre les instructions contenues dans les données.

La sortie est validée avec Pydantic. Les erreurs de format, champs manquants et scores hors limites sont enregistrés. Elles ne sont jamais corrigées manuellement et silencieusement.

Les prompts, versions, entrées, sorties, latences et erreurs sont tracés avec Langfuse. Les clés restent dans `.env` et ne sont jamais committées.

La V1 utilise **Ollama local avec `deepseek-r1:8b`** comme modèle initial, une température de 0 et des sorties contraintes par un schéma Pydantic/JSON. L'exécution locale n'entraîne aucun coût API. Le modèle pourra être remplacé s'il n'atteint pas les critères de succès, sans faire de la comparaison de modèles l'objectif du projet.

## 8. Travail à réaliser dans le notebook

Le notebook `08_quality_vs_cost_benchmark.ipynb` devient le livrable technique principal. Il doit être réécrit progressivement avec les sections suivantes :

1. présentation du problème et du MVP ;
2. installation, imports et configuration ;
3. chargement et contrôle du dataset ;
4. exploration des domaines et attributs ;
5. définition des schémas Pydantic ;
6. filtrage des idées selon une thèse VC ;
7. prompt V0 et premier résultat ;
8. prompt V1 structuré et scoring ;
9. prompt V2 produit et génération de la sélection adaptative ;
10. évaluation sur un jeu de requêtes test ;
11. visualisation des métriques et analyse d'erreurs ;
12. démonstration complète avec une requête utilisateur ;
13. conclusion, limites et prochaines étapes.

Le notebook ne doit pas dépendre des chemins `utils` et `eval` du repo du professeur. Le code réutilisable est progressivement extrait dans `src/`, puis importé par le notebook et l'interface.

## 9. Protocole d'évaluation produit

Le produit doit être évalué même s'il n'y a plus de comparaison entre deux modèles.

### Jeu de test

Créer au moins 12 requêtes représentant différents profils de VC : deux par domaine, dont des requêtes larges, précises et volontairement difficiles. Avant d'exécuter le système, deux membres définissent pour chaque requête les critères indispensables, 3 à 5 idées jugées pertinentes, les incompatibilités évidentes et une courte justification.

### Métriques minimales

- **Precision@5** : part des cinq recommandations jugées pertinentes ;
- **Recall@5** : part des idées de référence retrouvées dans le top 5 ;
- **respect des filtres** : domaine, géographie, stade et business model ;
- **validité structurée** : pourcentage de sorties Pydantic valides ;
- **groundedness** : pourcentage d'affirmations soutenues par les données ;
- **diversité** : absence de cinq idées quasi identiques ;
- **qualité des explications** : note humaine sur 5 ;
- **latence** : médiane et p95 ;
- **coût** : coût moyen par requête si l'API utilisée est payante.

### Tests essentiels

- domaine connu avec plusieurs résultats ;
- domaine sans résultat exact ;
- filtres contradictoires ;
- champs facultatifs absents ;
- données contenant une instruction malveillante ;
- erreur ou indisponibilité du LLM ;
- résultat vide après filtrage.

Une amélioration de prompt ou de pipeline n'est retenue que si elle améliore les métriques ou corrige un cas d'erreur documenté.

## 10. Interface fonctionnelle

Une fois le pipeline validé dans le notebook, créer une interface Streamlit contenant :

- un sélecteur de domaine ;
- des filtres facultatifs pour la thèse VC ;
- un bouton `Find opportunities` ;
- cinq cartes de recommandation affichées en priorité, avec accès à la shortlist complète ;
- le détail des scores, raisons, risques et questions à vérifier ;
- des messages clairs en cas d'absence de résultat ou d'erreur ;
- un avertissement indiquant qu'il s'agit d'une aide à la décision.

L'interface doit appeler les mêmes fonctions que le notebook. Il ne faut pas dupliquer la logique dans l'application.

## 11. Structure cible du dépôt

```text
Super_Project/
├── README.md
├── CONTEXT.md
├── .gitignore
├── .env.example
├── requirements.txt
├── 08_quality_vs_cost_benchmark.ipynb
├── app.py
├── data/
│   ├── startup_ideas.jsonl
│   ├── test_queries.jsonl
│   └── dataset_card.md
├── src/
│   ├── config.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── data_loader.py
│   ├── retrieval.py
│   ├── recommender.py
│   └── evaluation.py
├── results/
│   ├── recommendations.jsonl
│   ├── evaluation.csv
│   └── figures/
├── tests/
└── docs/
    ├── PROTOCOL.md
    └── PROJECT_ROADMAP.png
```

## 12. Roadmap d'exécution

### Phase 1 — Cadrage produit

1. Définir le persona VC et les décisions que l'outil doit faciliter.
2. Figer les entrées, sorties et critères de succès du MVP.
3. Créer les issues et répartir le travail.

### Phase 2 — Données

4. Figer le schéma de données et les six domaines.
5. Générer ou collecter les 60 idées.
6. Valider, dédupliquer, documenter et figer `data-v1`.

### Phase 3 — Prototype notebook

7. Charger et explorer les données.
8. Implémenter le filtrage, les prompts et la sortie structurée.
9. Calculer le score et générer une sélection adaptative expliquée.

### Phase 4 — Évaluation et amélioration

10. Créer les 12 requêtes de référence.
11. Mesurer pertinence, respect des filtres, groundedness, latence et coût.
12. Corriger les erreurs et figer le pipeline MVP.

### Phase 5 — Interface

13. Extraire la logique réutilisable dans `src/`.
14. Construire l'interface Streamlit.
15. Tester le parcours complet et les cas d'erreur.

### Phase 6 — Livraison

16. Finaliser le notebook, le README et la présentation.
17. Réaliser une démonstration reproductible.
18. Fusionner les Pull Requests relues et créer la release `v1.0`.

## 13. Organisation Git et répartition recommandée

Ne pas développer directement sur `main`. Utiliser le flux :

```text
issue → branche → commits courts → push → pull request → revue → merge
```

Branches proposées :

```text
feature/data-schema
data/startup-ideas-v1
feature/notebook-recommender
experiment/prompt-v1
experiment/prompt-v2
feature/evaluation
feature/streamlit-interface
docs/final-delivery
```

| Rôle | Responsabilités principales |
|---|---|
| Produit et données | persona, schéma, génération, dataset card |
| Recommandation et prompting | prompts, Pydantic, scoring, Langfuse |
| Évaluation | requêtes de référence, métriques, analyse d'erreurs |
| Interface et livraison | Streamlit, UX, README, démonstration |

Chaque lot de données et chaque modification importante du scoring doivent être relus par une autre personne.

## 14. Definition of Done

Le MVP est terminé lorsque :

- [ ] le parcours utilisateur et les critères de succès sont documentés ;
- [ ] 60 idées réparties sur 6 domaines sont validées et versionnées ;
- [ ] les données possèdent une provenance et une dataset card ;
- [ ] le notebook s'exécute de bout en bout dans `Super_Project` ;
- [ ] les anciens imports vers le repo du professeur ont disparu ;
- [ ] le filtrage respecte les préférences explicites du VC ;
- [ ] le moteur retourne une sélection adaptative structurée et expliquée ;
- [ ] le score final est calculé dans le code ;
- [ ] au moins trois versions de prompt sont documentées ;
- [ ] les appels LLM sont tracés avec Langfuse ;
- [ ] les 12 requêtes test et leurs références humaines sont versionnées ;
- [ ] les métriques produit et l'analyse d'erreurs sont présentées ;
- [ ] les cas sans résultat, les erreurs LLM et les injections sont gérés ;
- [ ] l'interface Streamlit utilise le même pipeline que le notebook ;
- [ ] aucun secret ni contenu confidentiel n'est committé ;
- [ ] le README permet de lancer le notebook et l'interface ;
- [ ] une démonstration reproductible et une présentation finale sont prêtes.

## 15. Première action à réaliser

Les décisions de cadrage de la V1 sont consignées dans `phases/01_cadrage/README.md` : six domaines, données synthétiques, filtres V1, sélection adaptative, grille sur 100, produit bilingue et modèle `deepseek-r1:8b` exécuté localement avec Ollama.

La phase 2 peut produire un échantillon de deux idées par domaine. Cet échantillon doit être validé avant de générer les 60 idées.
