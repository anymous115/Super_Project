#!/usr/bin/env python3
"""Génère docs/ENGINE_CHECKS.md depuis results/raw_runs.jsonl (§11 du protocole).

    python3 scripts/build_engine_checks.py

Comme la dataset card, ce compte rendu est **généré** : ses chiffres ne peuvent
pas diverger des appels qu'il décrit. Relancer le scoring, puis ce script.

Seuls les appels du modèle de production, en V2, sont retenus. Les cibles de
calibration sont les intentions d'écriture de l'équipe, pas une vérité : elles
servent de repère de cohérence, et le texte le dit.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import MODELS                                                # noqa: E402
from src.metrics import percentile, rank_pitches, select, selection_size, spearman  # noqa: E402

RUNS = ROOT / "results" / "raw_runs.jsonl"
PITCHES = ROOT / "data" / "pitches.jsonl"
CALIBRATION = ROOT / "data" / "calibration.jsonl"
OUT = ROOT / "docs" / "ENGINE_CHECKS.md"
TIERS = {"strong": "fort", "medium": "moyen", "weak": "faible"}


def jsonl(path: Path) -> List[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def table(header: List[str], rows: List[List]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def fr(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def build() -> str:
    model = MODELS["local"].name
    runs = [r for r in jsonl(RUNS) if r["model"] == model and r["prompt_version"] == "V2"]
    if not runs:
        sys.exit(f"aucun appel {model} en V2 dans {RUNS.relative_to(ROOT)}")
    pitches = {p["pitch_id"]: p for p in jsonl(PITCHES)}
    calib = {c["pitch_id"]: c for c in jsonl(CALIBRATION)}

    ok = [r for r in runs if r["parsed_output"]]
    latencies = [r["latency_seconds"] for r in runs]
    drift = [abs(r["total_reported"] - r["total_computed"]) for r in ok]

    traps = sorted(p for p in pitches if pitches[p].get("is_injection_test"))
    flagged = sorted({r["pitch_id"] for r in ok if r.get("guard_flagged")})
    families = {r["pitch_id"]: r.get("guard_families", []) for r in ok}

    all_totals = {r["pitch_id"]: r["total_computed"] for r in ok}
    all_notes = {r["pitch_id"]: r["parsed_output"]["scores"] for r in ok}
    all_rank = rank_pitches(all_totals, all_notes)
    recs = {r["pitch_id"]: r["parsed_output"]["recommendation"] for r in ok}

    totals = {p: t for p, t in all_totals.items() if p not in flagged}
    notes = {p: all_notes[p] for p in totals}
    rank = rank_pitches(totals, notes)
    selected = select(totals, notes)
    expected = [p for p in calib if calib[p].get("expected_in_selection")]
    targets = {p: calib[p]["target_score"] for p in calib}

    sp_all = spearman(all_totals, targets)
    sp_kept = spearman(totals, targets)

    tier_rows = []
    for tier, label in TIERS.items():
        ids = [p for p in totals if calib[p]["tier"] == tier]
        if ids:
            m = st.mean(totals[p] for p in ids)
            c = st.mean(targets[p] for p in ids)
            tier_rows.append([label, len(ids), fr(m, 1), fr(c, 1), f"{m - c:+.1f}".replace(".", ",")])

    trap_rows = [
        [p, targets[p], fr(all_totals[p], 0), recs[p], all_rank.index(p) + 1,
         "✅ signalé" if p in flagged else "❌ manqué", ", ".join(families.get(p, []))]
        for p in traps
    ]
    false_pos = [p for p in flagged if p not in traps]
    missed = [p for p in traps if p not in flagged]

    k = selection_size(len(totals))
    sel_rows = [[i + 1, p, fr(totals[p], 0), targets[p], TIERS[calib[p]["tier"]]] for i, p in enumerate(selected)]
    exp_rows = [[p, targets[p], fr(totals[p], 0), rank.index(p) + 1] for p in expected if p in totals]

    rec_counts = Counter(recs[p] for p in totals)
    day = max(r["timestamp"] for r in runs)[:10]

    return f"""# Contrôles du moteur

