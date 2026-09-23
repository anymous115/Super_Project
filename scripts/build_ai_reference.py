#!/usr/bin/env python3
"""Référence IA et mesure de son accord avec les humains (docs/AI_REFERENCE.md).

    python3 scripts/build_ai_reference.py --report   # l'accord, sans rien écrire
    python3 scripts/build_ai_reference.py            # écrit la référence et le rapport

La référence du benchmark devient les notes de l'IA tierce sur les 50 pitchs.
Ce n'est défendable que si l'IA s'accorde avec les humains **à peu près autant
que les humains entre eux**. L'échantillon humain sert à le mesurer, et le
critère d'acceptation est fixé ici, avant d'avoir vu les résultats.
"""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import CRITERIA, MAX_NOTE, WEIGHTS  # noqa: E402
from src.metrics import spearman                     # noqa: E402

ANNOTATIONS = ROOT / "data" / "annotations"
AI_DIR = ANNOTATIONS / "ai"
CALIBRATION = ROOT / "data" / "calibration.jsonl"
OUTPUT = ROOT / "data" / "reference_scores.jsonl"
REPORT = AI_DIR / "agreement.json"
DEFAULT_MODEL = "gemini-3.8-flash"

# Échantillon de validation : 12 pitchs, chacun annoté par deux humains, pour
# disposer d'un plafond humain-humain. Tous dans les binômes prévus, donc
# annotate.py les accepte tels quels. Couvre les trois paliers et deux injections.
VALIDATION_SAMPLE = {
    "A": ["P020", "P022", "P025", "P026", "P036", "P039", "P041", "P042"],
    "C": ["P010", "P012", "P015", "P018", "P020", "P022", "P025", "P026"],
    "D": ["P010", "P012", "P015", "P018", "P036", "P039", "P041", "P042"],
}

# Critère d'acceptation, fixé avant la mesure.
MAX_EXTRA_GAP = 0.30      # l'écart IA-humain ne dépasse l'écart humain-humain que de 0,3 point
MIN_SPEARMAN = 0.70       # le classement IA suit celui des humains


def read_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def weighted_total(notes: Dict[str, float]) -> float:
    return sum(notes[c] / MAX_NOTE * WEIGHTS[c] for c in CRITERIA)


def load_humans() -> Dict[str, Dict[str, dict]]:
    """{pitch_id: {annotateur: annotation}}, fichiers A-D uniquement."""
    out: Dict[str, Dict[str, dict]] = {}
    for path in sorted(ANNOTATIONS.glob("[A-D].jsonl")):
        for row in read_jsonl(path):
            out.setdefault(row["pitch_id"], {})[row["annotator"]] = row
    return out


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def criterion_gaps(a: dict, b: dict) -> List[int]:
    return [abs(a["scores"][c] - b["scores"][c]) for c in CRITERIA]


def agreement(ai: Dict[str, dict], humans: Dict[str, Dict[str, dict]]) -> dict:
    hh_gaps: List[int] = []
    ah_gaps: List[int] = []
    ah_total: List[float] = []
    rec_hits: List[bool] = []
    ai_totals: Dict[str, float] = {}
    human_totals: Dict[str, float] = {}
    per_pitch = []

    for pitch_id, by_who in sorted(humans.items()):
        if pitch_id not in ai:
            continue
        people = list(by_who.values())
        for a, b in combinations(people, 2):
            hh_gaps += criterion_gaps(a, b)
        for h in people:
            ah_gaps += criterion_gaps(ai[pitch_id], h)
            rec_hits.append(ai[pitch_id]["recommendation"] == h["recommendation"])
        human_mean = {c: mean([h["scores"][c] for h in people]) for c in CRITERIA}
        human_totals[pitch_id] = weighted_total(human_mean)
        ai_totals[pitch_id] = ai[pitch_id]["total_score"]
        ah_total.append(abs(ai_totals[pitch_id] - human_totals[pitch_id]))
        per_pitch.append({
            "pitch_id": pitch_id,
            "humans": sorted(by_who),
            "ai_total": ai_totals[pitch_id],
            "human_total": round(human_totals[pitch_id], 1),
        })

    result = {
        "pitches_compared": len(per_pitch),
        "human_human_gap": round(mean(hh_gaps), 3) if hh_gaps else None,
        "human_human_within_1": round(mean([g <= 1 for g in hh_gaps]), 3) if hh_gaps else None,
        "ai_human_gap": round(mean(ah_gaps), 3) if ah_gaps else None,
        "ai_human_within_1": round(mean([g <= 1 for g in ah_gaps]), 3) if ah_gaps else None,
        "ai_human_total_mae": round(mean(ah_total), 2) if ah_total else None,
        "ai_human_recommendation_agreement": round(mean(rec_hits), 3) if rec_hits else None,
        "ai_human_spearman": round(spearman(ai_totals, human_totals), 3) if len(ai_totals) > 2 else None,
        "per_pitch": per_pitch,
        "criteria": {"max_extra_gap": MAX_EXTRA_GAP, "min_spearman": MIN_SPEARMAN},
    }
    if result["human_human_gap"] is None or result["ai_human_spearman"] is None:
        result["verdict"] = "insufficient"
    else:
        ok = (result["ai_human_gap"] <= result["human_human_gap"] + MAX_EXTRA_GAP
              and result["ai_human_spearman"] >= MIN_SPEARMAN)
        result["verdict"] = "accepted" if ok else "rejected"
    return result


