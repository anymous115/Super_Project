# Contrôles Unicornext V1 — 24 septembre 2026

## Évaluations directes

- 50 / 50 pitchs notés directement par Codex après lecture du texte.
- 250 justifications individuelles (cinq critères par dossier).
- Schéma `PitchScore` validé, totals recalculés depuis les cinq notes.
- 100 extraits cités : présence exacte vérifiée dans les textes sources.
- Empreinte SHA-256 vérifiée ; un texte modifié ne réutilise pas son évaluation V1.
- Aucun statut de validation humaine utilisé pour charger les notes.
- 50 dossiers inclus dans le classement. Les 5 alertes de manipulation sont informatives ; les notes restent fondées sur le contenu économique.
- Top 5 : P017 78, P003 77, P001 76, P006 74, P015 73.

Les tests n’attestent pas la vérité des déclarations des pitchs ni une performance prédictive d’investissement. Les évaluations directes ne sont pas des appels Ollama/API mesurés et ne produisent pas de métrique de coût ou de latence du benchmark.

## Parcours applicatifs

Tests Streamlit AppTest : navigation, fiche, filtre sans résultat, sauvegarde/retrait de shortlist, comparaison d’un dossier scoré, dépôt disponible et erreur de lecture avec bouton de réessai. Scoring réel des nouveaux dépôts non déclenché pour cette refonte.

Interface française et anglaise exécutée sur le corpus V1. Les commentaires des 50 évaluations directes restent en français, indiqué dans l’interface.

## Vérification visuelle

- Chrome, bureau : vue d’ensemble avec 50 scores et top 5 contrôlée visuellement.
- Chrome en émulation mobile 400 × 898 : indicateurs sur deux colonnes, cartes empilées, fiche et sections forces/risques lisibles sans débordement observé.
- Émulation iPad Mini 768 × 1024 : fiche, score et barres par critère contrôlés.
- Contrôles natifs conservés, styles de focus et règle `prefers-reduced-motion: reduce` présents. Pas d’audit complet de lecteur d’écran réalisé.
- Suite complète : 162 tests réussis. Vérification `git diff --check` sans erreur.
