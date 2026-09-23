# Backlog — features envisagées après le MVP

Ce qui est identifié comme utile mais volontairement exclu de la première version. Rien ici n'est engagé : le MVP et son échéance passent d'abord.

---

## Extraction de profil

**Statut : envisagé, non planifié.**

### L'idée

En plus de noter le pitch, en extraire une **fiche structurée** de l'entreprise et de l'équipe.

```json
{
  "pitch_id": "P001",
  "company": {
    "name": "...", "sector": "...", "subsector": "...",
    "geography": ["..."], "stage": "pre-seed|seed|series-a",
    "founded_year": null
  },
  "team": {
    "founders": [{"role": "CEO", "background": "..."}],
    "team_size": null
  },
  "ask": { "amount_eur": null, "valuation_eur": null, "use_of_funds": ["..."] },
  "traction": { "arr_eur": null, "customers": null, "growth": "..." },
  "business_model": "...",
  "technology": ["..."],
  "extraction_confidence": { "...": "high|medium|low" }
}
```

Tout champ absent du pitch reste `null`. La règle du scoring s'applique à l'identique : **ne jamais inventer ce qui n'est pas écrit**.

### Pourquoi c'est utile

**Déduplication.** Avec l'ingestion multi-canal, le même fondateur peut envoyer son dossier par Telegram *et* par email. Sans profil structuré, ce sont deux entrées distinctes dans la file. Ce n'est pas du confort : c'est nécessaire dès que deux canaux tournent en parallèle.

**Filtrage par thèse.** Un VC ne veut voir que du pre-seed européen en B2B SaaS. Un score sur 100 ne permet pas ce filtre ; un profil structuré oui.

**Recherche et mémoire.** Retrouver un dossier six mois plus tard, ou repérer qu'un fondateur revient avec une nouvelle version de son pitch.

### Ce que ça réconcilie

C'est la pièce qui **relie les deux visions de l'équipe**.

La proposition « Opportunity Finder » de @MathisseSteckler reposait sur un catalogue d'idées décrites par des champs — domaine, stade, géographie, modèle économique — que le VC interroge selon sa thèse. Sa faiblesse était la source : un catalogue inventé par l'équipe, sans vérité externe.

L'extraction de profil produit **exactement ces champs**, mais à partir de pitchs réellement reçus. Sa couche de filtrage par thèse devient alors pertinente, posée sur un corpus entrant au lieu d'un catalogue fabriqué.

Autrement dit, les deux directions ne s'excluaient pas : il manquait l'étage qui les relie. Le désaccord portait sur l'ordre — construire le corpus d'abord, le filtre ensuite.

### Ce que ça apporterait à l'évaluation

> Section écrite quand le projet comparait deux modèles. L'argument vaut toujours si la comparaison revient (voir plus bas).

C'est l'argument le plus fort en faveur de cette feature, et il vaut d'être pesé **avant** de la repousser trop loin.

La qualité du scoring se mesure aujourd'hui contre des scores de référence produits par annotation humaine. C'est du jugement : deux annotateurs peuvent légitimement diverger, et la grille de calibration prévoit d'ailleurs deux cas ambigus.

L'extraction, elle, a une **vérité terrain non ambiguë**. « Combien demande cette société ? » a une seule bonne réponse, lisible dans le texte. Aucune discussion d'annotation, aucun désaccord à réconcilier.

Un benchmark portant sur deux tâches — une subjective, une objective — est nettement plus solide qu'un benchmark portant sur le seul scoring. C'est précisément là qu'un petit modèle local peut s'avérer suffisant alors qu'il échoue sur le jugement : l'extraction est une tâche de lecture, pas d'appréciation.

**Métriques** : exactitude par champ, taux de `null` correctement laissés vides, **taux d'hallucination** — un champ rempli alors que l'information est absente du pitch.

### Coût d'implémentation

| Approche | Pour | Contre |
|---|---|---|
| **Même appel que le scoring** | Un seul appel, pas de surcoût | Prompt plus lourd, sortie plus longue, risque de dégrader le scoring |
| **Appel séparé** | Tâches indépendantes, modèle bon marché possible pour l'extraction | Double les appels et la latence |

L'appel séparé se défend mieux : l'extraction étant plus facile, elle peut tourner sur le modèle local même si le scoring part sur le frontier. C'est un scénario hybride concret et chiffrable.

Le jeu de données existant suffit : les 50 pitchs portent déjà les champs à extraire. Il faut y ajouter une annotation de référence — **beaucoup plus rapide que l'annotation de scoring**, puisqu'il s'agit de relever des faits, pas de porter un jugement.

### Décision

**Hors MVP.** L'échéance du capstone passe d'abord, et le goulot actuel reste les 40 annotations de scoring.

À rouvrir si le pipeline est figé en avance. Dans ce cas, c'est l'ajout au meilleur rapport valeur / effort de tout le backlog.

---

## Connecteurs Instagram et X

**Statut : documenté, bloqué par des contraintes externes.**

Détaillé au §4 du [protocole](PROTOCOL.md#canaux). Instagram demande un compte Business lié à une Page, une app Meta et un passage en App Review ; X demande un accès API payant avec des DM restreints. Aucun des deux ne tient dans les délais du rendu.

À reprendre seulement si le produit sort du cadre du cours. Prérequis commun : un **résolveur de liens**, puisque sur ces canaux un pitch arrive sous forme de lien bien plus souvent que de PDF.

---

## Comparaison de modèles local / frontier

**Statut : retirée du MVP le 23 septembre 2026, avec l'accord du professeur.**

Le sujet d'origine du cours (P8) : comparer `deepseek-r1:8b` en local à un modèle frontier (`gpt-6-astra`) sur la qualité, la latence et le coût, et recommander lequel mettre en production.

### Ce qui est déjà construit

- la matrice reprenable (`src/benchmark.py`) en une passe, avec un test de stabilité sur 10 pitchs ;
- les métriques : MAE, Spearman, chevauchement du top 5, accord de recommandation, variation due aux injections (`src/metrics.py`) ;
- les bornes du modèle local et ses latences mesurées ;
- l'outillage d'annotation à l'aveugle (`scripts/annotate.py`, `scripts/build_reference.py`) et sa variante par IA tierce (`scripts/annotate_ai.py`, [`AI_REFERENCE.md`](AI_REFERENCE.md)).

### Ce qui manquait

- **une référence** : 100 annotations humaines, ou une référence IA validée sur un échantillon humain. Le quota gratuit de Gemini (20 requêtes par jour) a bloqué la seconde voie ;
- **du temps machine** : ~5,5 h pour la part locale en une passe ;
- **une clé OpenAI** : ~5 $ pour la part frontier, davantage si le modèle facture son raisonnement.

### Pour la rouvrir

Activer la facturation Gemini (moins de 1 $ pour les 45 pitchs restants), faire annoter l'échantillon de 12 pitchs, puis lancer `python3 -m src.benchmark`. Tout le reste est en place.

