"""Extraction du texte d'une soumission : message, PDF joints, liens (§4 et §6).

Entre l'ingestion et le scoring. Chaque adaptateur (Telegram, email) produit un
événement normalisé ; ce module en tire **un texte** que le moteur peut noter,
et dit précisément ce qui n'a pas pu être lu.

    from src.extract import extract_submission
    result = extract_submission(event)
    if result.ok:
        score_pitch({"pitch_id": ..., "pitch_text": result.text}, "local", "V2")

**Ce qui est lu.** Le texte du message, chaque PDF joint, et chaque lien : un
lien vers un PDF est téléchargé et lu comme une pièce jointe, une page HTML est
réduite à son texte.

**Ce qui ne l'est pas, et le dit.** Un PDF scanné n'a pas de couche texte : il
faudrait de l'OCR, hors du périmètre. DocSend, Notion ou Google Drive servent
souvent une page vide sans navigateur ni connexion : le lien est signalé, pas
deviné. Aucun échec n'est silencieux, chacun porte un code (`ExtractionError`).

**Sécurité.** Les liens viennent d'inconnus. Seuls `http` et `https` sont
acceptés, et toute adresse privée, locale ou de métadonnées cloud est refusée,
redirections comprises : sans ce contrôle, un pitch contenant
`http://localhost:11434/...` ferait interroger le serveur Ollama du fonds par
le fonds lui-même. Le texte extrait reste une donnée non fiable : c'est le
prompt V2 qui le traite comme tel.
"""
from __future__ import annotations

import io
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

# --- Bornes ------------------------------------------------------------------

MAX_PDF_BYTES = 15 * 1024 * 1024   # un deck lourd pèse quelques Mo
MAX_PAGES = 40                     # au-delà, ce n'est plus un pitch
MAX_CHARS = 20_000                 # ~5 000 tokens : tient dans la fenêtre de 8 192 avec le prompt
MIN_WORDS = 40                     # en dessous, rien à noter
MIN_CHARS_PER_PAGE = 25            # en dessous, la page n'a pas de couche texte
LINK_TIMEOUT = 15
USER_AGENT = "VC-Pitch-Intake/1.0 (+extraction de pitch)"


class ExtractionError(Exception):
    """Un échec qualifié. `code` est stable et lisible par l'interface."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class SourceReport:
    kind: str                 # "message" | "pdf" | "link"
    ref: str                  # nom de fichier, URL, ou "message"
    status: str               # "ok" ou un code d'erreur
    chars: int = 0
    detail: str = ""


@dataclass
class Extraction:
    text: str
    sources: List[SourceReport] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def words(self) -> int:
        return len(self.text.split())

    @property
    def ok(self) -> bool:
        """Assez de texte pour que le moteur ait quelque chose à noter."""
        return self.words >= MIN_WORDS

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "words": self.words,
            "text": self.text,
            "sources": [vars(s) for s in self.sources],
            "warnings": self.warnings,
        }


# --- Nettoyage ---------------------------------------------------------------

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SENTENCE_END = re.compile(r"[.!?:;»\"')\]]$")


def normalise(text: str) -> str:
    """Recolle les lignes coupées par la mise en page, sans toucher aux mots.

    Un PDF coupe les phrases à chaque fin de ligne. On recolle une ligne à la
    suivante quand elle ne finit pas une phrase et que la suivante commence en
    minuscule ou par un chiffre ; un mot coupé par un trait d'union en fin de
    ligne est reformé. Les titres et les listes restent sur leur ligne.
    """
    text = _CONTROL.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.strip() for line in text.split("\n")]
    out: List[str] = []
    for line in lines:
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if out and out[-1]:
            prev = out[-1]
            starts_low = line[0].islower() or line[0].isdigit()
            if prev.endswith("-") and line[0].islower():
                out[-1] = prev[:-1] + line
                continue
            if starts_low and not _SENTENCE_END.search(prev):
                out[-1] = prev + " " + line
                continue
        out.append(line)
    return "\n".join(out).strip()


def _cap(text: str, warnings: List[str]) -> str:
    if len(text) <= MAX_CHARS:
        return text
    warnings.append(f"texte tronqué à {MAX_CHARS} caractères sur {len(text)}")
    return text[:MAX_CHARS]


# --- PDF ---------------------------------------------------------------------


def extract_pdf(source: Union[bytes, str, Path]) -> str:
    """Le texte d'un PDF, ou une `ExtractionError` qui dit pourquoi pas."""
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source
    if not data:
        raise ExtractionError("empty", "fichier vide")
    if len(data) > MAX_PDF_BYTES:
        raise ExtractionError("too_large", f"PDF de {len(data) // 1024 // 1024} Mo, plafond {MAX_PDF_BYTES // 1024 // 1024} Mo")
    if not data.lstrip()[:5].startswith(b"%PDF"):
        raise ExtractionError("not_pdf", "le fichier n'est pas un PDF")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            # Beaucoup de PDF sont « chiffrés » sans mot de passe d'ouverture.
            try:
                if not reader.decrypt(""):
                    raise ExtractionError("encrypted_pdf", "PDF protégé par un mot de passe")
            except ExtractionError:
                raise
            except Exception as exc:
                raise ExtractionError("encrypted_pdf", f"PDF chiffré illisible : {exc}") from exc
        pages = reader.pages
        if len(pages) > MAX_PAGES:
            raise ExtractionError("too_large", f"{len(pages)} pages, plafond {MAX_PAGES}")
        texts = [page.extract_text() or "" for page in pages]
    except ExtractionError:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise ExtractionError("corrupt_pdf", f"PDF illisible : {exc}") from exc

    if not pages:
        raise ExtractionError("empty", "PDF sans page")
    if sum(len(t.strip()) for t in texts) < MIN_CHARS_PER_PAGE * len(pages):
        raise ExtractionError(
            "no_text_layer",
            "aucune couche texte : PDF scanné ou composé d'images, l'OCR n'est pas pris en charge",
        )
    return normalise("\n\n".join(texts))


