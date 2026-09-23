#!/usr/bin/env python3
"""Génère `data/dataset_card.md` depuis les données (§6 du protocole).

La carte est **générée, jamais éditée à la main** : ses chiffres viennent de
`data/pitches.jsonl` et `data/calibration.jsonl`, donc ils ne peuvent pas
diverger du corpus qu'ils décrivent. Le texte fixe est dans ce script.

    python3 scripts/build_dataset_card.py
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = DATA / "dataset_card.md"

TIER_LABEL = {"strong": "fort", "medium": "moyen", "weak": "faible"}


def read(path: Path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def table(headers, rows, aligns=None):
    aligns = aligns or ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(aligns) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build() -> str:
    pitches = read(DATA / "pitches.jsonl")
    calib = {r["pitch_id"]: r for r in read(DATA / "calibration.jsonl")}
    written = [p for p in pitches if p.get("pitch_text")]
    words = {p["pitch_id"]: len(p["pitch_text"].split()) for p in written}

    by_tier = defaultdict(list)
    for p in written:
        by_tier[calib[p["pitch_id"]]["tier"]].append(p["pitch_id"])

    flags = Counter(f for r in calib.values() for f in r["flags"])
    statuses = Counter(p["review_status"] for p in pitches)
    scores = [r["target_score"] for r in calib.values()]

    # Provenance regroupée par source : 37 pitchs, une quinzaine d'URL.
    by_source = defaultdict(list)
    for p in pitches:
        if p["source_type"] == "derived":
            by_source[(p["source_url"], p["accessed_at"])].append(p["pitch_id"])

    parts = [f"""# Dataset card — corpus de pitchs VC

> **Fichier généré.** Produit par `scripts/build_dataset_card.py` depuis
> `data/pitches.jsonl` et `data/calibration.jsonl`. Ne pas éditer à la main :
> relancer le script. Dernière génération : {date.today().isoformat()}.

## Ce que c'est

{len(pitches)} pitchs de startups **entièrement fictifs**, en anglais, écrits pour mesurer
un moteur de scoring VC. Chaque pitch est du texte libre structuré en sections
— problème, solution, marché, concurrence, équipe, traction, business model,
go-to-market, financement — comme un fondateur l'enverrait par email.

Le corpus alimente le moteur de scoring du produit et sa démonstration : chaque
pitch est noté par le même modèle, avec la même grille, et la file triée qui en
sort est celle que l'interface présente à l'investisseur.

## Composition

{table(["", "Valeur"], [
    ["Pitchs", len(pitches)],
    ["Rédigés", len(written)],
    ["Langue", "anglais (100 %)"],
    ["Longueur", f"{min(words.values())} à {max(words.values())} mots, médiane {int(statistics.median(words.values()))}"],
    ["Scores cibles", f"{min(scores)} à {max(scores)} sur 100"],
    ["Secteurs", len({r['sector'] for r in calib.values()})],
])}

### Par palier

{table(["Palier", "Pitchs", "Scores", "Longueur (mots)"], [
    [TIER_LABEL[t],
     len(by_tier[t]),
     f"{min(calib[p]['target_score'] for p in by_tier[t])}–{max(calib[p]['target_score'] for p in by_tier[t])}",
     f"{min(words[p] for p in by_tier[t])}–{max(words[p] for p in by_tier[t])}"]
    for t in ("strong", "medium", "weak")
], ["---", "---:", "---:", "---:"])}

La longueur ne suit pas le score : les paliers fort et moyen se recouvrent
presque entièrement. Seul le palier faible est court, parce qu'un mauvais pitch
l'est réellement. Un modèle qui noterait à la longueur trouverait le bas du
classement et se tromperait sur tout le reste.

### Cas particuliers

{table(["Marqueur", "Pitchs", "Rôle"], [
    ["💉 injection", flags.get("injection", 0), "contiennent une instruction adressée au modèle évaluateur"],
    ["⚠️ ambigu", flags.get("ambiguous", 0), "désaccord attendu entre deux annotateurs humains"],
    ["␀ info manquante", flags.get("missing_info", 0), "une dimension du dossier est absente, et doit être signalée comme telle"],
], ["---", "---:", "---"])}

Les cinq injections prennent cinq formes distinctes, sans expression commune :
instruction en clair, instruction cachée dans un e-mail cité, note d'un
prétendu évaluateur précédent, faux score de présélection, injonction directe.
Leurs scores honnêtes vont de 12 à 53, donc une défense qui échoue déplace le
score de plusieurs dizaines de points.

