# Super_Project — VC Pitch Intake & Triage

Capstone du cours « Prompt & Context Engineering ». Le projet reçoit des pitchs de fondateurs, les note selon une grille VC, les classe, et remonte les meilleurs dossiers à l'investisseur.

- **[`CONTEXT.md`](CONTEXT.md)** — le produit et son périmètre
- **[`docs/PROTOCOL.md`](docs/PROTOCOL.md)** — le protocole opérationnel
- **[`phases/01_cadrage/`](phases/01_cadrage/)** — le brief produit

## Tableau de bord d'avancement

Le tableau de bord de pilotage calcule l'état des six phases directement depuis
les fichiers du dépôt : pitchs validés, PDF, modules, pitchs scorés, ingestion
et livrables finaux. Il évolue donc après chaque pull ou commit, sans
mettre à jour un pourcentage à la main.

```bash
streamlit run dashboard.py
```

L'onglet **Vue d'ensemble** montre la phase active et les prochaines actions.
Les autres onglets détaillent les données, le moteur, la livraison et les
derniers commits. Un export JSON de l'état courant est disponible dans l'onglet
**Activité Git**.

## Moteur de scoring

Le produit note les pitchs avec **`deepseek-r1:8b`**, exécuté en local par Ollama. Pourquoi ce modèle : [CONTEXT.md](CONTEXT.md#moteur-de-scoring). En résumé, aucun coût d'API, et aucun pitch ne quitte la machine.

La comparaison avec un modèle frontier, prévue au départ, a été retirée du projet le 23 septembre 2026 avec l'accord du professeur. `gpt-6-astra` reste déclaré dans `src/config.py`, mais le produit ne l'appelle pas.

### Bornes d'exécution

- température 0 ;
- `num_ctx` 8192 et `num_predict` 4096 ;
- chaque appel plafonné à 600 s ;
- un appel d'échauffement au démarrage, non enregistré.

> **Ces bornes ne sont pas un réglage de confort.** Ollama charge `deepseek-r1:8b` avec une fenêtre de 4 096 tokens. Une entrée d'environ 1 000 tokens plus un raisonnement libre la sature, et le serveur se met alors à réévaluer le prompt en boucle : un appel observé a dépassé **58 minutes** sans rendre la main, contre 122 secondes pour un pitch de taille comparable.
>
> Le plafond de génération est à 4 096 et pas plus bas : à 2 048, sous le prompt V2, le modèle consomme **la totalité du budget en raisonnement et n'émet aucune réponse**. À 4 096, il termine de lui-même. Chaque appel enregistre s'il a été coupé par la borne.

### Latence mesurée

| Prompt | Latence par appel | 50 pitchs |
|---|---:|---:|
| V0 | 53 à 69 s | ~50 min |
| V1 | ~130 s (interpolé) | ~1 h 50 |
| **V2, production** | **~206 s** | **~2 h 50** |

V2 est le prompt de production : c'est le seul qui porte la défense contre l'injection. À ~3,5 min par pitch, le moteur traite environ 400 pitchs par jour en continu, ce qui est largement au-dessus du flux d'un fonds. Le tri se fait en tâche de fond.

Le raisonnement représente **63 à 78 % des caractères générés** en V0. Il est conservé dans `raw_thinking` pour chaque appel.

### Machine de mesure

Une latence sans machine ne veut rien dire.

| | |
|---|---|
| Machine | MacBook Pro `Mac16,1` |
| Processeur | Apple M4, 10 cœurs, arm64 |
| Mémoire | 16 Go unifiés |
| Système | macOS 26.5.1 (25F80) |
| Ollama | 0.34.0 |

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
```

La [dataset card](data/dataset_card.md) est **générée** depuis les données : ses chiffres ne peuvent pas diverger du corpus qu'ils décrivent.

Les PDF sont rendus **depuis `pitch_text`**, en trois mises en page — serif, deux colonnes, sans-serif — parce qu'un corpus où tous les PDF sortent du même gabarit ne teste pas l'extraction, il teste un gabarit. `pitch_text` reste l'entrée de référence du moteur ; l'extraction PDF se vérifie à part (§6).

Le générateur refuse de produire si la distribution, le nombre d'injections, l'ordre des scores, la largeur de la coupure, la répartition sectorielle ou la règle auteur ≠ annotateur ne tiennent plus.

## Annotation

La double annotation à l'aveugle devait fournir la référence du benchmark. Elle n'a plus d'objet depuis le retrait de la comparaison de modèles. Les outils restent dans le dépôt (`scripts/annotate.py`, `scripts/build_reference.py`, et la variante IA décrite dans [`docs/AI_REFERENCE.md`](docs/AI_REFERENCE.md)), mais aucune annotation n'est attendue.

Une règle garde son utilité : **`show_pitch.py` masque la cible de calibration par défaut**. Il faut `--reveal` pour la voir.

## Pipeline

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis remplir les clés — le .env n'est jamais committé
ollama pull deepseek-r1:8b
pytest                        # aucun appel de modèle
```

| Module | Rôle |
|---|---|
| `src/config.py` | Grille, poids, règle de sélection, modèle et ses bornes |
| `src/schemas.py` | Validation Pydantic des sorties, et recalcul du total |
| `src/prompts.py` | V0 / V1 / V2, avec l'empreinte de chaque version |
| `src/score_pitch.py` | Un appel : prompt, modèle, mesure, validation, enregistrement |
| `src/benchmark.py` | Passage sur le corpus, reprenable. Hérité du benchmark, il sert désormais à scorer les 50 pitchs de la démonstration |
| `src/extract.py` | Le texte d'une soumission : message, PDF joints, liens. Chaque échec porte un code, et les liens vers des adresses non publiques sont refusés |
| `src/metrics.py` | Sélection adaptative, classement, Spearman, latences |
| `src/project_status.py` | L'avancement calculé pour le tableau de bord |

```bash
python3 -m src.benchmark --models local --prompts V2 --limit 3   # essai sur 3 pitchs
python3 -m src.benchmark --models local --prompts V2             # les 50 pitchs, ~2 h 50
python3 scripts/check_extraction.py                               # fidélité de l'extraction sur les 50 PDF
```

Trois propriétés à ne pas perdre de vue :

**Le total est recalculé dans le code.** Le modèle annonce un total, gardé dans `total_reported`, mais le score qui fait foi est `total_computed`. Sur P001, le modèle a noté 4/5/4/4/4 (soit 85 une fois pondéré) et annoncé 4,25 : la moyenne non pondérée de ses propres notes.

**Le passage est reprenable.** Chaque appel est écrit dans `results/raw_runs.jsonl` dès qu'il revient, et une relance saute ce qui est déjà fait. Une coupure ne coûte rien.

**Aucune sortie n'est corrigée à la main.** Une réponse invalide est enregistrée comme échec. Le seul nettoyage automatique consiste à retirer le bloc markdown autour du JSON, et il est tracé (`valid_json` contre `valid_json_cleaned`).
