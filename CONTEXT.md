# Contexte du projet

C'est le capstone pour le cours "Prompt & Context Engineering" (9 projets au choix). Le projet choisi est le **P8 — Quality-vs-cost benchmark**, dont l'objectif de base est de comparer un modèle local léger vs un modèle frontier sur une tâche donnée, et d'en sortir un tableau qualité/coût/latence + une recommandation.

## Adaptation

Au lieu de la tâche de démo du cours (classifier finance/sport/tech), le projet s'applique à un vrai cas d'usage — un bot d'évaluation de pitchs pour VCs :

- Des porteurs de projet uploadent leur deck (le bot a de la latitude sur comment il le traite/extrait).
- Le bot note chaque pitch selon une grille façon VC.
- Il sélectionne le top 10% des meilleurs pitchs.
- Une analyse est envoyée directement aux VCs enregistrés sur le site.

Le P8 rentre dans cette histoire au niveau du scoring : l'évaluation des pitchs tourne sur un modèle local et un modèle frontier, pour mesurer lequel est le plus fiable/rapide/cheap, et recommander lequel utiliser en prod.

## Scope décidé

On fait d'abord le capstone — notebook + données seed, dans le cadre du cours. Le vrai site déployé (inscription VC, upload de deck, etc.) pourra venir après, pas maintenant.

## Ce qui reste ouvert

- La grille de notation (critères VC : équipe, marché, produit, traction, business model — pondérations à fixer).
- Le seuil du top 10% : relatif au lot soumis, ou score absolu ?
- Les données seed : génération de 15-20 pitchs fictifs avec scores de référence, ou utilisation d'exemples réels (anonymisés) ?
