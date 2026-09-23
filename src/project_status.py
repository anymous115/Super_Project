"""Mesure l'avancement du projet à partir des livrables présents dans le dépôt.

Le tableau de bord importe ce module à chaque chargement. Il n'y a donc aucun
statut à maintenir à la main : ajouter des annotations, des résultats ou un
livrable fait évoluer automatiquement les compteurs et les phases.
"""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class TaskProgress:
    label: str
    progress: float
    evidence: str
    next_action: str
    priority: int = 2

    @property
    def state(self) -> str:
        if self.progress >= 1:
            return "Terminé"
        if self.progress > 0:
            return "En cours"
        return "À faire"


@dataclass(frozen=True)
class PhaseProgress:
    number: int
    name: str
    tasks: Sequence[TaskProgress]

    @property
    def progress(self) -> float:
        return sum(task.progress for task in self.tasks) / len(self.tasks) if self.tasks else 0.0

    @property
    def state(self) -> str:
        if self.progress >= 1:
            return "Terminée"
        if self.progress > 0:
            return "En cours"
        return "À faire"


@dataclass(frozen=True)
class ProjectSnapshot:
    generated_at: str
    branch: str
    commit: str
    phases: Sequence[PhaseProgress]
    metrics: Dict[str, Any]
    recent_commits: Sequence[Dict[str, str]]

    @property
    def progress(self) -> float:
        tasks = [task for phase in self.phases for task in phase.tasks]
        return sum(task.progress for task in tasks) / len(tasks) if tasks else 0.0

    @property
    def current_phase(self) -> Optional[PhaseProgress]:
        return next((phase for phase in self.phases if phase.progress < 1), None)

    @property
    def next_actions(self) -> List[Dict[str, Any]]:
        actions = [
            {
                "phase": phase.number,
                "phase_name": phase.name,
                "task": task.label,
                "action": task.next_action,
                "progress": task.progress,
                "priority": task.priority,
            }
            for phase in self.phases
            for task in phase.tasks
            if task.progress < 1
        ]
        return sorted(actions, key=lambda row: (row["priority"], row["phase"], row["progress"]))

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["progress"] = self.progress
        payload["current_phase"] = self.current_phase.number if self.current_phase else None
        payload["next_actions"] = self.next_actions
        return payload


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ratio(value: int, target: int) -> float:
    return _clamp(value / target) if target else 0.0


def _jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _count_existing(root: Path, paths: Iterable[str]) -> int:
    return sum((root / path).exists() for path in paths)


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=3
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return ""


def _recent_commits(root: Path, limit: int = 8) -> List[Dict[str, str]]:
    output = _git(root, "log", f"-{limit}", "--date=short", "--pretty=%h%x1f%ad%x1f%an%x1f%s")
    commits = []
    for line in output.splitlines():
        parts = line.split("\x1f", 3)
        if len(parts) == 4:
            commits.append(dict(zip(("hash", "date", "author", "subject"), parts)))
    return commits


