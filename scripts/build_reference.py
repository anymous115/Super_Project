#!/usr/bin/env python3
"""Fusionne les annotations en `data/reference_scores.jsonl` (§6 du protocole).

    python3 scripts/build_reference.py --report   # l'état, sans rien écrire
    python3 scripts/build_reference.py            # produit la référence

Règles appliquées :

1. chaque pitch doit porter les **deux** annotations du binôme prévu ;
2. tout écart **> 1 point sur 5** sur un critère se discute et se tranche — il
   n'est pas moyenné en douce ;
3. les cas tranchés sont consignés dans `data/annotations/reconciliation.jsonl`,
   avec la raison ;
4. en dessous du seuil, la référence est la moyenne des deux notes.

Le script refuse de produire tant qu'un désaccord reste ouvert. Une référence
qui moyenne un désaccord de 3 points n'est pas une référence, c'est un chiffre.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_calibration import ANNOTATORS            # noqa: E402
from src.config import CRITERIA, MAX_NOTE, WEIGHTS  # noqa: E402

ANNOTATIONS = ROOT / "data" / "annotations"
RECONCILIATION = ANNOTATIONS / "reconciliation.jsonl"
OUTPUT = ROOT / "data" / "reference_scores.jsonl"

GAP_THRESHOLD = 1          # au-delà, on discute (§6)
SEVERITY = {"reject": 0, "review": 1, "shortlist": 2}


def read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_annotations() -> Dict[str, Dict[str, dict]]:
    """{pitch_id: {annotateur: annotation}}"""
    out: Dict[str, Dict[str, dict]] = {}
    for path in sorted(ANNOTATIONS.glob("*.jsonl")):
        if path.name == RECONCILIATION.name:
            continue
        for row in read_jsonl(path):
            out.setdefault(row["pitch_id"], {})[row["annotator"]] = row
    return out


def weighted_total(notes: Dict[str, float]) -> float:
    return sum(notes[c] / MAX_NOTE * WEIGHTS[c] for c in CRITERIA)


def gaps(a: dict, b: dict) -> Dict[str, int]:
    return {c: abs(a["scores"][c] - b["scores"][c]) for c in CRITERIA}


def merge(pitch_id: str, pair: Tuple[str, str], found: Dict[str, dict],
          settled: Dict[str, dict]) -> dict:
    """Une ligne de référence, ou un statut qui dit ce qui manque."""
    missing = [who for who in pair if who not in found]
    if missing:
        return {"pitch_id": pitch_id, "status": "incomplete", "missing": missing}

    first, second = found[pair[0]], found[pair[1]]
    by_criterion = gaps(first, second)
    worst = max(by_criterion.values())
    disputed = sorted(c for c, g in by_criterion.items() if g > GAP_THRESHOLD)

    if disputed and pitch_id not in settled:
        return {
            "pitch_id": pitch_id,
            "status": "disputed",
            "annotators": list(pair),
            "criteria": disputed,
            "max_gap": worst,
        }

    if pitch_id in settled:
        notes = {c: float(settled[pitch_id]["scores"][c]) for c in CRITERIA}
        status = "reconciled"
    else:
        notes = {c: (first["scores"][c] + second["scores"][c]) / 2 for c in CRITERIA}
        status = "agreed"

    recommendations = [first["recommendation"], second["recommendation"]]
    # En cas de désaccord, la référence retient la plus prudente et le signale.
    chosen = min(recommendations, key=lambda r: SEVERITY[r])

    return {
        "pitch_id": pitch_id,
        "scores": notes,
        "total_score": round(weighted_total(notes), 1),
        "recommendation": chosen,
        "recommendation_disputed": recommendations[0] != recommendations[1],
        "annotators": list(pair),
        "max_gap": worst,
        "status": status,
        "evidence": {who: found[who]["evidence"] for who in pair},
    }


def build(pitch_ids: List[str]) -> Tuple[List[dict], List[dict]]:
    found = load_annotations()
    settled = {r["pitch_id"]: r for r in read_jsonl(RECONCILIATION)}
    rows, blocked = [], []
    for pitch_id in pitch_ids:
        pair = ANNOTATORS[pitch_id]
        row = merge(pitch_id, pair, found.get(pitch_id, {}), settled)
        (blocked if row.get("status") in ("incomplete", "disputed") else rows).append(row)
    return rows, blocked


def report(rows: List[dict], blocked: List[dict], total: int) -> None:
    done = len(rows)
    print(f"{done}/{total} pitchs avec une référence utilisable")

    incomplete = [b for b in blocked if b["status"] == "incomplete"]
    disputed = [b for b in blocked if b["status"] == "disputed"]

    if incomplete:
        manquants: Dict[str, List[str]] = {}
        for b in incomplete:
            for who in b["missing"]:
                manquants.setdefault(who, []).append(b["pitch_id"])
        print(f"\n{len(incomplete)} pitchs incomplets :")
        for who, ids in sorted(manquants.items()):
            print(f"  {who} doit encore annoter {len(ids)} pitchs — {' '.join(ids)}")

    if disputed:
        print(f"\n{len(disputed)} désaccords à trancher (écart > {GAP_THRESHOLD} sur 5) :")
        for b in sorted(disputed, key=lambda r: -r["max_gap"]):
            print(f"  {b['pitch_id']} — {'+'.join(b['annotators'])} — écart {b['max_gap']} "
                  f"sur {', '.join(b['criteria'])}")
        print(f"\n  Une fois discutés, consigner la note retenue et la raison dans")
        print(f"  {RECONCILIATION.relative_to(ROOT)} :")
        print('  {"pitch_id": "P0XX", "scores": {"team": 3, "market": 4, "product": 3,'
              ' "traction": 2, "business_model": 3}, "reason": "..."}')

    if rows:
        agreed = sum(1 for r in rows if r["status"] == "agreed")
        ecarts = [r["max_gap"] for r in rows]
        print(f"\naccord direct sur {agreed}/{len(rows)} · "
              f"écart maximal moyen {sum(ecarts)/len(ecarts):.2f} sur 5")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Construit les scores de référence")
    parser.add_argument("--report", action="store_true", help="afficher l'état sans écrire")
    args = parser.parse_args(argv)

    pitch_ids = sorted(ANNOTATORS)
    rows, blocked = build(pitch_ids)
    report(rows, blocked, len(pitch_ids))

    if args.report:
        return 0
    if blocked:
        print(f"\n{OUTPUT.relative_to(ROOT)} n'est pas écrit : "
              f"{len(blocked)} pitchs ne sont pas réglés.")
        return 1

    OUTPUT.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8"
    )
    print(f"\n{len(rows)} lignes écrites dans {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
