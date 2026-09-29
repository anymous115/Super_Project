"""Adaptateur Telegram : une update de la Bot API devient un `Draft` (§4).

Le fondateur écrit au bot du fonds, en privé. Il peut envoyer du texte, un PDF
(avec ou sans légende) ou un lien, et reçoit aussitôt un accusé de réception.

**Long polling plutôt que webhook.** Un webhook exige une URL HTTPS publique ;
le long polling (`getUpdates`) marche depuis un portable, ce qui suffit pour la
démonstration. L'objet `update` est identique dans les deux modes : un webhook
n'aurait qu'à appeler `handle_update()` avec le corps de la requête.

La boucle de relève est dans `Input_Telegram_Mail/input_listener.py`. Le jeton
du bot n'apparaît jamais dans un message d'erreur : il fait partie de l'URL de
chaque appel.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import require_env
from .normalize import (
    EMPTY_REPLY,
    INSTRUCTIONS,
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

API = "https://api.telegram.org"
POLL_TIMEOUT = 30    # secondes : Telegram garde la requête ouverte jusqu'à un message

WELCOME = "Hello! This bot collects startup pitches for the fund. " + INSTRUCTIONS


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    """Les trois appels dont l'adaptateur a besoin, et rien d'autre."""

    def __init__(self, token: Optional[str] = None, http: Any = None):
        import httpx

        self._token = token or require_env("TELEGRAM_BOT_TOKEN")
        self._http = http or httpx.Client(timeout=POLL_TIMEOUT + 10)

    def _call(self, method: str, **params: Any) -> Any:
        try:
            response = self._http.post(f"{API}/bot{self._token}/{method}", json=params)
            payload = response.json()
        except Exception as exc:
            # Le message d'origine contient l'URL, donc le jeton : on ne le relaie pas.
            raise TelegramError(f"{method} : {type(exc).__name__}") from None
        if not payload.get("ok"):
            raise TelegramError(f"{method} : {payload.get('description', 'erreur inconnue')}")
        return payload["result"]

    def get_updates(self, offset: Optional[int]) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"timeout": POLL_TIMEOUT, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return self._call("getUpdates", **params)

    def download(self, file_id: str) -> bytes:
        file_path = self._call("getFile", file_id=file_id)["file_path"]
        try:
            response = self._http.get(f"{API}/file/bot{self._token}/{file_path}")
            response.raise_for_status()
        except Exception as exc:
            raise TelegramError(f"téléchargement : {type(exc).__name__}") from None
        return response.content

    def send_message(self, chat_id: int, text: str) -> None:
        self._call("sendMessage", chat_id=chat_id, text=text)


# --- Traduction d'une update -------------------------------------------------


def sender_handle(user: Dict[str, Any]) -> str:
    """`@pseudo` si l'utilisateur en a un, sinon son identifiant numérique."""
    if user.get("username"):
        return "@" + user["username"]
    return f"tg:{user.get('id', 'unknown')}"


def _hidden_links(message: Dict[str, Any]) -> List[str]:
    """Les liens posés sous un mot (« voir notre deck »), absents du texte brut."""
    entities = (message.get("entities") or []) + (message.get("caption_entities") or [])
    return [e["url"] for e in entities if e.get("type") == "text_link" and e.get("url")]


def parse_update(update: Dict[str, Any], client: Any) -> Optional[Draft]:
    """Traduit une update en `Draft`. `None` si elle n'est pas un pitch potentiel.

    Sont écartés : tout ce qui n'est pas un nouveau message, les groupes et
    canaux (le bot ne note que ce qu'on lui envoie en privé) et les commandes.
    """
    message = update.get("message")
    if not message or message.get("chat", {}).get("type") != "private":
        return None

    text = message.get("text") or message.get("caption") or ""
    if text.startswith("/"):
        return None

    attachments, warnings = [], []
    document = message.get("document")
    if document:
        if looks_like_pdf(document.get("file_name"), document.get("mime_type")):
            file_id = document["file_id"]
            attachments.append(PendingAttachment(
                filename=document.get("file_name") or "deck.pdf",
                fetch=lambda: client.download(file_id),
                size_hint=document.get("file_size"),
            ))
        else:
            warnings.append("Only PDF attachments are read; the file you sent was ignored.")

    received = datetime.fromtimestamp(message.get("date", 0), tz=timezone.utc) if message.get("date") else None
    chat_id = message["chat"]["id"]
    return Draft(
        channel="telegram",
        received_at=iso_utc(received),
        sender_handle=sender_handle(message.get("from", {})),
        text=text,
        links=merge_links(extract_links(text), _hidden_links(message)),
        source_ref=f"telegram:{chat_id}:{message['message_id']}",
        attachments=attachments,
        warnings=warnings,
    )


def handle_update(update: Dict[str, Any], client: Any, inbox: Inbox) -> Optional[Submission]:
    """Traite une update de bout en bout : enregistrement puis accusé de réception."""
    message = update.get("message") or {}
    chat_id = message.get("chat", {}).get("id")

    draft = parse_update(update, client)
    if draft is None:
        # Une commande en privé (/start, /help) reçoit les instructions.
        if message.get("chat", {}).get("type") == "private" and (message.get("text") or "").startswith("/"):
            client.send_message(chat_id, WELCOME)
        return None

    if inbox.seen(draft.source_ref):
        return None
    if draft.is_empty():
        # Un sticker, une photo seule, une pièce jointe non PDF sans texte.
        client.send_message(chat_id, " ".join([EMPTY_REPLY] + draft.warnings))
        return None

    submission = inbox.add(draft)
    try:
        client.send_message(chat_id, acknowledgement(submission))
    except TelegramError as exc:
        # Le pitch est enregistré : un accusé perdu ne l'annule pas.
        print(f"Telegram : accusé de {submission.submission_id} non envoyé ({exc}).")
    return submission

