"""Données et sélection de l'interface VC, sans dépendance à Streamlit."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pydantic import ValidationError

from .config import DATA, MODELS, RESULTS
from .guard import scan
from .metrics import rank_pitches, select
from .prompts import fingerprint
from .schemas import PitchScore
from .score_pitch import RAW_RUNS
from .v1_assessments import V1_ASSESSMENTS, load_v1_assessments

SUBMISSIONS = RESULTS / "intake_submissions.jsonl"
INTAKE_RUNS = RESULTS / "intake_runs.jsonl"


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


@dataclass(frozen=True)
class Dossier:
    pitch_id: str
    company_name: str
    sector: str
    channel: str
    text: str
    submitted_at: str
    score: Optional[float]
    recommendation: Optional[str]
    scores: Dict[str, int]
    strengths: Sequence[str]
    risks: Sequence[str]
    missing_information: Sequence[str]
    evidence: Sequence[str]
    flagged: bool
    guard_reason: str
    guard_excerpts: Sequence[str]
    error: Optional[str]
    assessment_source: str = ""
    criterion_reasons: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_dossiers(
    corpus_path: Path = DATA / "pitches.jsonl",
    corpus_runs_path: Path = RAW_RUNS,
    submissions_path: Path = SUBMISSIONS,
    intake_runs_path: Path = INTAKE_RUNS,
    assessments_path: Path = V1_ASSESSMENTS,
) -> List[Dossier]:
    """Priorité aux notes directes V1 du texte courant, puis aux appels locaux V2."""
    sources = read_jsonl(corpus_path) + read_jsonl(submissions_path)
    latest: Dict[str, Dict[str, Any]] = {}
    for run in read_jsonl(corpus_runs_path) + read_jsonl(intake_runs_path):
        if (run.get("model") == MODELS["local"].name
                and run.get("prompt_version") == "V2"
                and run.get("prompt_fingerprint") in (None, fingerprint("V2"))):
            latest[run.get("pitch_id", "")] = run

    assessments = load_v1_assessments(sources, assessments_path)
    dossiers: List[Dossier] = []
    for source in sources:
        pid = source.get("pitch_id", "")
        if not pid or not source.get("pitch_text"):
            continue
        run = latest.get(pid, {})
        parsed = None
        if run.get("parsed_output"):
            try:
                candidate = PitchScore.model_validate(run["parsed_output"])
                if candidate.pitch_id == pid and candidate.recommendation in ("reject", "review", "shortlist"):
                    parsed = candidate
            except (ValidationError, ValueError, TypeError):
                pass
        assessment = assessments.get(pid)
        if assessment:
            parsed = PitchScore.model_validate(assessment["parsed_output"])
        verdict = scan(source["pitch_text"])
        flagged = verdict.flagged or bool(run.get("guard_flagged"))
        dossiers.append(Dossier(
            pitch_id=pid,
            company_name=source.get("company_name") or pid,
            sector=source.get("sector") or "—",
            channel=source.get("channel") or "corpus",
            text=source["pitch_text"],
            submitted_at=source.get("submitted_at") or "",
            score=parsed.computed_total() if parsed else None,
            recommendation=parsed.recommendation if parsed else None,
            scores=parsed.scores.model_dump() if parsed else {},
            strengths=parsed.strengths if parsed else [],
            risks=parsed.risks if parsed else [],
            missing_information=parsed.missing_information if parsed else [],
            evidence=parsed.evidence if parsed else [],
            flagged=flagged,
            guard_reason=verdict.reason or ("Signalé par le filtre lors du scoring" if flagged else ""),
            guard_excerpts=[signal.excerpt for signal in verdict.signals],
            error=None if assessment else run.get("error") if run else None,
            assessment_source=assessment["assessor"] + " · " + assessment["assessed_at"] if assessment else (MODELS["local"].name + " · V2" if parsed else ""),
            criterion_reasons=assessment["criterion_reasons"] if assessment else {},
        ))
    return dossiers


def queue(dossiers: Sequence[Dossier], sector: Optional[str] = None, search: str = "") -> Dict[str, List[Dossier]]:
    """Classe tous les dossiers scorés ; les alertes sont informatives et non excluantes."""
    needle = search.casefold().strip()
    visible = [
        dossier for dossier in dossiers
        if (not sector or dossier.sector == sector)
        and (not needle or needle in f"{dossier.pitch_id} {dossier.company_name} {dossier.sector}".casefold())
    ]
    eligible = [d for d in visible if d.score is not None]
    by_id = {d.pitch_id: d for d in eligible}
    totals = {d.pitch_id: d.score for d in eligible}
    notes = {d.pitch_id: d.scores for d in eligible}
    ranking = [by_id[pid] for pid in select(totals, notes)]
    ordered = [by_id[pid] for pid in rank_pitches(totals, notes)]
    review = [d for d in visible if d.flagged]
    pending = [d for d in visible if d.score is None]
    return {"selected": ranking, "ranked": ordered, "review": review, "pending": pending}


def new_submission(pitch_id: str, text: str, company_name: str, sector: str, sources: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "pitch_id": pitch_id,
        "company_name": company_name.strip() or pitch_id,
        "sector": sector.strip() or "—",
        "channel": "manual",
        "pitch_text": text,
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": list(sources),
    }


SHORTLIST = RESULTS / "intake_shortlist.json"


def load_shortlist(path: Path = SHORTLIST) -> List[str]:
    """Local shared workspace shortlist; corrupt content is surfaced to the UI."""
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(item, str) for item in rows):
        raise ValueError("Invalid shortlist format")
    return list(dict.fromkeys(rows))


def save_shortlist(ids: Sequence[str], path: Path = SHORTLIST) -> None:
    """Replace atomically so interrupted writes cannot truncate the shortlist."""
    import os
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(list(dict.fromkeys(ids)), handle, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
