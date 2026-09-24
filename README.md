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

Le produit note les pitchs avec **`qwen2.5:14b`**, exécuté en local par Ollama, avec le prompt **V2**, derrière le filtre anti-injection de `src/guard.py`. Aucun coût d'API, et aucun pitch ne quitte la machine.

La comparaison avec un modèle frontier, prévue au départ, a été retirée du projet le 23 septembre 2026 avec l'accord du professeur. `gpt-6-astra` reste déclaré dans `src/config.py`, mais le produit ne l'appelle pas.

### Comment le modèle a été choisi

Trois modèles locaux, mesurés le 23 septembre 2026 sur les 50 pitchs avec le prompt V2. Les cibles de calibration sont les intentions d'écriture de l'équipe, pas une vérité : elles servent de repère de cohérence.

| | `deepseek-r1:8b` | `qwen2.5:7b` | **`qwen2.5:14b`** |
|---|---:|---:|---:|
| Réponses exploitables | **4 / 18**, arrêté | 50 / 50 | **50 / 50** |
| Latence médiane | 230 s | 25 s | **59 s** |
| Spearman contre les cibles | — | 0,57 | **0,73** |
| Pitchs forts dans le top 5 | — | 0 / 5 | 1 / 5 |
| Pitch piégé dans le top 5 | — | non | **oui : P025 premier, 100/100** |

- **`deepseek-r1:8b`** est un modèle de raisonnement : en V2, il épuise 4 096 tokens de réflexion sans écrire sa réponse sur 14 pitchs sur 18. L'option `think: false` d'Ollama est sans effet. Série arrêtée.
- **`qwen2.5:7b`** est rapide et toujours valide, mais il ne distingue pas un bon pitch d'un excellent : aucun des cinq meilleurs dossiers n'entre dans son top 5.
- **`qwen2.5:14b`** ordonne nettement mieux, mais obéit davantage aux injections : P025, qui se dit « pre-approved » et demande 5 sur 5 partout, sort **premier avec 100/100**, malgré la défense V2.

D'où le filtre en amont. Avec lui, les cinq pitchs piégés sortent du classement, et sur les 45 restants **le Spearman monte à 0,75**, avec P005 et P002 dans le top 5, P003 et P004 juste derrière.

**Ce qui reste faible.** Le modèle surnote les pitchs moyens (+19 points en moyenne) et faibles (+30), et tasse les notes entre 60 et 85. Trois pitchs moyens entrent dans le top 5, dont P028, qui présente un volume d'affaires (GMV) comme du chiffre d'affaires. Le moteur fait un bon premier tri, pas un classement fin : c'est l'investisseur qui départage le haut de la file.

### Défense en trois couches

1. **Le filtre** (`src/guard.py`), avant le modèle, sans appel au modèle. Il cherche cinq familles de formules qu'un fondateur honnête n'a aucune raison d'écrire : texte adressé à une IA, ordre d'ignorer la grille, note dictée, évaluation préalable invoquée, faux avis système. Un pitch signalé est noté quand même, pour mesure, mais **sort du classement automatique** et part en revue humaine avec la raison et l'extrait. Sur le corpus : **5 pièges sur 5, 0 faux positif sur 45**. Chaque piège touche au moins trois familles, ce qui laisse de la marge contre la paraphrase.
2. **Le prompt V2**, qui déclare le pitch non fiable, **et un rappel placé après le pitch** : un petit modèle obéit surtout à ce qu'il lit en dernier. Avec `qwen2.5:7b`, ce rappel fait passer P049 de 100 à 61 et P025 de 96 à 77.
3. **La revue humaine** : le score est une aide au tri, jamais une décision.

### Bornes d'exécution

- température 0 ;
- sortie **contrainte par le schéma JSON** de `PitchScore` (option `format` d'Ollama) : 50 réponses sur 50 en JSON pur ;
- `num_ctx` 8192, `num_predict` 2048, chaque appel plafonné à 600 s ;
- un appel d'échauffement au démarrage, non enregistré.

Le modèle occupe 10 Go de mémoire graphique : sur une machine de 16 Go, fermer les applications lourdes pendant un passage.

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
ollama pull qwen2.5:14b
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
| `src/triage.py` | Le chaînon entre la réception et l'interface : chaque soumission de `inbox/` est extraite, filtrée, notée, puis rangée dans sa file (classée, revue humaine, illisible, erreur) |
| `src/guard.py` | Filtre anti-injection, avant le modèle : un pitch signalé sort du classement automatique |
| `src/metrics.py` | Sélection adaptative, classement, Spearman, latences |
| `src/project_status.py` | L'avancement calculé pour le tableau de bord |

```bash
python3 -m src.benchmark --models local --prompts V2 --limit 3   # essai sur 3 pitchs
python3 -m src.benchmark --models local --prompts V2             # les 50 pitchs, ~50 min
python3 scripts/check_extraction.py                               # fidélité de l'extraction sur les 50 PDF
python3 scripts/build_engine_checks.py                            # régénère docs/ENGINE_CHECKS.md depuis les résultats
```

Le compte rendu du dernier passage est dans **[docs/ENGINE_CHECKS.md](docs/ENGINE_CHECKS.md)** : 50 réponses sur 50, 5 pièges sur 5 écartés, Spearman de 0,75 contre la calibration.

### Le parcours complet

```bash
python3 scripts/ingest.py telegram        # terminal 1 : reçoit les pitchs du bot
python3 scripts/ingest.py email           # terminal 2 : relève la boîte dédiée
python3 scripts/score_inbox.py --watch    # terminal 3 : note ce qui arrive, toutes les 30 s
python3 scripts/score_inbox.py queue      # les files : classés (★ sélection), revue humaine, illisibles
```

Chaque soumission de `inbox/SUB-0001/` reçoit un `score.json` à côté de son `submission.json`. `src/triage.load_queue()` rend les files que l'interface affiche. Une soumission déjà notée n'est jamais renotée.

Vérifié de bout en bout avec `qwen2.5:14b` le 24 septembre 2026 : un PDF reçu par Telegram est lu, noté et classé ; P025 reçu par email est noté 100/100 par le modèle, signalé par le filtre, et part en revue humaine.

> **Limite relevée.** Le même pitch (P005) obtient **73 reçu en PDF** et **83 en texte brut**. L'extraction est fidèle au mot près : c'est la mise en forme du texte (sauts de ligne, titres, étiquette de la pièce jointe) qui déplace la note. Deux fondateurs au contenu égal peuvent donc être notés différemment selon le format d'envoi.

Trois propriétés à ne pas perdre de vue :

**Le total est recalculé dans le code.** Le modèle annonce un total, gardé dans `total_reported`, mais le score qui fait foi est `total_computed`. Mesuré sur `qwen2.5:14b` : le total annoncé s'écarte souvent du total pondéré, parfois de plusieurs dizaines de points. `deepseek-r1:8b` renvoyait, lui, la moyenne non pondérée de ses propres notes.

**Le passage est reprenable.** Chaque appel est écrit dans `results/raw_runs.jsonl` dès qu'il revient, et une relance saute ce qui est déjà fait. Une coupure ne coûte rien.

**Aucune sortie n'est corrigée à la main.** Une réponse invalide est enregistrée comme échec. Le seul nettoyage automatique consiste à retirer le bloc markdown autour du JSON, et il est tracé (`valid_json` contre `valid_json_cleaned`).