# --- Liens -------------------------------------------------------------------

# Services qui servent une coquille vide sans navigateur ni connexion.
_UNSUPPORTED_HOSTS = ("docsend.com", "notion.so", "notion.site", "drive.google.com", "docs.google.com", "pitch.com")


def _check_host(url: str) -> None:
    """Refuse tout ce qui n'est pas une adresse publique en http(s)."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ExtractionError("blocked_link", f"schéma refusé : {parts.scheme or 'aucun'}")
    host = parts.hostname
    if not host:
        raise ExtractionError("blocked_link", "URL sans hôte")
    try:
        infos = socket.getaddrinfo(host, parts.port or (443 if parts.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ExtractionError("dead_link", f"hôte introuvable : {host}") from exc
    for info in infos:
        address = ipaddress.ip_address(info[4][0].split("%")[0])
        if (address.is_private or address.is_loopback or address.is_link_local
                or address.is_reserved or address.is_multicast or address.is_unspecified):
            raise ExtractionError("blocked_link", f"adresse non publique refusée : {host}")


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    """Chaque redirection repasse par le contrôle d'hôte."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_host(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url: str) -> tuple:
    """(octets, type de contenu). Séparé pour pouvoir être remplacé en test."""
    _check_host(url)
    opener = urllib.request.build_opener(_CheckedRedirects)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=LINK_TIMEOUT) as response:
            body = response.read(MAX_PDF_BYTES + 1)
            ctype = response.headers.get_content_type()
    except urllib.error.HTTPError as exc:
        raise ExtractionError("dead_link", f"HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise ExtractionError("dead_link", f"lien injoignable : {getattr(exc, 'reason', exc)}") from exc
    if len(body) > MAX_PDF_BYTES:
        raise ExtractionError("too_large", "contenu au-delà du plafond de téléchargement")
    return body, ctype


class _TextOnly(HTMLParser):
    _SKIP = {"script", "style", "noscript", "svg", "head", "template"}
    _BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self._skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skipping += 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skipping:
            self._skipping -= 1
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skipping:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextOnly()
    parser.feed(html)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return normalise(re.sub(r"\n\s*\n+", "\n\n", text))


def extract_link(url: str) -> str:
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    body, ctype = _fetch(url)
    if ctype == "application/pdf" or body.lstrip()[:5].startswith(b"%PDF"):
        return extract_pdf(body)
    if ctype in ("text/html", "application/xhtml+xml"):
        text = html_to_text(body.decode("utf-8", "replace"))
    elif ctype.startswith("text/"):
        text = normalise(body.decode("utf-8", "replace"))
    else:
        raise ExtractionError("unsupported_link", f"type de contenu non pris en charge : {ctype}")
    if len(text.split()) < MIN_WORDS and any(host == h or host.endswith("." + h) for h in _UNSUPPORTED_HOSTS):
        raise ExtractionError(
            "unsupported_link",
            f"{host} n'expose pas son contenu sans navigateur : demander le PDF au fondateur",
        )
    return text


# --- Soumission --------------------------------------------------------------


def _attachment_bytes(attachment: Dict[str, Any]) -> bytes:
    if attachment.get("content") is not None:
        return attachment["content"]
    return Path(attachment["path"]).read_bytes()


def extract_submission(event: Dict[str, Any]) -> Extraction:
    """Tout le texte d'un événement normalisé (§4), avec un compte rendu par source.

    L'ordre suit l'événement : le message, puis les pièces jointes, puis les
    liens. Chaque source lisible est précédée d'un séparateur qui dit d'où elle
    vient, pour que la justification d'une note reste traçable.
    """
    blocks: List[str] = []
    sources: List[SourceReport] = []
    warnings: List[str] = []

    message = normalise(event.get("text") or "")
    if message:
        blocks.append(message)
        sources.append(SourceReport("message", "message", "ok", len(message)))

    for attachment in event.get("attachments") or []:
        name = attachment.get("name") or Path(attachment.get("path", "pièce jointe")).name
        if attachment.get("type") != "pdf":
            sources.append(SourceReport("attachment", name, "unsupported", 0, f"type {attachment.get('type')}"))
            continue
        try:
            text = extract_pdf(_attachment_bytes(attachment))
        except (ExtractionError, OSError) as exc:
            code = getattr(exc, "code", "unreadable")
            sources.append(SourceReport("pdf", name, code, 0, getattr(exc, "message", str(exc))))
            continue
        blocks.append(f"[pièce jointe : {name}]\n{text}")
        sources.append(SourceReport("pdf", name, "ok", len(text)))

    for url in _unique(event.get("links") or []):
        try:
            text = extract_link(url)
        except ExtractionError as exc:
            sources.append(SourceReport("link", url, exc.code, 0, exc.message))
            continue
        blocks.append(f"[lien : {url}]\n{text}")
        sources.append(SourceReport("link", url, "ok", len(text)))

    text = _cap("\n\n".join(blocks), warnings)
    if len(text.split()) < MIN_WORDS:
        failed = [s for s in sources if s.status != "ok"]
        warnings.append(
            "trop peu de texte pour noter ce pitch"
            + (f" — {len(failed)} source(s) illisible(s)" if failed else "")
        )
    return Extraction(text=text, sources=sources, warnings=warnings)


def _unique(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def find_links(text: str) -> List[str]:
    """Les URL d'un message, pour les adaptateurs qui ne les isolent pas."""
    return _unique(m.rstrip(".,;:!?)»\"'") for m in re.findall(r"https?://[^\s<>\"']+", text or ""))
