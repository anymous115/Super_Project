"""Extraction : ce qui est lu, ce qui est refusé, et pourquoi (§4, §6, §11).

Aucun appel réseau : le téléchargement est remplacé en test. Les contrôles
d'adresse, eux, sont testés pour de vrai, parce que c'est la barrière qui
empêche un pitch de faire interroger le réseau interne du fonds.
"""
import io
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("pypdf")

from pypdf import PdfWriter  # noqa: E402

from src import extract  # noqa: E402
from src.extract import ExtractionError, extract_pdf, extract_submission, normalise  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_extraction import fidelity  # noqa: E402

PITCHES = {r["pitch_id"]: r for r in map(json.loads, (ROOT / "data/pitches.jsonl").read_text().splitlines()) if r}


def blank_pdf(pages=1, password=None) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    if password is not None:
        writer.encrypt(password)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def corpus_pdf(pid="P001") -> bytes:
    return (ROOT / "data/pdfs" / f"{pid}.pdf").read_bytes()


class TestPdf:
    @pytest.mark.parametrize("pid", ["P001", "P002", "P003"])   # les trois mises en page
    def test_corpus_redonne_les_memes_mots(self, pid):
        assert fidelity(PITCHES[pid]["pitch_text"], extract_pdf(corpus_pdf(pid))) >= 0.98

    def test_fichier_vide(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(b"")
        assert err.value.code == "empty"

    def test_pas_un_pdf(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(b"GIF89a....")
        assert err.value.code == "not_pdf"

    def test_pdf_corrompu(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(b"%PDF-1.7\n" + b"\x00garbage" * 50)
        assert err.value.code in ("corrupt_pdf", "empty")

    def test_pdf_tronque(self):
        data = corpus_pdf()
        with pytest.raises(ExtractionError) as err:
            extract_pdf(data[: len(data) // 3])
        assert err.value.code in ("corrupt_pdf", "no_text_layer")

    def test_pdf_scanne_sans_couche_texte(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(blank_pdf(pages=3))
        assert err.value.code == "no_text_layer"

    def test_pdf_protege_par_mot_de_passe(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(blank_pdf(password="secret"))
        assert err.value.code == "encrypted_pdf"

    def test_trop_de_pages(self):
        with pytest.raises(ExtractionError) as err:
            extract_pdf(blank_pdf(pages=extract.MAX_PAGES + 1))
        assert err.value.code == "too_large"


class TestNettoyage:
    def test_recolle_les_lignes_coupees(self):
        assert normalise("Industry consumes roughly\n95 million tonnes of\nhydrogen a year.") == \
            "Industry consumes roughly 95 million tonnes of hydrogen a year."

    def test_garde_les_titres(self):
        assert normalise("The Problem\nIndustry consumes") == "The Problem\nIndustry consumes"

    def test_reforme_un_mot_coupe(self):
        assert normalise("they cannot decarbon-\nise it") == "they cannot decarbonise it"

    def test_retire_les_caracteres_de_controle(self):
        assert normalise("a\x00b\x07c") == "abc"


class TestLiens:
    @pytest.mark.parametrize("url", [
        "http://localhost:11434/api/tags",          # le serveur Ollama du fonds
        "http://127.0.0.1/",
        "http://10.0.0.5/deck.pdf",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data",  # métadonnées cloud
        "http://[::1]/",
        "file:///etc/passwd",
        "ftp://example.com/deck.pdf",
    ])
    def test_adresses_non_publiques_refusees(self, url):
        with pytest.raises(ExtractionError) as err:
            extract._check_host(url)
        assert err.value.code == "blocked_link"

    def test_lien_vers_un_pdf(self, monkeypatch):
        monkeypatch.setattr(extract, "_fetch", lambda url: (corpus_pdf("P002"), "application/octet-stream"))
        text = extract.extract_link("https://example.com/deck")
        assert fidelity(PITCHES["P002"]["pitch_text"], text) >= 0.98

    def test_page_html_reduite_a_son_texte(self, monkeypatch):
        html = "<html><head><title>x</title><script>alert(1)</script></head><body><h1>Acme</h1>" \
               "<p>" + "We sell software to dentists. " * 20 + "</p></body></html>"
        monkeypatch.setattr(extract, "_fetch", lambda url: (html.encode(), "text/html"))
        text = extract.extract_link("https://acme.example/")
        assert "alert" not in text and text.startswith("Acme")

    def test_docsend_vide_est_signale(self, monkeypatch):
        monkeypatch.setattr(extract, "_fetch", lambda url: (b"<html><body>Loading...</body></html>", "text/html"))
        with pytest.raises(ExtractionError) as err:
            extract.extract_link("https://docsend.com/view/abc")
        assert err.value.code == "unsupported_link"

    def test_trouve_les_liens_d_un_message(self):
        assert extract.find_links("Deck: https://a.com/x.pdf, and (https://b.org/y).") == \
            ["https://a.com/x.pdf", "https://b.org/y"]


class TestSoumission:
    def test_message_plus_pdf(self):
        event = {"text": "Hi, deck attached.", "attachments": [{"type": "pdf", "name": "deck.pdf", "content": corpus_pdf()}]}
        result = extract_submission(event)
        assert result.ok
        assert [s.status for s in result.sources] == ["ok", "ok"]
        assert "[pièce jointe : deck.pdf]" in result.text

    def test_pdf_illisible_est_rapporte_pas_cache(self):
        event = {"text": "See attached", "attachments": [{"type": "pdf", "name": "scan.pdf", "content": blank_pdf()}]}
        result = extract_submission(event)
        assert not result.ok
        assert result.sources[-1].status == "no_text_layer"
        assert result.warnings

    def test_lien_bloque_ne_fait_pas_echouer_le_reste(self):
        event = {"text": PITCHES["P001"]["pitch_text"], "links": ["http://localhost:11434/api/tags"]}
        result = extract_submission(event)
        assert result.ok
        assert result.sources[-1].status == "blocked_link"

    def test_texte_trop_long_tronque_et_signale(self):
        result = extract_submission({"text": "word " * (extract.MAX_CHARS // 2)})
        assert len(result.text) == extract.MAX_CHARS
        assert any("tronqué" in w for w in result.warnings)

    def test_soumission_vide(self):
        result = extract_submission({})
        assert not result.ok and result.text == ""
