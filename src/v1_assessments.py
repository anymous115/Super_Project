"""Versioned direct AI assessments, separate from benchmark/API measurements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from .config import DATA, CRITERIA
from .schemas import PitchScore, RECOMMENDATIONS

V1_ASSESSMENTS = DATA / 'assessments' / 'unicornext_v1.jsonl'


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_v1_assessments(sources: Sequence[dict], path: Path = V1_ASSESSMENTS) -> dict[str, dict[str, Any]]:
    """Only expose assessments of the exact current pitch, never an old revision.

    Corrupt artifacts raise an error. Missing files/revised pitches remain unscored.
    No calibration or human approval status is consulted.
    """
    if not path.exists():
        return {}
    source_by_id = {s['pitch_id']: s for s in sources if s.get('pitch_id')}
    result = {}
    seen = set()
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        pid = row['pitch_id']
        if pid in seen:
            raise ValueError(f'Duplicate V1 assessment: {pid}')
        seen.add(pid)
        score = PitchScore.model_validate(row['parsed_output'])
        if score.pitch_id != pid or score.recommendation not in RECOMMENDATIONS:
            raise ValueError(f'Invalid V1 assessment: {pid}')
        if score.total_drift() > 0.0001 or set(row['criterion_reasons']) != set(CRITERIA):
            raise ValueError(f'Invalid V1 score or reasons: {pid}')
        source = source_by_id.get(pid)
        if not source or text_hash(source.get('pitch_text', '')) != row['source_sha256']:
            continue
        if any(quote not in source['pitch_text'] for quote in score.evidence):
            raise ValueError(f'Unsupported V1 evidence: {pid}')
        result[pid] = row
    return result
