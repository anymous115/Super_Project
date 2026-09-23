# Super_Project — VC Pitch Intake & Triage

Capstone du cours « Prompt & Context Engineering ». Le projet reçoit des pitchs de fondateurs, les note selon une grille VC, les classe, et remonte les meilleurs dossiers à l'investisseur.

- **[`CONTEXT.md`](CONTEXT.md)** — le produit et son périmètre
- **[`docs/PROTOCOL.md`](docs/PROTOCOL.md)** — le protocole opérationnel
- **[`phases/01_cadrage/`](phases/01_cadrage/)** — le brief produit

## Tableau de bord d'avancement

Le tableau de bord de pilotage calcule l'état des six phases directement depuis
les fichiers du dépôt : pitchs validés, annotations, PDF, modules, appels du
benchmark et livrables finaux. Il évolue donc après chaque pull ou commit, sans
mettre à jour un pourcentage à la main.

```bash
streamlit run dashboard.py
```

L'onglet **Vue d'ensemble** montre la phase active et les prochaines actions.
Les autres onglets détaillent les données, le benchmark, la livraison et les
derniers commits. Un export JSON de l'état courant est disponible dans l'onglet
**Activité Git**.

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

Coût estimé de la part frontier : **~14 $** pour 450 appels (501 k tokens d'entrée, 180 k de sortie), hors cache et outils externes.

Recalculé sur le corpus réel par `python3 scripts/estimate_cost.py`. L'estimation précédente de ~17 $ partait du plafond de 800 mots par pitch ; le corpus en fait **475 en moyenne**, et une entrée pèse 897 à 1 287 tokens selon la version de prompt, pas 1 800.

### Conditions de mesure

- température 0 ;
- mêmes 50 pitchs, même ordre de passage ;
- un appel d'échauffement local exclu des mesures ;
- 3 répétitions par configuration.

### Machine de mesure

Exigée par le §10. La latence est l'un des trois axes du benchmark : une latence sans machine ne veut rien dire, et une fois la série lancée il est trop tard pour la documenter.

| | |
|---|---|
| Machine | MacBook Pro `Mac16,1` |
| Processeur | Apple M4, 10 cœurs, arm64 |
| Mémoire | 16 Go unifiés |
| Système | macOS 26.5.1 (25F80) |
| Ollama | 0.34.0 |

**Toute la série locale tourne sur cette machine.** Changer de machine en cours de benchmark invalide les latences déjà mesurées — il faudrait tout reprendre, ou rapporter deux séries séparément.

> ⏱️ **Ordre de grandeur relevé.** Un appel sur le plus court pitch du corpus (82 mots) a pris **14,6 s** avec `llama2` sur cette machine. `deepseek-r1:8b` est un modèle de raisonnement : il produit ses tokens de réflexion avant la réponse, donc il sera plus lent, et les pitchs longs font sept fois la taille de celui-là.
>
> La part locale de la matrice complète — 450 appels — représente donc plusieurs heures, pas plusieurs minutes. À lancer en tâche de fond, et à ne pas découvrir la veille du rendu.

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
python3 scripts/build_calibration.py      # régénère et vérifie les invariants
python3 scripts/show_pitch.py P005 P006   # lit un pitch, cible masquée
python3 scripts/build_dataset_card.py     # régénère data/dataset_card.md
python3 scripts/render_pdfs.py            # rend les 50 PDF
python3 scripts/estimate_cost.py          # recalcule le budget depuis le corpus
```

La [dataset card](data/dataset_card.md) est **générée** depuis les données : ses chiffres ne peuvent pas diverger du corpus qu'ils décrivent.

Les PDF sont rendus **depuis `pitch_text`**, en trois mises en page — serif, deux colonnes, sans-serif — parce qu'un corpus où tous les PDF sortent du même gabarit ne teste pas l'extraction, il teste un gabarit. `pitch_text` reste l'entrée unique du benchmark ; l'extraction se mesure à part (§6).

Le générateur refuse de produire si la distribution, le nombre d'injections, l'ordre des scores, la largeur de la coupure, la répartition sectorielle ou la règle auteur ≠ annotateur ne tiennent plus.

## Annotation

La référence ne vient pas des cibles de calibration : elle vient de la double annotation à l'aveugle (§6). 50 pitchs × 2 annotateurs = **100 annotations, 25 par personne**.

```bash
python3 scripts/annotate.py --who A --status    # ce qu'il me reste
python3 scripts/annotate.py --who A             # annoter, à l'aveugle
python3 scripts/build_reference.py --report     # l'état de la fusion
python3 scripts/build_reference.py              # produit data/reference_scores.jsonl
```

`annotate.py` ne lit jamais `calibration.jsonl` : ni cible, ni rang, ni palier, ni drapeau. Le total pondéré n'apparaît qu'après la saisie des cinq notes, pour qu'il n'ancre pas la recommandation.

Pour la même raison, **`show_pitch.py` masque la cible par défaut** — il faut `--reveal` pour la voir.

`build_reference.py` refuse de produire tant qu'un pitch n'a pas ses deux annotations, ou tant qu'un écart supérieur à 1 point sur 5 n'a pas été tranché et consigné. Une référence qui moyenne un désaccord de 3 points n'est pas une référence.

## Pipeline

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis remplir les clés — le .env n'est jamais committé
pytest                        # 53 tests, aucun appel de modèle
```

| Module | Rôle |
|---|---|
| `src/config.py` | Grille, poids, règle de sélection, modèles, tarifs — les constantes figées du §10 |
| `src/schemas.py` | Validation Pydantic des sorties, et recalcul du total |
| `src/prompts.py` | V0 / V1 / V2, avec l'empreinte de chaque version |
| `src/score_pitch.py` | Un appel : prompt, modèle, mesure, validation, enregistrement |
| `src/benchmark.py` | La matrice 2 × 3 × 50 × 3, reprenable |
| `src/metrics.py` | MAE, Spearman, chevauchement du top 5, latences, coûts |

```bash
python3 -m src.benchmark --models local --prompts V0 --limit 3 --repetitions 1
python3 -m src.benchmark                 # la matrice complète, 900 appels
python3 -m src.benchmark --summary       # agrège dans results/benchmark_summary.csv
python3 scripts/estimate_cost.py         # recalcule le budget depuis le corpus
```

Trois propriétés à ne pas perdre de vue :

**Le total est recalculé dans le code.** Le modèle annonce un total, on le garde dans `total_reported` pour mesurer s'il sait compter, mais le score qui fait foi est `total_computed`.

**La série est reprenable.** Chaque appel est écrit dans `results/raw_runs.jsonl` dès qu'il revient, et un relancement saute ce qui est déjà mesuré. Une coupure ne coûte pas la série.

**Le benchmark tourne, mais ne peut pas encore être noté.** `src/benchmark.py --summary` exige `data/reference_scores.jsonl`, produit par la double annotation. Les cibles de `calibration.jsonl` ne sont pas la référence : elles ont servi à garantir l'étalement des scores avant rédaction, pas à dire la vérité.
