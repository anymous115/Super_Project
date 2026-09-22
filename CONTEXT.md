# Contexte du projet

Ce dépôt contient le capstone du cours « Prompt & Context Engineering ». Il part du sujet **P8 — Quality-vs-cost benchmark**, mais le périmètre a été modifié avec l'accord du professeur afin de privilégier la création d'un produit fonctionnel.

## Nouvelle orientation

Le projet devient un **VC Startup Opportunity Finder** : un outil qui aide un investisseur à découvrir les meilleures idées de startups selon son domaine et sa thèse d'investissement.

Le VC choisit un secteur et peut préciser des préférences comme le stade, la géographie, le ticket, le business model ou des mots-clés. Le produit filtre un catalogue d'idées, analyse les opportunités compatibles, les classe et fournit un top 5 expliqué avec scores, raisons, risques et questions à vérifier.

La comparaison entre un modèle local et un modèle frontier n'est plus l'objectif principal. Le modèle est évalué comme composant du produit : pertinence des recommandations, respect des filtres, groundedness, qualité des explications, latence et coût.

## Scope du MVP

- dataset seed de 60 idées fictives et validées, réparties sur 6 domaines ;
- moteur hybride de filtrage, analyse et classement ;
- prompts versionnés et sorties structurées avec Pydantic ;
- top 5 personnalisé et explicable ;
- évaluation sur 12 requêtes de référence ;
- tracing avec Langfuse ;
- prototype complet dans `08_quality_vs_cost_benchmark.ipynb` ;
- interface Streamlit une fois le pipeline validé.

Le produit est une aide à l'exploration et ne remplace pas la due diligence ou la décision finale du VC. Le protocole détaillé se trouve dans `docs/PROTOCOL.md`.
