"""La matrice du P8 : 2 modèles x 3 prompts x 50 pitchs x 3 répétitions (§10).

900 appels au total, 450 côté frontier. La série est reprenable : chaque appel
est écrit dans `results/raw_runs.jsonl` dès qu'il revient, et un relancement
saute ce qui est déjà fait. Une coupure de réseau ne coûte donc pas la série.

    python3 -m src.benchmark --models local --prompts V0 --repetitions 1
    python3 -m src.benchmark --summary
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .config import DATA, MODELS, PROMPT_VERSIONS, REPETITIONS, RESULTS
from .metrics import (
    injection_score_shift,
    mae,
    percentile,
    rate,
    recommendation_agreement,
    spearman,
    top_k_overlap,
)
from .score_pitch import RAW_RUNS, append_run, load_pitches, score_pitch

SUMMARY = RESULTS / "benchmark_summary.csv"
REFERENCE = DATA / "reference_scores.jsonl"

Cell = Tuple[str, str, str, int]   # (pitch_id, model, prompt_version, repetition)


# --- Reprise -----------------------------------------------------------------


def completed_cells(path: Optional[Path] = None) -> Set[Cell]:
    """Ce qui est déjà mesuré, pour ne pas le repayer."""
    path = path or RAW_RUNS
    if not path.exists():
        return set()
    done: Set[Cell] = set()
    counts: Dict[Tuple[str, str, str], int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row["pitch_id"], row["model"], row["prompt_version"])
        counts[key] = counts.get(key, 0) + 1
        done.add((*key, counts[key]))
    return done


# --- Exécution ---------------------------------------------------------------


def warm_up(model_key: str, pitch: Dict[str, Any]) -> None:
    """Un appel d'échauffement, exclu des mesures (§10). Non enregistré."""
    score_pitch(pitch, model_key, "V0", trace=False)


def run_matrix(
    model_keys: Iterable[str] = ("local", "frontier"),
    prompt_versions: Iterable[str] = PROMPT_VERSIONS,
    repetitions: int = REPETITIONS,
    pitches: Optional[List[Dict[str, Any]]] = None,
    resume: bool = True,
) -> int:
    """Parcourt la matrice. Renvoie le nombre d'appels réellement effectués."""
    pitches = pitches if pitches is not None else load_pitches()
    done = completed_cells() if resume else set()
    performed = 0

    for model_key in model_keys:
        model = MODELS[model_key]
        if model.backend == "ollama" and pitches:
            print(f"échauffement {model.name}…", file=sys.stderr)
            warm_up(model_key, pitches[0])

        for prompt_version in prompt_versions:
            for repetition in range(1, repetitions + 1):
                for pitch in pitches:
                    cell = (pitch["pitch_id"], model.name, prompt_version, repetition)
                    if cell in done:
                        continue
                    record = score_pitch(pitch, model_key, prompt_version)
                    append_run(record)
                    performed += 1
                    flag = "ok" if record.valid_json else "JSON invalide"
                    print(
                        f"{model.name} {prompt_version} r{repetition} "
                        f"{pitch['pitch_id']} — {record.latency_seconds}s — {flag}",
                        file=sys.stderr,
                    )
    return performed


# --- Référence ---------------------------------------------------------------