def calibration_check(ai: Dict[str, dict]) -> Optional[float]:
    """Bonus : les pitchs ont-ils été écrits au niveau visé ? (pas une référence)"""
    targets = {r["pitch_id"]: r["target_score"] for r in read_jsonl(CALIBRATION)}
    totals = {p: r["total_score"] for p, r in ai.items()}
    return round(spearman(totals, targets), 3) if len(set(totals) & set(targets)) > 2 else None


def print_report(result: dict, n_ai: int, calib: Optional[float]) -> None:
    print(f"IA : {n_ai}/50 pitchs notés · comparés aux humains : {result['pitches_compared']}")
    if result["verdict"] == "insufficient":
        print("\nPas encore assez d'annotations humaines doubles pour juger.")
        for who, ids in VALIDATION_SAMPLE.items():
            print(f"  {who} : python3 scripts/annotate.py --who {who} --only {' '.join(ids)}")
    else:
        print(f"\n  écart moyen par critère   humain-humain {result['human_human_gap']:.2f}"
              f"   IA-humain {result['ai_human_gap']:.2f}   (tolérance +{MAX_EXTRA_GAP})")
        print(f"  notes à 1 point près      humain-humain {result['human_human_within_1']:.0%}"
              f"   IA-humain {result['ai_human_within_1']:.0%}")
        print(f"  Spearman IA / humains     {result['ai_human_spearman']:.2f}   (seuil {MIN_SPEARMAN})")
        print(f"  MAE du total              {result['ai_human_total_mae']:.1f} points sur 100")
        print(f"  même recommandation       {result['ai_human_recommendation_agreement']:.0%}")
        print(f"\n  verdict : {result['verdict'].upper()}")
    if calib is not None:
        print(f"\n  bonus — Spearman IA / cibles de calibration : {calib:.2f}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Référence IA et accord avec les humains")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--report", action="store_true", help="afficher sans écrire")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(ROOT / "scripts"))
    from annotate_ai import out_file  # noqa: E402

    ai = {r["pitch_id"]: r for r in read_jsonl(out_file(args.model))}
    result = agreement(ai, load_humans())
    calib = calibration_check(ai)
    print_report(result, len(ai), calib)

    if args.report:
        return 0
    if len(ai) < 50:
        print(f"\nRéférence non écrite : il manque {50 - len(ai)} pitchs notés par l'IA.")
        return 1
    if result["verdict"] != "accepted":
        print("\nRéférence non écrite : l'accord avec les humains n'est pas établi. "
              "Voir docs/AI_REFERENCE.md, « Si le verdict est négatif ».")
        return 1

    rows = [{
        "pitch_id": p,
        "scores": {c: float(r["scores"][c]) for c in CRITERIA},
        "total_score": r["total_score"],
        "recommendation": r["recommendation"],
        "source": "ai",
        "annotator": r["annotator"],
        "evidence": r["evidence"],
    } for p, r in sorted(ai.items())]
    OUTPUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                      encoding="utf-8")
    REPORT.write_text(json.dumps({**result, "calibration_spearman": calib, "model": args.model},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(rows)} lignes écrites dans {OUTPUT.relative_to(ROOT)}"
          f" · rapport dans {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
