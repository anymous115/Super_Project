# Contexte du projet

Ce dépôt contient le capstone du cours « Prompt & Context Engineering ». Il part du sujet **P8 — Quality-vs-cost benchmark**, dont le périmètre a été élargi **avec l'accord du professeur** afin de privilégier la construction d'un produit fonctionnel plutôt que la tâche de démonstration du cours.

Le benchmark du P8 n'est pas abandonné pour autant : il porte sur le moteur de scoring, qui est le cœur du produit.

## Produit

**VC Pitch Intake & Triage** : un système qui reçoit les pitchs de fondateurs, les note selon une grille VC, les classe, et envoie aux investisseurs inscrits une analyse des meilleurs dossiers.

Le problème traité est concret. Un fonds reçoit des centaines de pitchs par mois, par des canaux dispersés — email, Telegram, DM sur les réseaux. La plupart ne seront jamais lus. L'outil centralise ce flux entrant, applique la même grille d'évaluation à tous les dossiers, et fait remonter le haut du panier avec une justification traçable.

Le nombre de dossiers remontés suit une **sélection adaptative** : `min(50, max(5, ceil(n × 0,10)))`. Les 5 meilleurs sous 50 pitchs, puis le top 10 %, plafonné à 50 dossiers. Les régimes se rejoignent exactement à 50.

Le tri reste une aide à la décision. Il ne remplace ni la due diligence ni le jugement de l'investisseur.

## Lien avec le P8

Le cœur du produit est le **moteur de scoring**. C'est là que le sujet du cours s'applique directement : le scoring tourne sur un modèle local léger et sur un modèle frontier, et on mesure lequel est le plus fiable, le plus rapide et le moins cher, pour recommander lequel mettre en production.

La question du cours devient une vraie question d'ingénierie produit : **quel modèle fait tourner le tri des pitchs en production, et à quel prix ?**

## Ingestion multi-canal

L'entrée du système est pensée dès le départ comme multi-canal, avec un adaptateur par canal produisant un événement normalisé. Les canaux ne se valent pas :

| Canal | Version 1 | Raison |
|---|---|---|
| Telegram | ✅ | Bot API gratuite, webhook, réception directe de PDF |
| Email | ✅ | Canal réel dominant chez les VCs, inbound parsing simple |
| Instagram | ❌ phase 2 | API Messaging Meta : compte Business, App Review, pas de pièce jointe en DM |
| X / Twitter | ❌ phase 2 | API payante par paliers, accès aux DM restreint |
| LinkedIn | ❌ | Aucune API de messagerie pour cet usage |

Les deux canaux de la v1 couvrent le cas d'usage réel. Les autres sont documentés comme extensions, avec leurs contraintes, sans être construits.

## Scope du MVP

- 50 pitchs fictifs annotés en double, en texte et en PDF ;
- grille de notation VC explicite et pondérée ;
- sélection adaptative `min(50, max(5, 10 %))` ;
- modèle local `deepseek-r1:8b` via Ollama ;
- restitution bilingue français / anglais ;
- pipeline de scoring commun aux deux modèles ;
- sorties structurées validées avec Pydantic ;
- prompts versionnés V0 / V1 / V2, avec défense contre le prompt injection ;
- benchmark qualité / coût / latence et recommandation défendue ;
- tracing des appels LLM avec Langfuse ;
- ingestion Telegram et email ;
- interface Streamlit présentant la file de pitchs triée ;
- notebook exécutable de bout en bout.

## Hors périmètre

- comptes VC, paiement, base de données de production ;
- connecteurs Instagram et X ;
- traitement de decks réels ou confidentiels ;
- toute décision d'investissement automatisée sans validation humaine.

## Historique des décisions

L'élargissement du périmètre validé par le professeur a d'abord donné lieu à une variante « VC Startup Opportunity Finder » — un catalogue d'idées que le VC explore — proposée puis écartée. Elle inversait le sens du flux : plus de fondateurs, plus de dossiers entrants, et une évaluation mesurée contre des idées inventées par l'équipe elle-même, donc sans vérité externe.

Les apports techniques de cette proposition sont conservés : validation Pydantic, tracing Langfuse, interface Streamlit et la discipline d'évaluation produit.

Le protocole détaillé se trouve dans `docs/PROTOCOL.md`. La calibration du jeu de données est dans `docs/CALIBRATION_GRID.md`.