def collect_project_status(root: Optional[Path] = None) -> ProjectSnapshot:
    root = (root or Path(__file__).resolve().parent.parent).resolve()
    pitches = _jsonl(root / "data/pitches.jsonl")
    drafted = sum(bool(row.get("pitch_text", "").strip()) for row in pitches)
    validated = sum(row.get("review_status") == "validated" for row in pitches)
    derived = [row for row in pitches if row.get("source_type") == "derived"]
    sourced = sum(bool(row.get("source_url")) for row in derived)
    pdfs = len(list((root / "data/pdfs").glob("P*.pdf"))) if (root / "data/pdfs").exists() else 0

    annotations: List[Dict[str, Any]] = []
    for annotator in "ABCD":
        annotations.extend(_jsonl(root / f"data/annotations/{annotator}.jsonl"))
    reconciliations = _jsonl(root / "data/annotations/reconciliation.jsonl")
    references = _jsonl(root / "data/reference_scores.jsonl")

    modules = (
        "src/config.py",
        "src/schemas.py",
        "src/prompts.py",
        "src/score_pitch.py",
        "src/benchmark.py",
        "src/metrics.py",
    )
    module_count = _count_existing(root, modules)
    test_count = len(list((root / "tests").glob("test_*.py"))) if (root / "tests").exists() else 0
    prompt_text = (root / "src/prompts.py").read_text(encoding="utf-8") if (root / "src/prompts.py").exists() else ""
    prompt_versions = sum(version in prompt_text for version in ("V0", "V1", "V2"))

    runs = _jsonl(root / "results/raw_runs.jsonl")
    valid_runs = sum(bool(row.get("valid_json")) for row in runs)
    configurations = {
        (row.get("model"), row.get("prompt_version"))
        for row in runs
        if row.get("model") and row.get("prompt_version")
    }
    summaries = _csv_rows(root / "results/benchmark_summary.csv")

    ingestion_files = (
        "src/ingest/normalize.py",
        "src/ingest/telegram.py",
        "src/ingest/email.py",
        "src/extract.py",
    )
    ingestion_count = _count_existing(root, ingestion_files)
    product_app = (root / "app.py").exists()

    notebook = root / "08_quality_vs_cost_benchmark.ipynb"
    notebook_ready = False
    if notebook.exists():
        notebook_text = notebook.read_text(encoding="utf-8")
        notebook_ready = "benchmark_task.jsonl" not in notebook_text and "src.benchmark" in notebook_text

    presentation_count = len(list(root.glob("*.pptx"))) + len(list((root / "docs").glob("*.pptx")))
    final_report = any(
        (root / path).exists()
        for path in ("docs/FINAL_REPORT.md", "docs/RECOMMENDATION.md", "results/FINAL_REPORT.md")
    )
    tags = set(_git(root, "tag", "--list").splitlines())

    phases = (
        PhaseProgress(1, "Cadrage", (
            TaskProgress("Vision et protocole", float((root / "docs/PROTOCOL.md").exists()), "Protocole versionné", "Finaliser docs/PROTOCOL.md", 1),
            TaskProgress("Grille et sélection", float((root / "data/calibration.jsonl").exists()), "Calibration machine-lisible", "Générer data/calibration.jsonl", 1),
            TaskProgress("Modèles et machine figés", float((root / "src/config.py").exists() and "gpt-6-astra" in (root / "src/config.py").read_text(encoding="utf-8")), "Configuration du benchmark", "Figer les deux modèles et la machine", 1),
        )),
        PhaseProgress(2, "Données", (
            TaskProgress("Corpus rédigé", _ratio(drafted, 50), f"{drafted}/50 pitchs", "Rédiger les pitchs manquants", 1),
            TaskProgress("Validation humaine", _ratio(validated, 50), f"{validated}/50 validés", "Relire et valider les pitchs drafted", 1),
            TaskProgress("Provenance documentée", _ratio(sourced, max(37, len(derived))), f"{sourced}/{max(37, len(derived))} sources dérivées", "Compléter les URL de provenance", 1),
            TaskProgress("PDF générés", _ratio(pdfs, 50), f"{pdfs}/50 PDF", "Générer les PDF manquants", 2),
            TaskProgress("Double annotation", _ratio(len(annotations), 100), f"{len(annotations)}/100 annotations", "Lancer scripts/annotate.py pour A, B, C et D", 1),
            TaskProgress("Référence réconciliée", _ratio(len(references), 50), f"{len(references)}/50 références · {len(reconciliations)} arbitrages", "Réconcilier puis lancer scripts/build_reference.py", 1),
        )),
        PhaseProgress(3, "Pipeline", (
            TaskProgress("Modules du pipeline", _ratio(module_count, len(modules)), f"{module_count}/{len(modules)} modules", "Implémenter les modules manquants", 2),
            TaskProgress("Prompts V0 / V1 / V2", _ratio(prompt_versions, 3), f"{prompt_versions}/3 versions", "Compléter les versions de prompt", 2),
            TaskProgress("Tests automatisés écrits", _ratio(test_count, 7), f"{test_count} fichiers de tests", "Ajouter les tests essentiels manquants", 2),
            TaskProgress("Premier appel enregistré", float(bool(runs)), f"{len(runs)} appel(s) enregistré(s)", "Faire un smoke test local sur 3 pitchs", 1),
        )),
        PhaseProgress(4, "Expériences", (
            TaskProgress("Matrice benchmark", _ratio(len(runs), 900), f"{len(runs)}/900 appels · {valid_runs} JSON valides", "Lancer ou reprendre la matrice", 2),
            TaskProgress("Six configurations couvertes", _ratio(len(configurations), 6), f"{len(configurations)}/6 modèle × prompt", "Couvrir les configurations manquantes", 2),
            TaskProgress("Synthèse des métriques", _ratio(len(summaries), 6), f"{len(summaries)}/6 lignes de synthèse", "Générer benchmark_summary.csv", 2),
            TaskProgress("Recommandation finale", float(final_report), "Rapport final détecté" if final_report else "Aucun rapport final", "Rédiger la recommandation local/frontier/hybride", 3),
        )),
        PhaseProgress(5, "Produit", (
            TaskProgress("Ingestion et extraction", _ratio(ingestion_count, len(ingestion_files)), f"{ingestion_count}/{len(ingestion_files)} composants", "Construire Telegram, email et extraction PDF", 3),
            TaskProgress("Interface VC Streamlit", float(product_app), "app.py présent" if product_app else "app.py absent", "Construire l'interface produit dans app.py", 3),
        )),
        PhaseProgress(6, "Livraison", (
            TaskProgress("Notebook final", float(notebook_ready), "Notebook relié au pipeline" if notebook_ready else "Notebook starter encore détecté", "Réécrire le notebook avec le pipeline réel", 3),
            TaskProgress("Présentation", float(presentation_count > 0), f"{presentation_count} présentation(s)", "Créer la présentation finale", 4),
            TaskProgress("Release v1.0", float("v1.0" in tags), "Tag v1.0 présent" if "v1.0" in tags else "Tag v1.0 absent", "Tester la démo puis créer le tag v1.0", 4),
        )),
    )

    branch = _git(root, "branch", "--show-current") or "hors dépôt Git"
    commit = _git(root, "rev-parse", "--short", "HEAD") or "—"
    metrics = {
        "pitches": len(pitches),
        "drafted_pitches": drafted,
        "validated_pitches": validated,
        "pdfs": pdfs,
        "annotations": len(annotations),
        "references": len(references),
        "benchmark_runs": len(runs),
        "valid_runs": valid_runs,
        "summary_rows": len(summaries),
        "tests": test_count,
    }
    return ProjectSnapshot(
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        branch=branch,
        commit=commit,
        phases=phases,
        metrics=metrics,
        recent_commits=_recent_commits(root),
    )
