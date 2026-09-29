"""Donner suite : les liens sont sûrs même quand les coordonnées viennent d'un inconnu."""
import pytest

from src.followup import find_email, find_phone, follow_up, mailto


def test_repondre_a_un_email_ouvre_un_mailto_prerempli():
    fu = follow_up("email", "jane@acme.io", "We sell payroll software.", "SUB-0007", "fr")
    assert fu.reply_channel == "email"
    assert fu.reply_href.startswith("mailto:jane@acme.io?subject=Votre%20pitch%20SUB-0007&body=")
    assert "%0A" in fu.reply_href                     # les retours à la ligne du message sont encodés
    assert fu.any


def test_le_message_prerempli_suit_la_langue():
    assert "Your%20pitch" in follow_up("email", "jane@acme.io", "", "SUB-1", "en").reply_href


def test_repondre_a_telegram_ouvre_le_chat_du_pseudo():
    fu = follow_up("telegram", "@jane_doe", "A pitch.", "SUB-0008")
    assert fu.reply_channel == "telegram" and fu.reply_href == "https://t.me/jane_doe"


@pytest.mark.parametrize("handle", ["tg:123456", "@ab", "jane_doe", "@jane doe", "@jane/../x", "", "unknown"])
def test_telegram_sans_pseudo_utilisable_ne_donne_aucun_lien(handle):
    fu = follow_up("telegram", handle, "A pitch.", "SUB-0009")
    assert fu.reply_href is None and fu.reply_channel == "" and not fu.any


@pytest.mark.parametrize("hostile", [
    "jane@acme.io?bcc=boss@x.com",          # destinataire en copie
    "jane@acme.io&cc=boss@x.com",
    "jane@acme.io,boss@x.com",              # deuxième destinataire
    "jane@acme.io\nBcc: boss@x.com",        # injection d'en-tête
    "jane@acme.io\r\nSubject: piégé",
    "jane@acme.io ",
    "javascript:alert(1)",
    "<jane@acme.io>",
    "jane@localhost",                       # pas de domaine
])
def test_adresse_douteuse_ne_devient_jamais_un_lien(hostile):
    assert mailto(hostile, "SUB-1") is None
    assert follow_up("email", hostile, "", "SUB-1").reply_href is None


def test_adresse_ecrite_dans_le_pitch_est_proposee_quand_le_canal_n_est_pas_l_email():
    fu = follow_up("telegram", "@jane_doe", "Write to founders@acme.io for the data room.", "SUB-1")
    assert fu.email == "founders@acme.io" and fu.email_href.startswith("mailto:founders@acme.io?")
    assert fu.reply_channel == "telegram"


def test_adresse_deja_couverte_par_repondre_n_est_pas_proposee_deux_fois():
    fu = follow_up("email", "jane@acme.io", "Contact me at Jane@Acme.io", "SUB-1")
    assert fu.reply_href and fu.email is None and fu.email_href is None


@pytest.mark.parametrize("text, attendu", [
    ("Call +33 6 12 34 56 78 anytime", "+33612345678"),
    ("Tel: +1 (415) 555-0132.", "+14155550132"),
    ("Appelez le 06 12 34 56 78", "+33612345678"),
    ("Mobile 06.12.34.56.78 ou 06-12-34-56-78", "+33612345678"),
])
def test_numeros_reconnus_sont_normalises(text, attendu):
    assert find_phone(text) == attendu


@pytest.mark.parametrize("text", [
    "Founded 2026-09-24, raised 1 400 000 EUR",     # date et chiffre d'affaires
    "ARR of 1400000 and 20260924",
    "Version 3.14.159.26.53",
    "Ref +12345",                                   # trop court
    "+1234567890123456789",                         # trop long
    "",
])
def test_ce_qui_ressemble_a_un_nombre_n_est_pas_un_telephone(text):
    assert find_phone(text) is None


def test_numero_du_pitch_devient_un_lien_d_appel():
    fu = follow_up("email", "jane@acme.io", "Call me on +33 6 12 34 56 78", "SUB-1")
    assert fu.phone == "+33612345678" and fu.phone_href == "tel:+33612345678"


def test_dossier_sans_contact_ne_propose_rien():
    fu = follow_up("", "", "A fictional pitch with no contact.", "P001")
    assert not fu.any and fu.reply_href is None and fu.email is None and fu.phone is None


def test_find_email_normalise_la_casse():
    assert find_email("Me: Jane.Doe+vc@Acme.IO.") == "jane.doe+vc@acme.io"
