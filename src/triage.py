"""Le chaînon entre la réception et l'interface : extraire, filtrer, noter, classer.

    from src.triage import process_inbox, load_queue
    process_inbox()          # note ce qui est arrivé dans inbox/ depuis le dernier passage
    queue = load_queue()     # ce que l'interface affiche

Chaque soumission de `inbox/SUB-0001/` reçoit, à côté de son `submission.json`,
un `score.json`. Son `status` dit dans quelle file elle va :

- ``scored``      — notée, entre dans le classement ;
- ``review``      — le filtre anti-injection l'a signalée : notée pour la trace,
                    mais **hors classement**, en revue humaine (§8) ;
- ``unreadable``  — pas assez de texte à noter (PDF scanné, lien vide…) ;
- ``error``       — le modèle n'a pas rendu de sortie exploitable.

Une soumission déjà notée n'est jamais renotée : relancer ne coûte rien.
Supprimer son `score.json` la fait repasser.

**Ce qui fait foi.** Le total est celui recalculé dans le code
(`total_computed`), jamais celui annoncé par le modèle. Le classement et la
sélection adaptative sont ceux de `src/metrics.py`, appliqués aux seules
soumissions ``scored``.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ROOT
from .extract import extract_submission
from .ingest.normalize import Inbox, Submission
from .metrics import rank_pitches, select
from .score_pitch import score_pitch

SCORE_FILE = "score.json"
PROMPT_VERSION = "V2"


def _folder(inbox: Inbox, submission: Submission) -> Path:
    return inbox.root / submission.submission_id


def _event(submission: Submission) -> Dict[str, Any]:
    """L'événement du §4, avec des chemins de pièces jointes absolus.

    L'ingestion enregistre les chemins relatifs à la racine du dépôt : sans
    cette résolution, l'extraction dépendrait du dossier d'où l'on lance.
    """
    event = submission.model_dump()
    for attachment in event["attachments"]:
        path = Path(attachment["path"])
        attachment["path"] = str(path if path.is_absolute() else ROOT / path)
        attachment["name"] = path.name
    return event


def _write(path: Path, payload: Dict[str, Any]) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def score_submission(
    submission: Submission,
    inbox: Optional[Inbox] = None,
    model_key: str = "local",
) -> Dict[str, Any]:
    """Extrait, filtre et note une soumission, puis écrit son `score.json`."""
    inbox = inbox or Inbox()
    extraction = extract_submission(_event(submission))
    payload: Dict[str, Any] = {
        "submission_id": submission.submission_id,
        "channel": submission.channel,
        "received_at": submission.received_at,
        "sender_handle": submission.sender_handle,
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ingestion_warnings": submission.warnings,
        "extraction": extraction.as_dict(),
        "run": None,
    }

    if not extraction.ok:
        payload["status"] = "unreadable"
    else:
        record = score_pitch(
            {"pitch_id": submission.submission_id, "pitch_text": extraction.text},
            model_key,
            PROMPT_VERSION,
        )
        payload["run"] = asdict(record)
        if not record.parsed_output:
            payload["status"] = "error"
        elif record.guard_flagged:
            payload["status"] = "review"
        else:
            payload["status"] = "scored"

    _write(_folder(inbox, submission) / SCORE_FILE, payload)
    return payload


def pending(inbox: Optional[Inbox] = None) -> List[Submission]:
    """Les soumissions reçues qui n'ont pas encore de `score.json`."""
    inbox = inbox or Inbox()
    return [s for s in inbox.submissions() if not (_folder(inbox, s) / SCORE_FILE).exists()]


def process_inbox(
    inbox: Optional[Inbox] = None,
    model_key: str = "local",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Note tout ce qui attend, dans l'ordre d'arrivée."""
    inbox = inbox or Inbox()
    todo = pending(inbox)[:limit] if limit else pending(inbox)
    return [score_submission(s, inbox, model_key) for s in todo]


# --- Ce que l'interface lit ---------------------------------------------------


@dataclass
class Queue:
    ranked: List[Dict[str, Any]] = field(default_factory=list)      # classés, meilleur en tête
    selected: List[str] = field(default_factory=list)               # sélection adaptative (§5)
    review: List[Dict[str, Any]] = field(default_factory=list)      # signalés par le filtre
    unreadable: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    waiting: List[str] = field(default_factory=list)                # reçus, pas encore notés

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_queue(inbox: Optional[Inbox] = None) -> Queue:
    """Toutes les soumissions, rangées dans leur file."""
    inbox = inbox or Inbox()
    queue = Queue()
    scored: Dict[str, Dict[str, Any]] = {}

    for submission in inbox.submissions():
        path = _folder(inbox, submission) / SCORE_FILE
        if not path.exists():
            queue.waiting.append(submission.submission_id)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        status = payload.get("status")
        if status == "scored":
            scored[submission.submission_id] = payload
        elif status == "review":
            queue.review.append(payload)
        elif status == "unreadable":
            queue.unreadable.append(payload)
        else:
            queue.errors.append(payload)

    if scored:
        totals = {sid: p["run"]["total_computed"] for sid, p in scored.items()}
        notes = {sid: p["run"]["parsed_output"]["scores"] for sid, p in scored.items()}
        queue.ranked = [scored[sid] for sid in rank_pitches(totals, notes)]
        queue.selected = select(totals, notes)
    return queue
