"""L'ingestion Telegram et e-mail (§4, cas d'erreur du §11).

Aucun test ne touche le réseau : le client Telegram est remplacé par un faux
qui renvoie des octets, et les e-mails sont construits en mémoire. Ce qu'on
vérifie, ce sont les règles — un nom de fichier hostile, un faux PDF, un
message déjà reçu, un répondeur automatique — pas la Bot API elle-même.
"""
from email.message import EmailMessage

import pytest

from src.ingest import mail, telegram
from src.ingest.normalize import (
    Draft,
    Inbox,
    PendingAttachment,
    Submission,
    extract_links,
    safe_filename,
)

PDF = b"%PDF-1.4\n% faux deck de test\n%%EOF\n"


@pytest.fixture
def inbox(tmp_path):
    return Inbox(tmp_path / "inbox")


# --- Utilitaires communs -----------------------------------------------------


def test_liens_extraits_dans_l_ordre_sans_ponctuation_ni_doublon():
    texte = "Deck: https://docsend.com/view/abc. Notion (https://notion.so/x), again https://docsend.com/view/abc!"
    assert extract_links(texte) == ["https://docsend.com/view/abc", "https://notion.so/x"]


@pytest.mark.parametrize("recu, attendu", [
    ("../../etc/deck.pdf", "deck.pdf"),
    ("..\\..\\Windows\\deck.pdf", "deck.pdf"),
    ("Mon Deck (final).PDF", "Mon_Deck_final_.PDF"),
    ("deck", "deck.pdf"),
    ("", "attachment.pdf"),
    ("...", "attachment.pdf"),
])
def test_un_nom_de_fichier_recu_ne_sort_jamais_du_dossier(recu, attendu):
    assert safe_filename(recu) == attendu


def test_numeros_sequentiels_et_relecture(inbox):
    for i in range(3):
        inbox.add(Draft("email", "2026-09-24T10:00:00Z", "a@b.c", f"pitch {i}", [], f"ref-{i}"))
    ids = [s.submission_id for s in inbox.submissions()]
    assert ids == ["SUB-0001", "SUB-0002", "SUB-0003"]
    assert inbox.seen("ref-1") and not inbox.seen("ref-9")


def test_un_dossier_interrompu_n_est_ni_lu_ni_reutilise(inbox):
    inbox.root.mkdir(parents=True)
    (inbox.root / "SUB-0001").mkdir()          # ingestion plantée avant l'écriture
    s = inbox.add(Draft("email", "2026-09-24T10:00:00Z", "a@b.c", "pitch", [], "ref"))
    assert s.submission_id == "SUB-0002"
    assert [x.submission_id for x in inbox.submissions()] == ["SUB-0002"]


def test_un_faux_pdf_est_ecarte_avec_un_avertissement(inbox):
    faux = PendingAttachment("deck.pdf", fetch=lambda: b"MZ\x90\x00 executable")
    s = inbox.add(Draft("email", "2026-09-24T10:00:00Z", "a@b.c", "pitch", [], "ref", [faux]))
    assert s.attachments == []
    assert "not a readable PDF" in s.warnings[0]


def test_un_pdf_trop_lourd_n_est_pas_telecharge(inbox):
    def interdit():
        raise AssertionError("le fichier n'aurait pas dû être téléchargé")
    lourd = PendingAttachment("deck.pdf", fetch=interdit, size_hint=50 * 1024 * 1024)
    s = inbox.add(Draft("email", "2026-09-24T10:00:00Z", "a@b.c", "pitch", [], "ref", [lourd]))
    assert s.attachments == [] and "20 MB" in s.warnings[0]


def test_deux_pieces_jointes_de_meme_nom_ne_s_ecrasent_pas(inbox):
    deux = [PendingAttachment("deck.pdf", lambda: PDF), PendingAttachment("deck.pdf", lambda: PDF + b"v2")]
    s = inbox.add(Draft("email", "2026-09-24T10:00:00Z", "a@b.c", "", [], "ref", deux))
    noms = [a.path.replace("\\", "/").split("/")[-1] for a in s.attachments]
    assert noms == ["deck.pdf", "deck_2.pdf"]


# --- Telegram ----------------------------------------------------------------


class FakeTelegram:
    def __init__(self, files=None):
        self.files = files or {}
        self.sent = []

    def download(self, file_id):
        return self.files[file_id]

    def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


def update(message_id=1, chat_type="private", **message):
    base = {
        "message_id": message_id,
        "date": 1790000000,
        "chat": {"id": 42, "type": chat_type},
        "from": {"id": 42, "username": "founder"},
    }
    base.update(message)
    return {"update_id": 1000 + message_id, "message": base}


def test_telegram_texte_et_liens(inbox):
    bot = FakeTelegram()
    msg = update(
        text="Hi, we are Acme. Deck here and https://acme.io",
        entities=[{"type": "text_link", "offset": 17, "length": 9, "url": "https://docsend.com/v/acme"}],
    )
    s = telegram.handle_update(msg, bot, inbox)

    assert s.channel == "telegram" and s.sender_handle == "@founder"
    assert s.received_at == "2026-09-21T14:13:20Z"
    assert s.links == ["https://acme.io", "https://docsend.com/v/acme"]
    assert s.source_ref == "telegram:42:1"
    assert bot.sent == [(42, telegram.acknowledgement(s))]
    assert "SUB-0001" in bot.sent[0][1] and "Acme" not in bot.sent[0][1]


