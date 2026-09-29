"""Donner suite à un dossier qui plaît : répondre, écrire, appeler.

L'application n'envoie rien. Elle prépare un lien (`mailto:`, `https://t.me/…`, `tel:`) que le VC
ouvre dans son propre client, avec un message prérempli pour l'e-mail. Rien ne part sans son geste,
et aucun identifiant du fonds n'est nécessaire.

Les coordonnées viennent d'inconnus : l'adresse d'un expéditeur, un numéro écrit dans un pitch. Chacune
est validée en entier avant de devenir un lien. Une adresse qui contiendrait `?`, `&`, une virgule ou
un retour à la ligne ne donne aucun lien, de sorte qu'un expéditeur ne peut ni ajouter de destinataire
en copie ni injecter d'en-tête dans le message.

Sources de coordonnées :
- le canal d'origine : l'adresse d'un e-mail, le `@pseudo` d'un message Telegram ;
- le texte du pitch : une adresse ou un numéro que le fondateur y a écrit.
Un fondateur Telegram sans pseudo public (`tg:<id>`) ne peut pas être joint depuis un lien : le canal
d'origine n'offre alors rien.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

_ADDRESS = r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
EMAIL = re.compile(_ADDRESS)
TG_USER = re.compile(r"@[A-Za-z0-9_]{5,32}")

# Deux formes de numéro, volontairement étroites : une date (2026-09-24), un chiffre d'affaires
# (1 400 000) ou un identifiant ne doivent jamais devenir un lien d'appel.
_PHONE_INTL = re.compile(r"(?<![\w+])\+\d(?:[ .()-]{0,2}\d){7,14}(?!\d)")  # +33 6 12 34 56 78, +1 (415) 555-0132
_PHONE_FR = re.compile(r"(?<![\w+])0[1-9](?:[ .-]?\d{2}){4}(?!\d)")      # 06 12 34 56 78

MESSAGES = {
    "fr": ("Votre pitch {ref}",
           "Bonjour,\n\nMerci pour votre pitch (réf. {ref}). Il a retenu notre attention et nous aimerions "
           "en discuter avec vous.\n\nQuand seriez-vous disponible pour un échange ?\n\nCordialement"),
    "en": ("Your pitch {ref}",
           "Hello,\n\nThank you for your pitch (ref. {ref}). It caught our attention and we would like to "
           "discuss it with you.\n\nWhen would you be available for a call?\n\nBest regards"),
}


@dataclass(frozen=True)
class FollowUp:
    """Ce qu'on peut faire pour donner suite. Un champ vide veut dire : rien de fiable à proposer."""
    reply_channel: str = ""            # "email" ou "telegram" : le canal par lequel le fondateur a écrit
    reply_href: Optional[str] = None
    email: Optional[str] = None        # une adresse trouvée dans le pitch, si le canal d'origine n'est pas l'e-mail
    email_href: Optional[str] = None
    phone: Optional[str] = None        # au format international
    phone_href: Optional[str] = None

    @property
    def any(self) -> bool:
        return bool(self.reply_href or self.email_href or self.phone_href)


def find_phone(text: str) -> Optional[str]:
    """Le premier numéro du texte, au format international (+33…), ou None."""
    match = _PHONE_INTL.search(text or "")
    if match:
        digits = re.sub(r"\D", "", match.group())
        return "+" + digits if 8 <= len(digits) <= 15 else None
    match = _PHONE_FR.search(text or "")
    if match:
        return "+33" + re.sub(r"\D", "", match.group())[1:]
    return None


def find_email(text: str) -> Optional[str]:
    match = EMAIL.search(text or "")
    return match.group().lower() if match else None


def mailto(address: str, ref: str, language: str = "fr") -> Optional[str]:
    """Un lien `mailto:` avec sujet et message préremplis, ou None si l'adresse n'est pas sûre."""
    if not EMAIL.fullmatch(address or ""):
        return None
    subject, body = MESSAGES.get(language, MESSAGES["fr"])
    return f"mailto:{address}?subject={quote(subject.format(ref=ref), safe='')}&body={quote(body.format(ref=ref), safe='')}"


def follow_up(channel: str, handle: str, text: str, ref: str, language: str = "fr") -> FollowUp:
    """Les actions possibles pour un dossier : canal d'origine, puis coordonnées écrites dans le pitch."""
    reply_channel, reply_href = "", None
    if channel == "email":
        reply_href = mailto((handle or "").lower(), ref, language)
        reply_channel = "email" if reply_href else ""
    elif channel == "telegram" and TG_USER.fullmatch(handle or ""):
        reply_channel, reply_href = "telegram", f"https://t.me/{handle[1:]}"

    email = find_email(text)
    if email and reply_channel == "email" and email == (handle or "").lower():
        email = None                                    # déjà couvert par « Répondre »
    phone = find_phone(text)
    return FollowUp(
        reply_channel=reply_channel, reply_href=reply_href,
        email=email, email_href=mailto(email, ref, language) if email else None,
        phone=phone, phone_href=f"tel:{phone}" if phone else None,
    )
