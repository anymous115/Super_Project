# Annotations

Un fichier par annotateur, écrit par `scripts/annotate.py`. **Ne pas éditer à la main** : le script garantit que les notes sont des entiers de 0 à 5 et que chacune porte sa justification.

| Fichier | Contenu |
|---|---|
| `A.jsonl` · `B.jsonl` · `C.jsonl` · `D.jsonl` | Les annotations de chacun, 25 par personne |
| `reconciliation.jsonl` | Les désaccords tranchés en réunion, avec leur raison |

Une ligne d'annotation :

```json
{"pitch_id": "P012", "annotator": "A", "annotated_at": "2026-09-23",
 "scores": {"team": 4, "market": 3, "product": 3, "traction": 2, "business_model": 3},
 "evidence": {"team": "ten years in fleet operations, the last four running a 900-vehicle fleet", "…": "…"},
 "total_score": 62.0, "recommendation": "review", "comment": ""}
```

Une ligne de réconciliation, ajoutée **après discussion** et seulement pour un écart supérieur à 1 point :

```json
{"pitch_id": "P012", "scores": {"team": 4, "market": 3, "product": 3, "traction": 2, "business_model": 3},
 "reason": "A comptait les lettres d'intention comme traction, B non. Retenu : non."}
```

`scripts/build_reference.py` fusionne le tout en `data/reference_scores.jsonl` et refuse de produire tant qu'un désaccord reste ouvert.
