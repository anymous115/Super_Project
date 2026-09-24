"""Adaptateur e-mail : un message reçu sur l'adresse du fonds devient un `Draft` (§4).

Le module s'appelle `mail` et non `email` : il utilise le module standard
`email`, qu'un fichier du même nom masquerait.

**Réception par IMAP.** Une boîte dédiée est relevée à intervalle régulier.
Aucun service d'« inbound parsing » payant, aucune URL publique : la
bibliothèque standard suffit. Un message n'est marqué lu qu'une fois
enregistré ; un plantage en cours de route le laisse dans la file.

**Accusé par SMTP, sans boucle.** Un répondeur automatique qui répond à un
autre répondeur automatique s'emballe. On ne répond donc jamais à un message
automatique, et notre accusé se déclare lui-même automatique (RFC 3834).

Identifiants lus dans `.env` : `EMAIL_ADDRESS`, `EMAIL_PASSWORD`,
`EMAIL_IMAP_HOST`, `EMAIL_SMTP_HOST`, et les ports en option.
"""
from __future__ import annotations

import hashlib
import os
import time
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser
from typing import Callable, List, Optional, Tuple

from ..config import load_env, require_env
from .normalize import (
    EMPTY_REPLY,
    Draft,
    Inbox,
    PendingAttachment,
    Submission,
    acknowledgement,
    extract_links,
    iso_utc,
    looks_like_pdf,
    merge_links,
)

POLL_INTERVAL = 60   # secondes entre deux relevés de la boîte

# Reply = Callable[[destinataire, sujet, corps, message d'origine], None]
Reply = Callable[[str, str, str, EmailMessage], None]


# --- HTML → texte ------------------------------------------------------------


class _HTMLText(HTMLParser):
    """Texte visible et liens d'un corps HTML. Suffisant pour un e-mail de pitch."""

    BLOCKS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
    HIDDEN = {"script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.links: List[str] = []
        self._hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self._hidden += 1
        if tag in self.BLOCKS:
            self.parts.append("\n")
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if href.lower().startswith(("http://", "https://")):
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag in self.HIDDEN and self._hidden:
            self._hidden -= 1
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._hidden:
            self.parts.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        out: List[str] = []
        for line in lines:
            if line or (out and out[-1]):
                out.append(line)
        return "\n".join(out).strip()


def html_to_text(html: str) -> Tuple[str, List[str]]:
    parser = _HTMLText()
    parser.feed(html)
    parser.close()
    return parser.text(), parser.links


# --- Traduction d'un message -------------------------------------------------


def _body(message: EmailMessage) -> Tuple[str, List[str]]:
    """Le corps en texte, et les liens cachés dans le HTML s'il n'y a que lui."""
    part = message.get_body(preferencelist=("plain", "html"))
    if part is None:
        return "", []
    content = part.get_content()
    if part.get_content_type() == "text/html":
        return html_to_text(content)
    return content, []


def _received_at(message: EmailMessage) -> str:
    try:
        return iso_utc(parsedate_to_datetime(message["Date"]))
    except (TypeError, ValueError):
        return iso_utc()


def source_ref(message: EmailMessage, raw: bytes) -> str:
    """Le Message-ID, ou à défaut une empreinte du message brut."""
    message_id = (message.get("Message-ID") or "").strip()
    if message_id:
        return f"email:{message_id}"
    return "email:sha256:" + hashlib.sha256(raw).hexdigest()[:16]


def parse_email(raw: bytes) -> Tuple[Draft, EmailMessage]:
    """Traduit un e-mail brut (RFC 5322) en `Draft`."""
    message = message_from_bytes(raw, policy=policy.default)

    subject = (message.get("Subject") or "").strip()
    body, html_links = _body(message)
    text = f"{subject}\n\n{body.strip()}".strip() if subject else body.strip()

    attachments, warnings = [], []
    for part in message.iter_attachments():
        filename = part.get_filename()
        if looks_like_pdf(filename, part.get_content_type()):
            attachments.append(PendingAttachment(
                filename=filename or "deck.pdf",
                fetch=lambda p=part: p.get_payload(decode=True) or b"",
            ))
        else:
            warnings.append(f"Only PDF attachments are read; {filename or 'one file'} was ignored.")

    draft = Draft(
        channel="email",
        received_at=_received_at(message),
        sender_handle=parseaddr(message.get("From", ""))[1].lower() or "unknown",
        text=text,
        links=merge_links(extract_links(body), html_links),
        source_ref=source_ref(message, raw),
        attachments=attachments,
        warnings=warnings,
    )
    return draft, message


def is_automatic(message: EmailMessage, own_address: str = "") -> bool:
    """Vrai si le message ne doit pas recevoir d'accusé (RFC 3834).

    Répondre à un répondeur automatique, à une liste de diffusion ou à un
    rapport de non-remise, c'est risquer une boucle sans fin.
    """
    if (message.get("Auto-Submitted") or "no").strip().lower() != "no":
        return True
    if (message.get("Precedence") or "").strip().lower() in {"bulk", "list", "junk"}:
        return True
    if message.get("List-Id") or message.get("X-Autoreply") or message.get("X-Autorespond"):
        return True
    sender = parseaddr(message.get("From", ""))[1].lower()
    local = sender.split("@")[0]
    if not sender or local in {"mailer-daemon", "postmaster", "noreply", "no-reply"}:
        return True
    return bool(own_address) and sender == own_address.lower()


def handle_email(raw: bytes, inbox: Inbox, reply: Optional[Reply] = None,
                 own_address: str = "") -> Optional[Submission]:
    """Traite un e-mail de bout en bout : enregistrement puis accusé de réception."""
    draft, message = parse_email(raw)
    if inbox.seen(draft.source_ref):
        return None

    answer = None if is_automatic(message, own_address) else reply
    subject = (message.get("Subject") or "your pitch").strip()
    if not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    if draft.is_empty():
        if answer:
            answer(draft.sender_handle, subject, " ".join([EMPTY_REPLY] + draft.warnings), message)
        return None

    submission = inbox.add(draft)
    if answer:
        try:
            answer(draft.sender_handle, subject, acknowledgement(submission), message)
        except Exception as exc:
            # Le pitch est enregistré : un accusé perdu ne l'annule pas.
            print(f"E-mail : accusé de {submission.submission_id} non envoyé ({type(exc).__name__}).")
    return submission


# --- Connexion à la boîte ----------------------------------------------------


class MailSettings:
    def __init__(self) -> None:
        load_env()
        self.address = require_env("EMAIL_ADDRESS")
        self.password = require_env("EMAIL_PASSWORD")
        self.imap_host = require_env("EMAIL_IMAP_HOST")
        self.imap_port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
        self.smtp_host = require_env("EMAIL_SMTP_HOST")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "465"))