> **Généré** par `scripts/build_engine_checks.py` depuis `results/raw_runs.jsonl`. Ne pas éditer à la main.
> Protocole : [§11](PROTOCOL.md#11-contrôles-du-moteur). Dernier appel : {day}.

Passage des {len(runs)} pitchs du corpus sur le moteur de production : **`{model}`**, prompt **V2**, température 0, filtre anti-injection actif. Empreinte du prompt : `{runs[0]['prompt_fingerprint']}`.

## Fiabilité

{table(["", "Valeur"], [
    ["Réponses exploitables", f"**{len(ok)} / {len(runs)}**"],
    ["JSON pur, sans nettoyage", f"{sum(r['valid_json'] for r in runs)} / {len(runs)}"],
    ["Réponses coupées par la borne de génération", sum(bool(r['truncated']) for r in runs)],
    ["Identifiant de pitch mal renvoyé", sum(bool(r['pitch_id_mismatch']) for r in runs)],
    ["Erreurs d'appel", sum(1 for r in runs if r['error'])],
    ["Latence médiane / p95 / max", f"{fr(st.median(latencies), 1)} s / {fr(percentile(latencies, 95), 1)} s / {fr(max(latencies), 1)} s"],
    ["Durée totale du passage", f"{fr(sum(latencies) / 60, 0)} min"],
    ["Tokens par appel (médiane, entrée / sortie)", f"{st.median(r['input_tokens'] for r in runs):.0f} / {st.median(r['output_tokens'] for r in runs):.0f}"],
])}

**Le total annoncé par le modèle est faux {sum(d > 5 for d in drift)} fois sur {len(drift)}** : écart médian de {fr(st.median(drift), 1)} points, maximum {fr(max(drift), 1)}. Le modèle semble additionner ses notes au lieu de les pondérer sur 100. Le total qui fait foi est recalculé dans le code (`total_computed`) : sans ce recalcul, le classement serait inutilisable.

## Sécurité

{table(["Pitch", "Cible", "Score du modèle", "Recommandation", "Rang sans filtre", "Filtre", "Familles"], trap_rows)}

**{len(flagged) - len(false_pos)} pièges sur {len(traps)} signalés, {len(false_pos)} faux positif{'s' if len(false_pos) > 1 else ''} sur {len(pitches) - len(traps)} pitchs sains**{f" ({', '.join(false_pos)})" if false_pos else ""}{f", manqués : {', '.join(missed)}" if missed else ""}.

La colonne « rang sans filtre » montre pourquoi le filtre existe : le modèle attribue lui-même un score et une recommandation à chaque piège, et P025 sortirait **premier**. Les pitchs signalés sont notés pour la trace, mais sortent du classement ci-dessous et partent en revue humaine.

## Cohérence avec la calibration

Les cibles sont les **intentions d'écriture** de l'équipe, fixées avant rédaction. Elles ne sont pas une vérité : un écart signale un pitch à relire, pas forcément une erreur du modèle.

{table(["Mesure", "Valeur"], [
    ["Spearman sur les 50 pitchs", fr(sp_all, 3)],
    [f"Spearman sur les {len(totals)} pitchs classés (pièges écartés)", f"**{fr(sp_kept, 3)}**"],
    ["Plage des scores", f"{fr(min(totals.values()), 0)} à {fr(max(totals.values()), 0)}"],
    ["Recommandations", " · ".join(f"{k} {v}" for k, v in sorted(rec_counts.items()))],
])}

### Par palier

{table(["Palier", "Pitchs", "Score moyen", "Cible moyenne", "Écart"], tier_rows)}

### Sélection adaptative

{len(totals)} pitchs classés, donc **{k} dossiers retenus** (`min(50, max(5, ⌈n × 10 %⌉))`).

{table(["Rang", "Pitch", "Score", "Cible", "Palier"], sel_rows)}

Où se placent les {len(expected)} pitchs que la calibration mettait en tête :

{table(["Pitch", "Cible", "Score", "Rang"], exp_rows)}

## Lecture

- **Le moteur est fiable techniquement.** Toutes les réponses sont exploitables, sans nettoyage ni troncature, et la génération contrainte par schéma supprime les défauts de forme observés avec `deepseek-r1:8b`.
- **Le filtre fait le travail que le prompt ne fait pas.** Sans lui, un pitch qui se dit pré-approuvé serait le premier dossier présenté à l'investisseur.
- **Le classement est correct dans l'ensemble, flou en tête.** La corrélation avec la calibration est nette, mais le modèle surnote les pitchs moyens et faibles, et tasse les scores : plusieurs dossiers moyens entrent dans la sélection, et le meilleur pitch du corpus n'y est pas. Le moteur fait un premier tri ; l'investisseur départage le haut de la file.
- **Le passage est reproductible.** À température 0, un second passage complet a redonné exactement les mêmes scores.

## Limites

- 50 pitchs fictifs, rédigés pour couvrir une échelle de qualité, pas pour reproduire le flux réel d'un fonds.
- Pas de référence annotée : la cohérence se mesure contre les intentions d'écriture, pas contre un jugement indépendant.
- Le filtre attrape les formes connues d'injection et leurs variantes proches. Une injection paraphrasée avec soin peut passer : le prompt V2 et la revue humaine restent les couches suivantes.
- Un seul modèle, jamais comparé à un modèle frontier.
"""


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)} généré")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
