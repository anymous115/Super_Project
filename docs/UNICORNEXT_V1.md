# Unicornext — décision produit V1

Décision de l’équipe transmise le 24 septembre 2026 : supprimer l’étape obligatoire de validation humaine des pitchs, pour livrer une V1 sur des évaluations IA.

## Produit livré

- Entrée : `streamlit run app.py` (Unicornext). `dashboard.py` reste le pilotage interne du projet.
- 50 pitchs du corpus de démonstration lus et évalués directement par Codex, avec cinq notes, cinq justifications, réserves, informations absentes et citations.
- Source versionnée : `data/assessments/unicornext_v1.jsonl`. Rapport lisible : `docs/UNICORNEXT_V1_SCORES.md`.
- Une empreinte SHA-256 rattache chaque note au texte précis évalué. Changer le texte invalide cette note ; les anciens statuts `drafted` / `validated` sont historiques et ne bloquent pas l’application.
- Vue d’ensemble avec sélection automatique, recherche filtrée en cartes/tableau, fiche explicative, shortlist locale persistante et comparaison de trois dossiers.
- Aucun écran ou bouton de validation humaine. Les réserves sont des informations de la fiche, pas une étape de workflow.
- Les cinq tentatives de manipulation sont ignorées dans les notes et signalées à titre informatif. Tous les dossiers scorés participent au classement, à la sélection et à la shortlist sans exclusion liée à cette alerte.

## Sens des notes

Les sociétés du corpus sont fictives, dérivées ou synthétiques. Les notes jugent la solidité des informations fournies, sans vérifier les affirmations auprès de sources externes. Elles ne sont ni une probabilité de succès ni une performance financière attendue.

Grille conservée : équipe 20 %, marché 25 %, produit 15 %, traction 25 %, modèle économique 15 %. Échelle entière : 0 absent, 1 non étayé, 2 faible, 3 crédible, 4 solide, 5 exceptionnel. Le code recalcule le total sur 100. Les justifications signalent les calculs incohérents ; les notes de calibration ne sont pas des notes de production.

Avis indicatif : priorité élevée à partir de 75, à approfondir entre 50 et 74, non prioritaire en dessous. Des réserves matérielles peuvent rendre l’avis plus défavorable (économie structurellement négative, chiffres incompatibles). Le top utilise le score pondéré, puis traction, marché et identifiant pour départager. Il ne faut pas confondre l’avis IA et la shortlist sauvegardée par l’utilisateur.

## Nouveaux pitchs et mesures historiques

Les nouveaux dépôts texte/PDF/liens utilisent le moteur automatique local existant (`qwen2.5:14b`, V2). La fiche affiche cette provenance, distincte des évaluations directes Codex du corpus. Ces deux sources ne sont pas présentées comme un modèle unique. Sans Ollama disponible, le dossier est conservé mais aucune note n’est inventée.

Les évaluations directes n’ont pas de mesure API de tokens, de latence ou de coût. Elles ne sont donc pas injectées dans `results/raw_runs.jsonl` et ne constituent pas une nouvelle expérience du benchmark. Le notebook et les documents expérimentaux conservent leur historique. Cette décision V1 remplace leurs exigences de validation humaine pour le produit.

La shortlist est locale, partagée entre les sessions de cet ordinateur, sans compte utilisateur ni synchronisation multi-utilisateur. La V1 est une application locale ; aucun déploiement public n’est effectué.
