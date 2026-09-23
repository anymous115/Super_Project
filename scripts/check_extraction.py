#!/usr/bin/env python3
"""Fidélité de l'extraction PDF sur le corpus (§6 du protocole).

    python3 scripts/check_extraction.py

Chaque PDF est rendu depuis `pitch_text`. Son extraction doit redonner les mêmes
mots dans le même ordre : sinon, un écart de score entre la version texte et la
version PDF d'un pitch viendrait du lecteur de PDF, pas du modèle.

La mesure compare des **suites de mots** (casse et ponctuation ignorées), ce qui
attrape une perte de mots comme une inversion de colonnes.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.extract import ExtractionError, extract_pdf  # noqa: E402

PITCHES = ROOT / "data" / "pitches.jsonl"
PDFS = ROOT / "data" / "pdfs"
THRESHOLD = 0.98


def words(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


def fidelity(source: str, extracted: str) -> float:
    return difflib.SequenceMatcher(None, words(source), words(extracted), autojunk=False).ratio()


def main() -> int:
    from render_pdfs import LAYOUTS

    rows = [json.loads(l) for l in PITCHES.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_layout: dict = {layout: [] for layout in LAYOUTS}
    failures = []
    for row in rows:
        pid = row["pitch_id"]
        layout = LAYOUTS[int(pid[1:]) % len(LAYOUTS)]
        try:
            ratio = fidelity(row["pitch_text"], extract_pdf(PDFS / f"{pid}.pdf"))
        except (ExtractionError, OSError) as exc:
            failures.append((pid, getattr(exc, "code", "missing"), str(exc)))
            continue
        by_layout[layout].append((ratio, pid))

    print(f"{'mise en page':<16}{'PDF':>5}{'min':>8}{'moyenne':>10}")
    for layout, values in by_layout.items():
        if values:
            values.sort()
            mean = sum(r for r, _ in values) / len(values)
            print(f"{layout:<16}{len(values):>5}{values[0][0]:>8.3f}{mean:>10.3f}   (min : {values[0][1]})")
    below = [(pid, r) for v in by_layout.values() for r, pid in v if r < THRESHOLD]
    for pid, code, message in failures:
        print(f"  ✗ {pid} — {code} : {message}")
    for pid, ratio in below:
        print(f"  ! {pid} — fidélité {ratio:.3f} sous le seuil de {THRESHOLD}")
    ok = not failures and not below
    print("\nextraction fidèle sur tout le corpus" if ok else "\nextraction à revoir")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