def smtp_reply(settings: MailSettings) -> Reply:
    """Un `Reply` qui envoie l'accusé par SMTP, dans le fil du message d'origine."""
    import smtplib

    def send(to: str, subject: str, body: str, original: EmailMessage) -> None:
        ack = EmailMessage()
        ack["From"] = settings.address
        ack["To"] = to
        ack["Subject"] = subject
        ack["Auto-Submitted"] = "auto-replied"
        if original.get("Message-ID"):
            ack["In-Reply-To"] = original["Message-ID"]
            ack["References"] = original["Message-ID"]
        ack.set_content(body)

        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.starttls()
        with server:
            server.login(settings.address, settings.password)
            server.send_message(ack)

    return send


def poll_once(settings: MailSettings, inbox: Inbox, reply: Optional[Reply]) -> List[Submission]:
    """Relève les messages non lus, les ingère, et les marque lus un par un."""
    import imaplib

    received: List[Submission] = []
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
        imap.login(settings.address, settings.password)
        imap.select("INBOX")
        status, data = imap.uid("search", None, "UNSEEN")
        if status != "OK":
            return received
        for uid in data[0].split():
            # PEEK : le message reste non lu tant qu'il n'est pas enregistré.
            status, fetched = imap.uid("fetch", uid, "(BODY.PEEK[])")
            if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                continue
            try:
                submission = handle_email(fetched[0][1], inbox, reply, settings.address)
            except Exception as exc:
                # Un message illisible ne doit pas bloquer la file ; il reste non lu.
                print(f"E-mail : message {uid.decode()} ignoré ({type(exc).__name__}: {exc}).")
                continue
            imap.uid("store", uid, "+FLAGS", "(\\Seen)")
            if submission:
                received.append(submission)
    return received


def run(inbox: Optional[Inbox] = None, once: bool = False, interval: int = POLL_INTERVAL) -> None:
    """Relève la boîte toutes les `interval` secondes. `once` : un seul relevé."""
    settings = MailSettings()
    inbox = inbox or Inbox()
    reply = smtp_reply(settings)
    print(f"E-mail : relève {settings.address} toutes les {interval} s. Ctrl+C pour arrêter.")
    while True:
        try:
            for submission in poll_once(settings, inbox, reply):
                print(f"E-mail : {submission.submission_id} reçu de {submission.sender_handle}.")
        except Exception as exc:
            print(f"E-mail : relevé impossible ({type(exc).__name__}: {exc}).")
        if once:
            return
        time.sleep(interval)
