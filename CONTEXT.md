# Contexte du projet

> **Évolution V1 — 24 septembre 2026 :** l’équipe a supprimé la validation humaine obligatoire. Les 50 notes directes IA alimentent Unicornext. Voir [la décision V1](docs/UNICORNEXT_V1.md). Les mentions de validation ci-dessous décrivent le protocole antérieur.

Ce dépôt contient le capstone du cours « Prompt & Context Engineering ». Il part du sujet **P8 — Quality-vs-cost benchmark**, dont le périmètre a été élargi **avec l'accord du professeur** afin de privilégier la construction d'un produit fonctionnel plutôt que la tâche de démonstration du cours.

Le **23 septembre 2026**, toujours avec l'accord du professeur, la comparaison de modèles a été retirée du projet. Le livrable est désormais **le produit** : un moteur de scoring sur un seul modèle, alimenté par de vrais canaux d'entrée et présenté dans une interface. Le détail de cette décision est plus bas, dans l'historique.

## Produit

**VC Pitch Intake & Triage** : un système qui reçoit les pitchs de fondateurs, les note selon une grille VC, les classe, et envoie aux investisseurs inscrits une analyse des meilleurs dossiers.

Le problème traité est concret. Un fonds reçoit des centaines de pitchs par mois, par des canaux dispersés : email, Telegram, DM sur les réseaux. La plupart ne seront jamais lus. L'outil centralise ce flux entrant, applique la même grille d'évaluation à tous les dossiers, et fait remonter le haut du panier avec une justification traçable.

Le nombre de dossiers remontés suit une **sélection adaptative** : `min(50, max(5, ceil(n × 0,10)))`. On garde les 5 meilleurs sous 50 pitchs, puis le top 10 %, plafonné à 50 dossiers. Les deux régimes donnent exactement le même résultat à 50 pitchs.

Le tri reste une aide à la décision. Il ne remplace ni la due diligence ni le jugement de l'investisseur.

## Moteur de scoring

Le scoring tourne sur **`qwen2.5:14b` en local, via Ollama**, derrière un **filtre anti-injection** qui s'applique avant le modèle.

| | |
|---|---|
| **Coût** | Aucun coût d'API : le modèle tourne sur la machine du fonds. |
| **Confidentialité** | Un pitch n'est jamais envoyé à un service tiers. C'est un argument réel pour un fonds, qui reçoit des informations non publiques. |
| **Débit** | ~1 min par pitch sur un MacBook Pro M4, soit ~1 400 pitchs par jour en continu. Un fonds en reçoit quelques centaines par mois : le tri se fait en tâche de fond. |
| **Sécurité** | Un pitch qui tente de dicter sa note sort du classement automatique et part en revue humaine. Sur le corpus : 5 pièges sur 5 écartés, 0 pitch sain signalé à tort. |
| **Limites connues** | Le modèle surnote les pitchs moyens et faibles, et tasse les notes entre 60 et 85 : il ordonne correctement l'ensemble, mais départage mal les bons dossiers entre eux. |

Le choix se fait sur le coût et la confidentialité, **pas sur la puissance**. Il a été mesuré, pas supposé : trois modèles locaux ont été essayés sur les 50 pitchs (détail dans le [README](README.md#moteur-de-scoring)).

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
- moteur de scoring sur `qwen2.5:14b` en local, derrière un filtre anti-injection ;
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

Le même jour, le modèle local a changé. `deepseek-r1:8b`, un modèle de raisonnement, ne répondait pas sur 14 pitchs sur 18 : il épuisait son budget en réflexion. `qwen2.5:7b` puis `qwen2.5:14b` ont été mesurés sur les 50 pitchs. Le 14b a été retenu, et le filtre anti-injection ajouté parce qu'il plaçait un pitch piégé premier à 100/100.

Ce qui avait été construit pour le benchmark reste dans le dépôt et sert le produit : la grille, les prompts versionnés, la validation, les bornes du modèle local, les métriques. Le protocole a été mis à jour en conséquence.

Le protocole détaillé se trouve dans `docs/PROTOCOL.md`. La calibration du jeu de données est dans `docs/CALIBRATION_GRID.md`.
