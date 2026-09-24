"""L'événement normalisé commun à tous les canaux (§4 du protocole).

Chaque adaptateur traduit un message brut — une update Telegram, un e-mail —
en un `Draft`, puis `Inbox.add()` en fait une `Submission` enregistrée sur
disque. Rien en aval ne sait d'où vient le pitch : ajouter un canal revient à
écrire un adaptateur qui produit un `Draft`.

Le contenu reçu vient d'inconnus. Trois règles en découlent :

1. **Un nom de fichier n'est jamais fait confiance.** Il est réduit à un nom
   simple, sans chemin, avant d'être écrit.
2. **Un PDF se reconnaît à son contenu, pas à son nom.** Un fichier qui ne
   commence pas par `%PDF-` est écarté, avec un avertissement.
3. **Rien de ce qui arrive n'est committé.** `inbox/` est dans `.gitignore` :
   une soumission réelle contient au minimum un identifiant personnel.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..config import ROOT

INBOX = ROOT / "inbox"

MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024   # limite de téléchargement de la Bot API Telegram
PDF_MAGIC = b"%PDF-"


# --- L'objet normalisé -------------------------------------------------------


class Attachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["pdf"]
    path: str          # relatif à la racine du dépôt


class Submission(BaseModel):
    """Un pitch reçu, quel que soit le canal. C'est l'objet du §4."""

    model_config = ConfigDict(extra="forbid")

    submission_id: str = Field(pattern=r"^SUB-\d{4,}$")
    channel: Literal["telegram", "email"]
    received_at: str
    sender_handle: str
    text: str
    attachments: List[Attachment]
    links: List[str]
    # Identifiant du message côté canal : un redémarrage ne réingère rien.
    source_ref: str
    # Ce qui s'est mal passé à l'ingestion (PDF illisible, trop lourd…).
    warnings: List[str] = []


# --- Ce qu'un adaptateur produit ---------------------------------------------


@dataclass
class PendingAttachment:
    """Une pièce jointe annoncée, pas encore téléchargée.

    Le téléchargement est différé jusqu'à ce que la soumission ait un numéro :
    un message déjà ingéré ne coûte ainsi aucun appel réseau.
    """

    filename: str
    fetch: Callable[[], bytes]
    size_hint: Optional[int] = None


@dataclass
class Draft:
    channel: str
    received_at: str
    sender_handle: str
    text: str
    links: List[str]
    source_ref: str
    attachments: List[PendingAttachment] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.text.strip() or self.links or self.attachments)


# --- Utilitaires communs aux adaptateurs -------------------------------------

_URL = re.compile(r"https?://[^\s<>\"'()\[\]{}]+", re.I)


def extract_links(*texts: str) -> List[str]:
    """Les URL présentes dans les textes, dans l'ordre, sans doublon."""
    seen: List[str] = []
    for text in texts:
        for match in _URL.findall(text or ""):
            url = match.rstrip(".,;:!?")
            if url not in seen:
                seen.append(url)
    return seen


def merge_links(*groups: List[str]) -> List[str]:
    merged: List[str] = []
    for group in groups:
        for url in group:
            if url not in merged:
                merged.append(url)
    return merged


def safe_filename(name: Optional[str], default: str = "attachment.pdf") -> str:
    """Réduit un nom de fichier reçu à un nom sûr, sans chemin.

    `../../etc/deck.pdf` devient `deck.pdf` ; un nom vide ou réduit à des
    caractères exotiques devient `default`.
    """
    base = re.split(r"[\\/]", name or "")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")[:80]
    if not base:
        return default
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base


def looks_like_pdf(filename: Optional[str], mime: Optional[str]) -> bool:
    """Tri préalable, sur ce que l'expéditeur annonce. Le contenu tranche ensuite."""
    return (mime or "").lower() == "application/pdf" or (filename or "").lower().endswith(".pdf")


def iso_utc(moment: Optional[datetime] = None) -> str:
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Accusés de réception ----------------------------------------------------
# Les pitchs sont rédigés en anglais (§6) : l'accusé l'est aussi.