def test_telegram_pdf_avec_legende(inbox):
    bot = FakeTelegram(files={"F1": PDF})
    msg = update(caption="Our deck", document={
        "file_id": "F1", "file_name": "acme-deck.pdf", "mime_type": "application/pdf", "file_size": len(PDF),
    })
    s = telegram.handle_update(msg, bot, inbox)

    assert s.text == "Our deck"
    assert len(s.attachments) == 1 and s.attachments[0].type == "pdf"
    assert (inbox.root / "SUB-0001" / "acme-deck.pdf").read_bytes() == PDF


def test_telegram_meme_message_recu_deux_fois(inbox):
    bot = FakeTelegram()
    assert telegram.handle_update(update(text="pitch"), bot, inbox) is not None
    assert telegram.handle_update(update(text="pitch"), bot, inbox) is None
    assert len(inbox.submissions()) == 1 and len(bot.sent) == 1


def test_telegram_ignore_les_groupes(inbox):
    bot = FakeTelegram()
    assert telegram.handle_update(update(text="pitch", chat_type="group"), bot, inbox) is None
    assert inbox.submissions() == [] and bot.sent == []


def test_telegram_commande_start_renvoie_les_instructions(inbox):
    bot = FakeTelegram()
    assert telegram.handle_update(update(text="/start"), bot, inbox) is None
    assert inbox.submissions() == [] and bot.sent == [(42, telegram.WELCOME)]


def test_telegram_fichier_non_pdf_seul(inbox):
    bot = FakeTelegram()
    msg = update(document={"file_id": "F2", "file_name": "deck.pptx",
                           "mime_type": "application/vnd.ms-powerpoint"})
    assert telegram.handle_update(msg, bot, inbox) is None
    assert inbox.submissions() == []
    assert "could not find a pitch" in bot.sent[0][1] and "Only PDF" in bot.sent[0][1]


def test_telegram_sans_pseudo():
    assert telegram.sender_handle({"id": 7}) == "tg:7"


# --- E-mail ------------------------------------------------------------------


def email(body="We are Acme.\nDeck: https://docsend.com/v/acme", subject="Acme — pre-seed",
          pdf=None, html=None, **headers):
    m = EmailMessage()
    m["From"] = "Jane Founder <Jane@Acme.io>"
    m["To"] = "pitchs@fonds.example"
    m["Subject"] = subject
    m["Date"] = "Wed, 24 Sep 2026 16:03:11 +0200"
    m["Message-ID"] = headers.pop("message_id", "<abc@acme.io>")
    for name, value in headers.items():
        m[name.replace("_", "-")] = value
    if html is not None:
        m.set_content(html, subtype="html")
    else:
        m.set_content(body)
    if pdf is not None:
        m.add_attachment(pdf, maintype="application", subtype="pdf", filename="acme-deck.pdf")
    return m.as_bytes()


class Replies:
    def __init__(self):
        self.sent = []

    def __call__(self, to, subject, body, original):
        self.sent.append((to, subject, body))


def test_email_texte_piece_jointe_et_accuse(inbox):
    replies = Replies()
    s = mail.handle_email(email(pdf=PDF), inbox, replies, own_address="pitchs@fonds.example")

    assert s.channel == "email" and s.sender_handle == "jane@acme.io"
    assert s.received_at == "2026-09-24T14:03:11Z"
    assert s.text.startswith("Acme — pre-seed\n\nWe are Acme.")
    assert s.links == ["https://docsend.com/v/acme"]
    assert s.source_ref == "email:<abc@acme.io>"
    assert (inbox.root / "SUB-0001" / "acme-deck.pdf").read_bytes() == PDF
    assert replies.sent == [("jane@acme.io", "Re: Acme — pre-seed", mail.acknowledgement(s))]


def test_email_html_seul(inbox):
    html = ("<html><head><style>p{color:red}</style></head><body>"
            "<p>We are <b>Acme</b>.</p><p>See <a href='https://notion.so/acme'>our deck</a></p>"
            "</body></html>")
    s = mail.handle_email(email(html=html), inbox)
    assert "We are Acme." in s.text and "color" not in s.text
    assert s.links == ["https://notion.so/acme"]


def test_email_deja_recu(inbox):
    replies = Replies()
    mail.handle_email(email(), inbox, replies)
    assert mail.handle_email(email(), inbox, replies) is None
    assert len(inbox.submissions()) == 1 and len(replies.sent) == 1


@pytest.mark.parametrize("headers", [
    {"Auto_Submitted": "auto-replied"},
    {"Precedence": "bulk"},
    {"List_Id": "<news.example>"},
])
def test_email_automatique_enregistre_sans_accuse(inbox, headers):
    replies = Replies()
    assert mail.handle_email(email(**headers), inbox, replies) is not None
    assert replies.sent == []


def test_email_jamais_d_accuse_a_soi_meme(inbox):
    replies = Replies()
    mail.handle_email(email(), inbox, replies, own_address="JANE@acme.io")
    assert replies.sent == []


def test_email_vide(inbox):
    replies = Replies()
    assert mail.handle_email(email(body="", subject=""), inbox, replies) is None
    assert inbox.submissions() == []
    assert "could not find a pitch" in replies.sent[0][2]


def test_email_sans_message_id_a_une_empreinte_stable():
    brut = email(message_id="")
    assert mail.parse_email(brut)[0].source_ref == mail.parse_email(brut)[0].source_ref
    assert mail.parse_email(brut)[0].source_ref.startswith("email:sha256:")


# --- Le contrat commun -------------------------------------------------------


def test_les_deux_canaux_produisent_le_meme_objet(inbox):
    """C'est la promesse du §4 : rien en aval ne sait d'où vient le pitch."""
    t = telegram.handle_update(update(text="pitch"), FakeTelegram(), inbox)
    e = mail.handle_email(email(), inbox)
    assert set(t.model_dump()) == set(e.model_dump())
    for s in (t, e):
        Submission.model_validate_json(s.model_dump_json())
