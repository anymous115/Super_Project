"""Adaptateur e-mail : un message reçu sur l'adresse du fonds devient un `Draft` (§4).

Le module s'appelle `mail` et non `email` : il utilise le module standard
`email`, qu'un fichier du même nom masquerait.

**Réception par IMAP.** Une boîte dédiée est relevée à intervalle régulier par
`Input_Telegram_Mail/input_listener.py`. Aucun service d'« inbound parsing »
payant, aucune URL publique : la bibliothèque standard suffit. Un message n'est
marqué lu qu'une fois enregistré ; un plantage en cours de route le laisse dans
la file.

**Accusé par SMTP, sans boucle.** Un répondeur automatique qui répond à un
autre répondeur automatique s'emballe. On ne répond donc jamais à un message
automatique, et notre accusé se déclare lui-même automatique (RFC 3834).
"""
from __future__ import annotations

import hashlib
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parseaddr, parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any, Callable, List, Optional, Tuple

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


# --- Accusé de réception par SMTP ----------------------------------------------------


def smtp_reply(settings: Any) -> Reply:
    """Un `Reply` qui envoie l'accusé par SMTP, dans le fil du message d'origine.

    `settings` porte `address`, `password`, `smtp_host` et `smtp_port`.
    """
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

