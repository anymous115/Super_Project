#!/usr/bin/env python3
"""Annotation à l'aveugle des pitchs (§6 du protocole).

    python3 scripts/annotate.py --who A            # annote ce qui reste
    python3 scripts/annotate.py --who A --status   # où j'en suis
    python3 scripts/annotate.py --who A --only P012

**Pourquoi ce script existe.** `show_pitch.py` affiche la cible de calibration.
Un annotateur qui lit un pitch avec cet outil voit le score qu'on visait en
l'écrivant, et l'annotation ne mesure plus rien. Ici, rien de `calibration.jsonl`
n'est jamais affiché : ni la cible, ni le rang, ni le palier, ni les drapeaux.

Le total pondéré n'apparaît qu'**après** la saisie des cinq notes, pour qu'il
n'ancre pas la sixième décision.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_calibration import ANNOTATORS            # noqa: E402
from src.config import CRITERIA, MAX_NOTE, WEIGHTS  # noqa: E402

PITCHES = ROOT / "data" / "pitches.jsonl"
TEAM = ROOT / "data" / "team.json"
ANNOTATIONS = ROOT / "data" / "annotations"

LABELS = {
    "team": "Équipe — compétences et expérience",
    "market": "Marché — importance, crédibilité, accessibilité",
    "product": "Produit — clarté, différenciation, faisabilité",
    "traction": "Traction — preuves concrètes d'adoption",
    "business_model": "Business model — revenus et go-to-market",
}
SCALE = """  0 rien sur ce critère   1 mentionné, sans appui   2 affirmé, sans preuve
  3 crédible, sans relief  4 preuve précise du texte  5 preuve sur laquelle un fonds agirait"""
RECOMMENDATIONS = ("reject", "review", "shortlist")


def load_pitches() -> Dict[str, dict]:
    return {
        r["pitch_id"]: r
        for r in (json.loads(l) for l in PITCHES.read_text(encoding="utf-8").splitlines() if l.strip())
    }


def my_file(who: str) -> Path:
    return ANNOTATIONS / f"{who}.jsonl"


def already_done(who: str) -> Dict[str, dict]:
    path = my_file(who)
    if not path.exists():
        return {}
    return {
        r["pitch_id"]: r
        for r in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
    }


def assigned_to(who: str, pitches: Dict[str, dict]) -> List[str]:
    """Les pitchs que `who` doit annoter, dans l'ordre des identifiants."""
    return [p for p in sorted(pitches) if who in ANNOTATORS.get(p, ())]


def weighted_total(notes: Dict[str, int]) -> float:
    return sum(notes[c] / MAX_NOTE * WEIGHTS[c] for c in CRITERIA)


# --- Saisie ------------------------------------------------------------------


def ask_note(label: str) -> int:
    while True:
        raw = input(f"  {label}\n  note (0-{MAX_NOTE}) > ").strip()
        if raw.isdigit() and 0 <= int(raw) <= MAX_NOTE:
            return int(raw)
        print(f"  ! une note entière de 0 à {MAX_NOTE}")


def ask_evidence() -> str:
    while True:
        raw = input("  la phrase du pitch qui justifie cette note > ").strip()
        if raw:
            return raw
        print("  ! une note sans justification ne se réconcilie pas — une ligne suffit")


def ask_recommendation() -> str:
    while True:
        raw = input(f"  recommandation ({' / '.join(RECOMMENDATIONS)}) > ").strip().lower()
        if raw in RECOMMENDATIONS:
            return raw
        for r in RECOMMENDATIONS:
            if r.startswith(raw) and raw:
                return r
        print(f"  ! une valeur parmi {', '.join(RECOMMENDATIONS)}")


def annotate_one(who: str, pitch: dict) -> Optional[dict]:
    """Affiche le pitch nu, recueille les cinq notes. None si on abandonne."""
    bar = "─" * 78
    print(f"\n{bar}\n{pitch['pitch_id']} — {pitch['company_name']}\n{bar}\n")
    print(pitch["pitch_text"])
    print(f"\n{bar}\nGrille — " + " · ".join(f"{c.replace('_',' ')} {WEIGHTS[c]}%" for c in CRITERIA))
    print(SCALE)
    print(bar)

    notes, evidence = {}, {}
    try:
        for criterion in CRITERIA:
            notes[criterion] = ask_note(LABELS[criterion])
            evidence[criterion] = ask_evidence()
        total = weighted_total(notes)
        print(f"\n  total pondéré, calculé : {total:.0f}/100")
        recommendation = ask_recommendation()
        comment = input("  remarque libre (facultatif) > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n  interrompu — rien n'est enregistré pour ce pitch")
        return None

    return {
        "pitch_id": pitch["pitch_id"],
        "annotator": who,
        "annotated_at": date.today().isoformat(),
        "scores": notes,
        "evidence": evidence,
        "total_score": round(total, 1),
        "recommendation": recommendation,
        "comment": comment,
    }


def append(who: str, row: dict) -> None:
    path = my_file(who)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


# --- CLI ---------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    team = json.loads(TEAM.read_text(encoding="utf-8")) if TEAM.exists() else {}
    parser = argparse.ArgumentParser(description="Annotation à l'aveugle des pitchs")
    parser.add_argument("--who", required=True, choices=sorted(team) or ["A", "B", "C", "D"])
    parser.add_argument("--only", nargs="*", help="n'annoter que ces identifiants")
    parser.add_argument("--status", action="store_true", help="afficher l'avancement et sortir")
    args = parser.parse_args(argv)

    who = args.who
    pitches = load_pitches()
    mine = assigned_to(who, pitches)
    done = already_done(who)
    todo = [p for p in mine if p not in done]

    name = team.get(who, who)
    print(f"{name} ({who}) — {len(done)}/{len(mine)} annotés, {len(todo)} restants")
    if args.status:
        if todo:
            print("à faire :", " ".join(todo))
        return 0

    if args.only:
        inconnus = [p for p in args.only if p not in mine]
        if inconnus:
            sys.exit(f"{who} n'annote pas {', '.join(inconnus)} — voir CALIBRATION_GRID.md")
        todo = [p for p in args.only if p not in done]

    if not todo:
        print("rien à annoter.")
        return 0

    print("Aucune cible de calibration n'est affichée. Noter sur le texte, rien d'autre.\n")
    for pitch_id in todo:
        pitch = pitches[pitch_id]
        if pitch.get("written_by") == who:
            # Vérifié aussi par build_calibration.py, mais mieux vaut deux verrous.
            print(f"{pitch_id} : {who} en est l'auteur, on passe.")
            continue
        row = annotate_one(who, pitch)
        if row is None:
            break
        append(who, row)
        print(f"  enregistré dans data/annotations/{who}.jsonl")

    restants = len([p for p in mine if p not in already_done(who)])
    print(f"\n{len(mine) - restants}/{len(mine)} annotés — {restants} restants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