def load_reference(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Les scores de référence, issus de la double annotation (§6).

    Ce fichier n'est pas une copie de `calibration.jsonl` : les cibles de
    calibration ont servi à garantir l'étalement des scores avant rédaction,
    elles ne sont pas la vérité. La vérité sort de l'annotation à l'aveugle.
    """
    path = path or REFERENCE
    if not path.exists():
        raise FileNotFoundError(
            f"{path} n'existe pas encore. Il est produit par la double annotation "
            "(phase 2). Tant qu'il manque, le benchmark peut tourner mais pas être noté."
        )
    return {
        row["pitch_id"]: row
        for row in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
    }


# --- Agrégation --------------------------------------------------------------


def summarise(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Une ligne par couple (modèle, version de prompt)."""
    path = path or RAW_RUNS
    if not path.exists():
        raise FileNotFoundError(f"{path} n'existe pas — lancer la matrice d'abord.")

    runs: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        runs.setdefault((row["model"], row["prompt_version"]), []).append(row)

    reference = load_reference()
    ref_totals = {p: r["total_score"] for p, r in reference.items()}
    ref_recs = {p: r["recommendation"] for p, r in reference.items() if "recommendation" in r}
    traps = [r["pitch_id"] for r in load_pitches() if r.get("is_injection_test")]

    rows: List[Dict[str, Any]] = []
    for (model, prompt_version), cells in sorted(runs.items()):
        valid = [c for c in cells if c["parsed_output"]]
        # Moyenne des répétitions par pitch, pour ne pas compter trois fois un pitch.
        totals: Dict[str, List[float]] = {}
        recs: Dict[str, str] = {}
        for c in valid:
            totals.setdefault(c["pitch_id"], []).append(c["total_computed"])
            recs[c["pitch_id"]] = c["parsed_output"]["recommendation"]
        predicted = {p: sum(v) / len(v) for p, v in totals.items()}
        latencies = [c["latency_seconds"] for c in cells]

        row: Dict[str, Any] = {
            "model": model,
            "prompt_version": prompt_version,
            "calls": len(cells),
            "valid_json_rate": round(rate(c["valid_json"] for c in cells), 3),
            "valid_after_cleanup_rate": round(rate(c["valid_json_cleaned"] for c in cells), 3),
            "latency_p50": round(percentile(latencies, 50), 2),
            "latency_p95": round(percentile(latencies, 95), 2),
            "input_tokens": sum(c["input_tokens"] for c in cells),
            "output_tokens": sum(c["output_tokens"] for c in cells),
            "cost_usd": round(sum(c["estimated_cost"] for c in cells), 4),
        }
        if predicted:
            row["mae_total"] = round(mae(predicted, ref_totals), 2)
            row["spearman"] = round(spearman(predicted, ref_totals), 3)
            row["top5_overlap"] = round(top_k_overlap(predicted, ref_totals), 2)
            if ref_recs:
                row["recommendation_agreement"] = round(
                    recommendation_agreement(recs, ref_recs), 3
                )
            shifts = injection_score_shift(predicted, ref_totals, traps)
            if shifts:
                row["injection_max_shift"] = round(max(shifts.values()), 1)
        rows.append(row)
    return rows


def write_summary(rows: List[Dict[str, Any]], path: Optional[Path] = None) -> Path:
    path = path or SUMMARY
    path.parent.mkdir(parents=True, exist_ok=True)
    columns: List[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


# --- CLI ---------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark P8 — qualité, coût, latence")
    parser.add_argument("--models", nargs="*", default=["local", "frontier"], choices=list(MODELS))
    parser.add_argument("--prompts", nargs="*", default=list(PROMPT_VERSIONS), choices=list(PROMPT_VERSIONS))
    parser.add_argument("--repetitions", type=int, default=REPETITIONS)
    parser.add_argument("--limit", type=int, default=None, help="n'utiliser que les N premiers pitchs")
    parser.add_argument("--no-resume", action="store_true", help="tout refaire, même ce qui est mesuré")
    parser.add_argument("--summary", action="store_true", help="agréger sans rien relancer")
    args = parser.parse_args(argv)

    if args.summary:
        rows = summarise()
        path = write_summary(rows)
        print(f"{len(rows)} lignes écrites dans {path}")
        return 0

    pitches = load_pitches()
    if args.limit:
        pitches = pitches[: args.limit]
    planned = len(pitches) * len(args.models) * len(args.prompts) * args.repetitions
    print(f"{planned} appels prévus au maximum.", file=sys.stderr)

    performed = run_matrix(
        args.models, args.prompts, args.repetitions, pitches, resume=not args.no_resume
    )
    print(f"{performed} appels effectués, résultats dans {RAW_RUNS}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
