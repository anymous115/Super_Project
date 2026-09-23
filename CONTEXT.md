# Contexte du projet

Ce dépôt contient le capstone du cours « Prompt & Context Engineering ». Il part du sujet **P8 — Quality-vs-cost benchmark**, dont le périmètre a été élargi **avec l'accord du professeur** afin de privilégier la construction d'un produit fonctionnel plutôt que la tâche de démonstration du cours.

Le **23 septembre 2026**, toujours avec l'accord du professeur, la comparaison de modèles a été retirée du projet. Le livrable est désormais **le produit** : un moteur de scoring sur un seul modèle, alimenté par de vrais canaux d'entrée et présenté dans une interface. Le détail de cette décision est plus bas, dans l'historique.

## Produit

**VC Pitch Intake & Triage** : un système qui reçoit les pitchs de fondateurs, les note selon une grille VC, les classe, et envoie aux investisseurs inscrits une analyse des meilleurs dossiers.

Le problème traité est concret. Un fonds reçoit des centaines de pitchs par mois, par des canaux dispersés : email, Telegram, DM sur les réseaux. La plupart ne seront jamais lus. L'outil centralise ce flux entrant, applique la même grille d'évaluation à tous les dossiers, et fait remonter le haut du panier avec une justification traçable.

Le nombre de dossiers remontés suit une **sélection adaptative** : `min(50, max(5, ceil(n × 0,10)))`. On garde les 5 meilleurs sous 50 pitchs, puis le top 10 %, plafonné à 50 dossiers. Les deux régimes donnent exactement le même résultat à 50 pitchs.

Le tri reste une aide à la décision. Il ne remplace ni la due diligence ni le jugement de l'investisseur.

## Moteur de scoring

Le scoring tourne sur **`deepseek-r1:8b` en local, via Ollama**.

| | |
|---|---|
| **Coût** | Aucun coût d'API : le modèle tourne sur la machine du fonds. |
| **Confidentialité** | Un pitch n'est jamais envoyé à un service tiers. C'est un argument réel pour un fonds, qui reçoit des informations non publiques. |
| **Débit** | ~3,5 min par pitch avec le prompt de production (V2) sur un MacBook Pro M4, soit ~400 pitchs par jour en continu. Un fonds en reçoit quelques centaines par mois : le tri se fait en tâche de fond, pas en temps réel. |
| **Limites connues** | Le modèle se trompe parfois en calculant le total : le code le recalcule. Il entoure son JSON d'un bloc markdown : le code le retire. Il hésite parfois sur l'identifiant du pitch : c'est l'identifiant de l'appel qui fait foi. |

Le choix se fait sur le coût et la confidentialité, **pas sur la puissance** : un modèle de 8 milliards de paramètres ne rivalise pas avec un modèle frontier en finesse de jugement. Les bornes d'exécution et les mesures réelles sont dans le [README](README.md#moteur-de-scoring).

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

- 50 pitchs fictifs calibrés, en texte et en PDF ;
- grille de notation VC explicite et pondérée ;
- sélection adaptative `min(50, max(5, 10 %))` ;
- moteur de scoring sur `deepseek-r1:8b` en local ;
- sorties structurées validées avec Pydantic, total recalculé dans le code ;
- prompts versionnés V0 / V1 / V2, avec défense contre le prompt injection : V2 est le prompt de production ;
- contrôles du moteur : sortie valide, latence, injections contenues, cohérence avec la calibration ;
- restitution bilingue français / anglais ;
- tracing des appels LLM avec Langfuse ;
- ingestion Telegram et email ;
- extraction du texte des PDF ;
- interface Streamlit présentant la file de pitchs triée ;
- notebook exécutable de bout en bout.

## Hors périmètre

- **comparaison de modèles** (local contre frontier), retirée le 23 septembre 2026, voir [`docs/BACKLOG.md`](docs/BACKLOG.md) ;
- comptes VC, paiement, base de données de production ;
- connecteurs Instagram et X ;
- traitement de decks réels ou confidentiels ;
- toute décision d'investissement automatisée sans validation humaine.

## Historique des décisions

L'élargissement du périmètre validé par le professeur a d'abord donné lieu à une variante « VC Startup Opportunity Finder », un catalogue d'idées que le VC explore. Elle a été proposée puis écartée : elle inversait le sens du flux (plus de fondateurs, plus de dossiers entrants), et elle aurait évalué le système sur des idées inventées par l'équipe elle-même, donc sans vérité externe.

Les apports techniques de cette proposition sont conservés : validation Pydantic, tracing Langfuse, interface Streamlit et la discipline d'évaluation produit.

**23 septembre 2026 : retrait de la comparaison de modèles.** Le projet prévoyait de comparer `deepseek-r1:8b` à un modèle frontier (`gpt-6-astra`), en mesurant la qualité contre une référence annotée à la main. Trois constats ont conduit à l'abandonner, avec l'accord du professeur :

- **le temps de calcul** : la série locale prenait ~16 h en trois répétitions, et encore ~5,5 h en une seule ;
- **la référence** : 100 annotations à l'aveugle par une équipe de non-investisseurs, dont un membre absent. Le relais par une IA tierce (Gemini) a buté sur les quotas gratuits ;
- **la valeur produit** : l'effort partait dans la mesure plutôt que dans ce que l'investisseur utilise.

Ce qui avait été construit pour le benchmark reste dans le dépôt et sert le produit : la grille, les prompts versionnés, la validation, les bornes du modèle local, les métriques. Le protocole a été mis à jour en conséquence.

Le protocole détaillé se trouve dans `docs/PROTOCOL.md`. La calibration du jeu de données est dans `docs/CALIBRATION_GRID.md`.
