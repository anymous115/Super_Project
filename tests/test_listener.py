"""L'écouteur retenu (Input_Telegram_Mail/) dépose bien les pitchs dans inbox/.

Sans réseau : les messages sont construits en mémoire et passés aux deux
fonctions de traitement de l'écouteur, comme le feraient ses boucles.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from src.ingest.normalize import Inbox
from src.triage import pending
from tests.test_ingest import PDF, FakeTelegram, Replies, email, update

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("input_listener", ROOT / "Input_Telegram_Mail" / "input_listener.py")
listener = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(listener)


@pytest.fixture
def inbox(tmp_path):
    return Inbox(tmp_path / "inbox")


@pytest.fixture
def config(tmp_path):
    return {"fichier_sortie": str(tmp_path / "messages.jsonl"), "mail": {"adresse": "pitchs@fonds.example"}}


def journal(config):
    return [json.loads(l) for l in Path(config["fichier_sortie"]).read_text().splitlines()]


def test_telegram_avec_deck_arrive_dans_inbox(inbox, config):
    bot = FakeTelegram(files={"F1": PDF})
    msg = update(caption="Our deck", document={
        "file_id": "F1", "file_name": "acme-deck.pdf", "mime_type": "application/pdf", "file_size": len(PDF),
    })
    s = listener.traiter_update(config, msg, bot, inbox)

    assert s.submission_id == "SUB-0001" and len(s.attachments) == 1
    assert (inbox.root / "SUB-0001" / "acme-deck.pdf").read_bytes() == PDF
    assert [p.submission_id for p in pending(inbox)] == ["SUB-0001"]      # la notation le verra
    assert journal(config)[0]["source"] == "telegram"
    assert "acme-deck.pdf" in journal(config)[0]["texte"]


def test_telegram_meme_message_deux_fois(inbox, config):
    bot = FakeTelegram()
    msg = update(text="We are Acme, pre-seed, https://acme.io")
    assert listener.traiter_update(config, msg, bot, inbox) is not None
    assert listener.traiter_update(config, msg, bot, inbox) is None
    assert len(inbox.submissions()) == 1


def test_mail_avec_deck_et_accuse(inbox, config):
    replies = Replies()
    s = listener.traiter_mail(config, email(pdf=PDF), inbox, replies)

    assert s.channel == "email" and s.sender_handle == "jane@acme.io"
    assert (inbox.root / "SUB-0001" / "acme-deck.pdf").read_bytes() == PDF
    assert len(replies.sent) == 1
    assert journal(config)[0]["source"] == "mail"


def test_config_exemple_sans_secret():
    exemple = json.loads((ROOT / "Input_Telegram_Mail" / "config.example.json").read_text())
    texte = json.dumps(exemple).lower()
    assert "token" not in texte and "mot_de_passe" not in texte and "adresse" not in texte
