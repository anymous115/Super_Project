"""Mesure l'avancement du projet à partir des livrables présents dans le dépôt.

Le tableau de bord importe ce module à chaque chargement. Il n'y a donc aucun
statut à maintenir à la main : ajouter des annotations, des résultats ou un
livrable fait évoluer automatiquement les compteurs et les phases.
"""
from __future__ import annotations

import csv
import difflib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.extract import ExtractionError, extract_pdf
from src.guard import scan
from src.v1_assessments import load_v1_assessments


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

    traps = {row["pitch_id"] for row in pitches if row.get("is_injection_test")}
    guard_verdicts = {
        row["pitch_id"]: scan(row.get("pitch_text", ""))
        for row in pitches if row.get("pitch_id")
    }
    guard_caught = sum(guard_verdicts[pid].flagged for pid in traps if pid in guard_verdicts)
    guard_false_positives = sum(
        verdict.flagged for pid, verdict in guard_verdicts.items() if pid not in traps
    )

    pdf_checked = pdf_fidelity_passed = 0
    for row in pitches:
        pdf = root / "data/pdfs" / f"{row.get('pitch_id', '')}.pdf"
        if not pdf.is_file():
            continue
        pdf_checked += 1
        try:
            source_words = re.findall(r"[a-z0-9]+", row.get("pitch_text", "").lower())
            extracted_words = re.findall(r"[a-z0-9]+", extract_pdf(pdf).lower())
            fidelity = difflib.SequenceMatcher(
                None, source_words, extracted_words, autojunk=False
            ).ratio()
            pdf_fidelity_passed += fidelity >= 0.98
        except (ExtractionError, OSError):
            pass

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
    # Le produit tourne sur un seul modèle, avec le prompt V2 (§10 du protocole).
    engine = [row for row in runs if row.get("prompt_version") == "V2" and row.get("parsed_output")]
    scored = {row.get("pitch_id") for row in engine}
    # Contenu : écarté par le filtre, ou noté sans finir en shortlist.
    contained = {
        row.get("pitch_id")
        for row in engine
        if row.get("pitch_id") in traps
        and (row.get("guard_flagged") or row["parsed_output"].get("recommendation") != "shortlist")
    }
    v1_mode = (root / "docs/UNICORNEXT_V1.md").exists()
    try:
        v1_assessments = load_v1_assessments(pitches, root / "data/assessments/unicornext_v1.jsonl")
    except (OSError, ValueError, KeyError, TypeError):
        v1_assessments = {}
    if v1_mode:
        scored.update(v1_assessments)
        contained.update(pid for pid in v1_assessments if pid in traps and guard_verdicts[pid].flagged)
    checks_written = (root / "docs/ENGINE_CHECKS.md").exists()

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
        notebook_ready = (
            "benchmark_task.jsonl" not in notebook_text
            and "src.benchmark" in notebook_text
            and "TODO" not in notebook_text
        )

    presentation_count = len(list(root.glob("*.pptx"))) + len(list((root / "docs").glob("*.pptx")))
    tags = set(_git(root, "tag", "--list").splitlines())

    phases = (
        PhaseProgress(1, "Cadrage", (
            TaskProgress("Vision et protocole", float((root / "docs/PROTOCOL.md").exists()), "Protocole versionné", "Finaliser docs/PROTOCOL.md", 1),
            TaskProgress("Grille et sélection", float((root / "data/calibration.jsonl").exists()), "Calibration machine-lisible", "Générer data/calibration.jsonl", 1),
            TaskProgress("Modèles et machine figés", float((root / "src/config.py").exists() and "qwen2.5:14b" in (root / "src/config.py").read_text(encoding="utf-8")), "Configuration du moteur", "Figer le modèle et la machine", 1),
        )),
        PhaseProgress(2, "Données", (
            TaskProgress("Corpus rédigé", _ratio(drafted, 50), f"{drafted}/50 pitchs", "Rédiger les pitchs manquants", 1),
            TaskProgress("Évaluations IA V1", _ratio(len(v1_assessments), 50), f"{len(v1_assessments)}/50 évaluations directes", "Compléter les évaluations IA du corpus", 1) if v1_mode else TaskProgress("Validation humaine", _ratio(validated, 50), f"{validated}/50 validés", "Relire et valider les pitchs drafted", 1),
            TaskProgress("Provenance documentée", _ratio(sourced, max(37, len(derived))), f"{sourced}/{max(37, len(derived))} sources dérivées", "Compléter les URL de provenance", 1),
            TaskProgress("PDF générés", _ratio(pdfs, 50), f"{pdfs}/50 PDF", "Générer les PDF manquants", 2),
            TaskProgress("Données gelées", float("data-v1" in tags), "Tag data-v1 présent" if "data-v1" in tags else "Tag data-v1 absent", "Taguer le corpus et ses évaluations V1" if v1_mode else "Taguer data-v1 une fois les pitchs validés", 2),
        )),
        PhaseProgress(3, "Pipeline", (
            TaskProgress("Modules du pipeline", _ratio(module_count, len(modules)), f"{module_count}/{len(modules)} modules", "Implémenter les modules manquants", 2),
            TaskProgress("Prompts V0 / V1 / V2", _ratio(prompt_versions, 3), f"{prompt_versions}/3 versions", "Compléter les versions de prompt", 2),
            TaskProgress("Filtre anti-injection vérifié", _ratio(guard_caught, max(len(traps), 1)) if guard_false_positives == 0 else 0.0, f"{guard_caught}/{len(traps)} pièges détectés, {guard_false_positives} faux positif(s)", "Vérifier src/guard.py sur le corpus", 1),
            TaskProgress("Tests automatisés écrits", _ratio(test_count, 7), f"{test_count} fichiers de tests", "Ajouter les tests essentiels manquants", 2),
            TaskProgress("Notes V1 disponibles", float(bool(v1_assessments)), "Évaluations directes, hors benchmark", "Générer les notes V1", 1) if v1_mode else TaskProgress("Premier appel enregistré", float(bool(runs)), f"{len(runs)} appel(s) enregistré(s)", "Faire un smoke test local sur 3 pitchs", 1),
        )),
        PhaseProgress(4, "Moteur", (
            TaskProgress("Corpus noté pour la V1" if v1_mode else "Corpus scoré en V2", _ratio(len(scored), 50), f"{len(scored)}/50 pitchs scorés", "Compléter les évaluations directes V1" if v1_mode else "python3 -m src.benchmark --models local --prompts V2", 1),
            TaskProgress("Injections contenues", _ratio(len(contained), max(len(traps), 1)), f"{len(contained)}/{len(traps)} pitchs piégés contenus", "Scorer les pitchs piégés en V2 et vérifier la sélection", 2),
            TaskProgress("Contrôles consignés", float(checks_written), "docs/ENGINE_CHECKS.md présent" if checks_written else "Aucun compte rendu", "Consigner les contrôles du §11 dans docs/ENGINE_CHECKS.md", 2),
        )),
        PhaseProgress(5, "Produit", (
            TaskProgress("Ingestion et extraction", _ratio(ingestion_count, len(ingestion_files)), f"{ingestion_count}/{len(ingestion_files)} composants", "Construire Telegram, email et extraction PDF", 3),
            TaskProgress("Fidélité de l'extraction PDF", _ratio(pdf_fidelity_passed, 50), f"{pdf_fidelity_passed}/{pdf_checked} PDF fidèles (seuil 98 %)", "Corriger les PDF dont l'extraction perd ou inverse des mots", 2),
            TaskProgress("Frontend Unicornext V1", float(product_app), "Application investisseur : app.py présent" if product_app else "app.py absent", "Construire l'interface produit dans app.py", 3),
        )),
        PhaseProgress(6, "Livraison", (
            TaskProgress("Notebook final", float(notebook_ready), "Notebook relié au pipeline" if notebook_ready else "Notebook structuré, cellules TODO restantes", "Compléter puis exécuter les cellules TODO du notebook", 3),
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
        "v1_mode": v1_mode,
        "direct_assessments": len(v1_assessments),
        "pdfs": pdfs,
        "engine_runs": len(runs),
        "valid_runs": valid_runs,
        "scored_pitches": len(scored),
        "traps_contained": len(contained),
        "guard_caught": guard_caught,
        "guard_traps": len(traps),
        "guard_false_positives": guard_false_positives,
        "pdf_checked": pdf_checked,
        "pdf_fidelity_passed": pdf_fidelity_passed,
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
