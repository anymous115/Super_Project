#!/usr/bin/env python3
"""Affiche un ou plusieurs pitchs de data/pitches.jsonl en lisible.

    python3 scripts/show_pitch.py P005 P006
    python3 scripts/show_pitch.py P005 P006 --md > docs/lecture.md
    python3 scripts/show_pitch.py P005 --reveal      # avec la cible de calibration

Sans argument, liste les pitchs déjà rédigés.

**La cible est masquée par défaut.** Elle a longtemps été affichée, ce qui
rendait toute annotation faite avec cet outil inutilisable : on ne peut pas
noter à l'aveugle un pitch dont on vient de lire le score visé. Pour annoter,
utiliser `scripts/annotate.py`, qui ne lit jamais calibration.jsonl.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PITCHES = ROOT / "data" / "pitches.jsonl"
CALIB = ROOT / "data" / "calibration.jsonl"


def load(path):
    return {r["pitch_id"]: r for r in
            (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines())}


def render(row, cal, markdown, reveal=False):
    head = f"{row['pitch_id']} — {row['company_name'] or '(sans nom)'}"
    meta = cal["sector"]
    if reveal:
        meta += (f" · cible {cal['target_score']}/100 · rang {cal['rank']}"
                 f" · {'RETENU' if cal['expected_in_selection'] else 'non retenu'}")
    if markdown:
        out = [f"## {head}", "", f"*{meta}*", ""]
        if row.get("source_note"):
            out += [f"**Source :** {row['source_note']}", ""]
        out += ["```text", row["pitch_text"] or "(pas encore rédigé)", "```", ""]
        return "\n".join(out)
    bar = "─" * 72
    out = [bar, head, meta]
    if row.get("source_note"):
        out.append(f"Source : {row['source_note']}")
    out += [bar, "", row["pitch_text"] or "(pas encore rédigé)", ""]
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    markdown = "--md" in sys.argv
    reveal = "--reveal" in sys.argv

    pitches, calib = load(PITCHES), load(CALIB)

    if not args:
        done = [p for p, r in sorted(pitches.items()) if r.get("pitch_text")]
        print(f"{len(done)} pitchs rédigés : {' '.join(done)}")
        print("\nUsage : python3 scripts/show_pitch.py P005 P006")
        print("Pour annoter à l'aveugle : python3 scripts/annotate.py --who A")
        return

    missing = [a for a in args if a not in pitches]
    if missing:
        sys.exit(f"identifiant inconnu : {', '.join(missing)}")

    if markdown:
        print("# Lecture\n")
    for pid in args:
        print(render(pitches[pid], calib[pid], markdown, reveal))


if __name__ == "__main__":
    main()
