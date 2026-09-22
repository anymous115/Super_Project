# Super_Project — VC Pitch Intake & Triage

Capstone du cours « Prompt & Context Engineering ». Le projet reçoit des pitchs de fondateurs, les note selon une grille VC, les classe, et remonte les meilleurs dossiers à l'investisseur.

- **[`CONTEXT.md`](CONTEXT.md)** — le produit et son périmètre
- **[`docs/PROTOCOL.md`](docs/PROTOCOL.md)** — le protocole opérationnel
- **[`phases/01_cadrage/`](phases/01_cadrage/)** — le brief produit

## Configuration de l'expérience

Exigée par le [§10 du protocole](docs/PROTOCOL.md#10-benchmark--le-volet-p8). Ces valeurs sont figées pour toute la durée du benchmark.

### Modèles comparés

| Rôle | Modèle | Exécution | Décidé en |
|---|---|---|---|
| Local | `deepseek-r1:8b` | Ollama, machine locale | phase 1 |
| Frontier | `gpt-6-astra` | API OpenAI | phase 1 |

**Pourquoi ce frontier.** L'écart de prix entre les candidats représente environ 14 $ sur l'ensemble du benchmark — un arrondi, pas un arbitrage budgétaire. Le choix s'est donc fait sur l'axe qualité : une étude *quality-vs-cost* compare un petit modèle local à un plafond de qualité, et retenir le frontier le moins cher écraserait l'axe même qu'on mesure. Une conclusion « le local suffit » n'est défendable que si le local a été comparé au meilleur disponible.

`gemini-3.1-pro-preview` a été écarté pour une seconde raison : son statut *Preview* signifie qu'il peut évoluer en cours d'expérience, ce qui casse la reproductibilité exigée au §10.

Aucun modèle Anthropic n'est éligible : les pitchs du corpus sont rédigés par Claude, et benchmarker un modèle de la même famille mesurerait en partie de l'auto-cohérence.

### Tarifs retenus

| Modèle | Entrée /M tokens | Sortie /M tokens |
|---|---:|---:|
| `gpt-6-astra` | 10 $ | 50 $ |

**Source :** [OpenAI — API pricing](https://developers.openai.com/api/docs/pricing) · **Consultée le 22 septembre 2026**

Coût estimé de la part frontier : **~17 $** pour 450 appels (810 k tokens d'entrée, 180 k de sortie), hors cache et outils externes.

### Conditions de mesure

- température 0 ;
- mêmes 50 pitchs, même ordre de passage ;
- un appel d'échauffement local exclu des mesures ;
- 3 répétitions par configuration ;
- machine de mesure locale à documenter avant la première série.

## Jeu de données

50 pitchs fictifs en anglais, calibrés avant rédaction.

| Fichier | Contenu |
|---|---|
| `data/pitches.jsonl` | Les pitchs et leur provenance |
| `data/calibration.jsonl` | Les scores cibles — **généré**, ne pas éditer |
| `data/team.json` | Correspondance A/B/C/D |
| `docs/CALIBRATION_GRID.md` | La calibration — source de vérité |
| `docs/SOURCING_CANDIDATES.md` | Les sociétés sources |
| `docs/PITCH_TEMPLATE.md` | Le gabarit de rédaction |

```bash
python3 scripts/build_calibration.py     # régénère et vérifie les invariants
python3 scripts/show_pitch.py P005 P006  # lit un pitch
```

Le générateur refuse de produire si la distribution, le nombre d'injections, l'ordre des scores, la largeur de la coupure, la répartition sectorielle ou la règle auteur ≠ annotateur ne tiennent plus.
