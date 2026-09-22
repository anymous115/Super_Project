#!/usr/bin/env python3
"""Génère les fichiers de données à partir de docs/CALIBRATION_GRID.md.

Le Markdown est la source de vérité : il est lu et discuté par l'équipe.
Le JSON en est dérivé, jamais édité à la main. Toute modification de la
calibration se fait dans le Markdown, puis on relance ce script.

    python3 scripts/build_calibration.py

Produit :
    data/calibration.jsonl  — la cible de chaque pitch (lecture seule)
    data/pitches.jsonl      — le squelette à remplir par les rédacteurs

Sort en erreur si les invariants de la grille ne sont pas respectés.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "docs" / "CALIBRATION_GRID.md"
DATA = ROOT / "data"

TIERS = {
    "Palier fort": "strong",
    "Palier moyen": "medium",
    "Palier faible": "weak",
}

FLAGS = {"💉": "injection", "⚠️": "ambiguous", "␀": "missing_info"}

# Attendu par la grille, vérifié après parsing.
EXPECTED = {
    "total": 50,
    "tiers": {"strong": 12, "medium": 26, "weak": 12},
    "injection": 5,
    "ambiguous": 5,
    "missing_info": 12,
    "selected": 5,
}

ROW = re.compile(
    r"^\|\s*(P\d{3})\s*\|\s*([^|]+?)\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|"
    r"\s*([DS])\s*\|\s*([^|]*?)\s*\|\s*(.+?)\s*\|\s*$"
)


def clean(text):
    """Retire le balisage Markdown d'une cellule."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_grid(path):
    rows, tier = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            heading = line[4:]
            tier = next((v for k, v in TIERS.items() if heading.startswith(k)), None)
            continue
        match = ROW.match(line)
        if not match or tier is None:
            continue
        pitch_id, sector, score, origin, flag_cell, profile = match.groups()
        flags = sorted({FLAGS[s] for s in FLAGS if s in flag_cell})
        rows.append({
            "pitch_id": pitch_id,
            "sector": clean(sector),
            "tier": tier,
            "target_score": int(score),
            "origin": "derived" if origin == "D" else "synthetic",
            "flags": flags,
            "profile": clean(profile),
        })
    return rows


def validate(rows):
    """Vérifie les invariants annoncés par la grille. Retourne la liste des écarts."""
    errors = []

    def check(label, actual, expected):
        if actual != expected:
            errors.append(f"{label} : {actual}, attendu {expected}")

    check("total", len(rows), EXPECTED["total"])

    ids = [r["pitch_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errors.append("identifiants dupliqués")
    if ids != sorted(ids):
        errors.append("identifiants non ordonnés")

    for tier, expected in EXPECTED["tiers"].items():
        check(f"palier {tier}", sum(r["tier"] == tier for r in rows), expected)

    for flag in ("injection", "ambiguous", "missing_info"):
        check(flag, sum(flag in r["flags"] for r in rows), EXPECTED[flag])

    scores = [r["target_score"] for r in rows]
    if scores != sorted(scores, reverse=True):
        errors.append("scores non décroissants — l'ordre des lignes doit être le classement")

    # La coupure : le 5e retenu et le 1er recalé doivent être serrés,
    # sinon le test de discrimination ne teste rien.
    if len(scores) > EXPECTED["selected"]:
        cut = scores[EXPECTED["selected"] - 1] - scores[EXPECTED["selected"]]
        if cut > 3:
            errors.append(f"coupure trop large : {cut} points entre le 5e et le 6e")

    # Aucun secteur ne doit vivre dans un seul palier, sinon le secteur
    # devient un raccourci vers la note.
    for sector in {r["sector"] for r in rows}:
        tiers = {r["tier"] for r in rows if r["sector"] == sector}
        count = sum(r["sector"] == sector for r in rows)
        if count > 1 and len(tiers) == 1:
            errors.append(f"secteur « {sector} » confiné au palier {tiers.pop()}")

    # Deux graphies du même secteur le feraient compter deux fois, ce qui
    # masquerait un confinement. On les repère par préfixe.
    sectors = sorted({r["sector"] for r in rows})
    for short in sectors:
        for long in sectors:
            if short != long and long.startswith(short):
                errors.append(f"secteurs à unifier : « {short} » et « {long} »")

    # Une injection sur un pitch fort rendrait l'attaque illisible.
    for row in rows:
        if "injection" in row["flags"] and row["tier"] == "strong":
            errors.append(f"{row['pitch_id']} : injection sur un pitch fort")

    return errors


def check_written_pitches():
    """Contrôle les pitchs déjà rédigés. Avertit sans bloquer."""
    path = DATA / "pitches.jsonl"
    if not path.exists():
        return
    written = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("pitch_text"):
            words = len(row["pitch_text"].split())
            written.append((row["pitch_id"], words))
            if words > 800:
                print(f"  ! {row['pitch_id']} : {words} mots, plafond 800", file=sys.stderr)
    if written:
        print(f"rédigés   — {len(written)}/50 "
              f"({', '.join(f'{i} {w}m' for i, w in written[:5])}"
              f"{'…' if len(written) > 5 else ''})")


def main():
    if not GRID.exists():
        sys.exit(f"introuvable : {GRID}")

    rows = parse_grid(GRID)
    errors = validate(rows)

    if errors:
        print("Invariants non respectés :", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    check_written_pitches()

    DATA.mkdir(exist_ok=True)

    selected = {r["pitch_id"] for r in rows[: EXPECTED["selected"]]}
    with (DATA / "calibration.jsonl").open("w", encoding="utf-8") as fh:
        for rank, row in enumerate(rows, start=1):
            fh.write(json.dumps({
                **row,
                "rank": rank,
                "expected_in_selection": row["pitch_id"] in selected,
            }, ensure_ascii=False) + "\n")

    # Squelette de rédaction. Ne jamais écraser un travail déjà commencé.
    skeleton = DATA / "pitches.jsonl"
    if skeleton.exists():
        print(f"{skeleton.name} existe déjà — laissé intact")
    else:
        with skeleton.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps({
                    "pitch_id": row["pitch_id"],
                    "company_name": None,
                    "sector": row["sector"],
                    "pitch_text": None,
                    "source_type": row["origin"],
                    "source_url": None,
                    "accessed_at": None,
                    "source_note": None,
                    "is_injection_test": "injection" in row["flags"],
                    "review_status": "pending",
                    "written_by": None,
                }, ensure_ascii=False) + "\n")

    by_tier = {t: sum(r["tier"] == t for r in rows) for t in EXPECTED["tiers"]}
    print(f"{len(rows)} pitchs — {by_tier['strong']} forts, "
          f"{by_tier['medium']} moyens, {by_tier['weak']} faibles")
    print(f"origines  — {sum(r['origin']=='derived' for r in rows)} dérivés, "
          f"{sum(r['origin']=='synthetic' for r in rows)} synthétiques")
    print(f"secteurs  — {len({r['sector'] for r in rows})} distincts")
    print(f"coupure   — {rows[4]['pitch_id']} ({rows[4]['target_score']}) retenu / "
          f"{rows[5]['pitch_id']} ({rows[5]['target_score']}) recalé")
    print("invariants respectés")


if __name__ == "__main__":
    main()