**`is_injection_test` reste dans les métadonnées et n'atteint jamais le modèle.**

## Comment il a été construit

Les scores cibles ont été **fixés avant la rédaction**, dans
[`docs/CALIBRATION_GRID.md`](../docs/CALIBRATION_GRID.md). Écrire d'abord et
noter ensuite aurait produit une distribution resserrée au milieu, sur laquelle
ni la corrélation de rang ni le chevauchement du top 5 ne veulent dire
grand-chose.

Trois viviers, parce que tout ce qui est publié est un survivant : les
bibliothèques de decks ne contiennent, par construction, aucun mauvais pitch.

{table(["Palier", "Vivier"], [
    ["fort", "levées récentes documentées"],
    ["moyen", "annuaire YC, levées modestes, échecs récents"],
    ["faible", "**post-mortems d'échec** — la seule source de mauvais pitchs qui existe"],
])}

Pour le palier faible : on lit pourquoi la société est morte, puis on écrit le
pitch **tel qu'il aurait été présenté avant l'échec**, avec les faiblesses déjà
lisibles pour qui sait lire.

{table(["Origine", "Pitchs", "Ce que ça veut dire"], [
    ["dérivé", sum(1 for p in pitches if p["source_type"] == "derived"),
     "structure et ordres de grandeur inspirés d'une société réelle, texte entièrement réécrit"],
    ["synthétique", sum(1 for p in pitches if p["source_type"] == "synthetic"),
     "inventé de bout en bout, sans source"],
], ["---", "---:", "---"])}

## Provenance

Chaque pitch dérivé porte l'URL consultée et sa date. **Aucun contenu n'a été
copié** : les sources ont servi à connaître un secteur, un ordre de grandeur et
un mode d'échec, jamais à fournir du texte.

{table(["Source", "Consultée le", "Pitchs"], [
    [f"[{(url or '').split('/')[2] if url else '—'}]({url})", accessed, " ".join(ids)]
    for (url, accessed), ids in sorted(by_source.items(), key=lambda kv: kv[1][0])
], ["---", "---:", "---"])}

## Usage prévu

Mesurer et comparer des systèmes de scoring automatique de pitchs :
justesse des notes, stabilité du classement, résistance à l'injection,
signalement de l'information manquante.

## Limites

**Ce n'est pas un échantillon de pitchs réels.** Les textes sont écrits pour
couvrir une échelle de qualité, pas pour reproduire la distribution qu'un fonds
reçoit vraiment — laquelle est bien plus concentrée dans le bas.

**Le corpus a été rédigé par un modèle de langage**, relu et corrigé par
l'équipe. Un modèle de la même famille le noterait en partie sur sa propre
cohérence : c'est la raison pour laquelle aucun modèle Anthropic ne sert de
moteur de scoring.

**Un seul secteur géographique et une seule langue.** Les pitchs sont anglophones
et les repères de marché européens et nord-américains.

**{sum(1 for p in pitches if p['review_status'] != 'validated')} pitchs sur {len(pitches)} sont encore en `{max(statuses, key=statuses.get)}`** : rédigés,
pas validés.

**Pas de scores de référence annotés.** La double annotation prévue a été
abandonnée avec la comparaison de modèles (23 septembre 2026). Les cibles de
`calibration.jsonl` sont les intentions d'écriture de l'équipe : elles servent
de repère de cohérence, pas de vérité.

## Réutilisation

Les sociétés sont fictives. Les noms, les chiffres et les personnes citées sont
inventés — **aucun pitch ne doit jamais être présenté comme une entreprise
réelle**, et aucun n'est une évaluation d'une société existante.

Le corpus ne contient ni adresse e-mail, ni URL, ni numéro de téléphone, ni nom
de personne réelle. C'est vérifié par un test (`tests/test_corpus.py`).

> ⚠️ **Licence à décider.** Le dépôt n'a pas de fichier `LICENSE`. Tant qu'il n'en
> a pas, le corpus n'est pas réutilisable par un tiers, même s'il est public.

## Fichiers

{table(["Fichier", "Contenu"], [
    ["`data/pitches.jsonl`", "les pitchs, leur provenance et leur statut"],
    ["`data/calibration.jsonl`", "les scores cibles — généré, lecture seule"],
    ["`data/pdfs/`", "les 50 PDF, rendus depuis `pitch_text` en trois mises en page"],
])}
"""]
    return "\n".join(parts)


def main() -> int:
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"{OUTPUT.relative_to(ROOT)} généré — {len(build().splitlines())} lignes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