INSTRUCTIONS = (
    "Send us your pitch here: write it directly, attach your deck as a PDF, "
    "or share a link (Notion, DocSend, Drive…)."
)

EMPTY_REPLY = "We could not find a pitch in your message. " + INSTRUCTIONS


def acknowledgement(submission: Submission) -> str:
    """Accusé de réception. Il ne répète jamais le contenu reçu."""
    lines = [
        f"Thanks, your pitch has been received (reference {submission.submission_id}).",
        "Every submission is read against the same evaluation grid.",
    ]
    if submission.warnings:
        lines.append("Note: " + " ".join(submission.warnings))
    return "\n".join(lines)


# --- Stockage ----------------------------------------------------------------


class Inbox:
    """Les soumissions reçues, un dossier par soumission.

    `inbox/SUB-0001/submission.json` et ses PDF à côté. Le numéro est réservé
    par la création du dossier, qui est atomique : deux adaptateurs lancés en
    parallèle — Telegram et e-mail — ne peuvent pas obtenir le même.
    """

    FILE = "submission.json"

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else INBOX

    # Lecture

    def submissions(self) -> List[Submission]:
        """Toutes les soumissions complètes, par numéro croissant."""
        if not self.root.exists():
            return []
        found = []
        for path in sorted(self.root.glob(f"SUB-*/{self.FILE}")):
            found.append(Submission.model_validate_json(path.read_text(encoding="utf-8")))
        return found

    def seen(self, source_ref: str) -> bool:
        return any(s.source_ref == source_ref for s in self.submissions())

    # Écriture

    def _reserve(self) -> tuple[str, Path]:
        self.root.mkdir(parents=True, exist_ok=True)
        taken = [int(p.name[4:]) for p in self.root.glob("SUB-*") if p.name[4:].isdigit()]
        number = max(taken, default=0) + 1
        while True:
            submission_id = f"SUB-{number:04d}"
            folder = self.root / submission_id
            try:
                folder.mkdir()
                return submission_id, folder
            except FileExistsError:
                number += 1

    def _store_attachment(self, pending: PendingAttachment, folder: Path, used: set) -> tuple:
        """Télécharge et écrit une pièce jointe. Renvoie (Attachment | None, avertissement | None)."""
        name = safe_filename(pending.filename)
        if pending.size_hint and pending.size_hint > MAX_ATTACHMENT_BYTES:
            return None, f"{name} is larger than 20 MB and was not read."
        try:
            content = pending.fetch()
        except Exception as exc:
            return None, f"{name} could not be downloaded ({type(exc).__name__})."
        if len(content) > MAX_ATTACHMENT_BYTES:
            return None, f"{name} is larger than 20 MB and was not read."
        if not content.startswith(PDF_MAGIC):
            return None, f"{name} is not a readable PDF."

        stem, suffix = name[:-4], name[-4:]
        counter = 1
        while name.lower() in used:
            counter += 1
            name = f"{stem}_{counter}{suffix}"
        used.add(name.lower())

        target = folder / name
        target.write_bytes(content)
        return Attachment(type="pdf", path=target.relative_to(ROOT).as_posix()
                          if target.is_relative_to(ROOT) else str(target)), None

    def add(self, draft: Draft) -> Submission:
        """Numérote, télécharge les pièces jointes et enregistre la soumission."""
        submission_id, folder = self._reserve()

        attachments, warnings, used = [], list(draft.warnings), set()
        for pending in draft.attachments:
            stored, warning = self._store_attachment(pending, folder, used)
            if stored:
                attachments.append(stored)
            if warning:
                warnings.append(warning)

        submission = Submission(
            submission_id=submission_id,
            channel=draft.channel,
            received_at=draft.received_at,
            sender_handle=draft.sender_handle,
            text=draft.text.strip(),
            attachments=attachments,
            links=draft.links,
            source_ref=draft.source_ref,
            warnings=warnings,
        )
        # Écriture atomique : un dossier sans submission.json est une
        # ingestion interrompue, ignorée par `submissions()`.
        temporary = folder / (self.FILE + ".tmp")
        temporary.write_text(submission.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, folder / self.FILE)
        return submission
