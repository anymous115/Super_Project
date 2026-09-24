"""De la boîte de réception aux files de l'interface, modèle remplacé.

Le parcours complet sans réseau ni Ollama : une soumission Telegram avec un
PDF, un pitch piégé, un PDF scanné, un message trop court. Chacun doit finir
dans la bonne file, et relancer ne doit rien renoter.
"""
import io
import json
import re
from pathlib import Path

import pytest

pytest.importorskip("pypdf")

from pypdf import PdfWriter  # noqa: E402

from src import score_pitch as sp  # noqa: E402
from src.ingest.normalize import Draft, Inbox, PendingAttachment  # noqa: E402
from src.triage import SCORE_FILE, load_queue, pending, process_inbox  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PITCHES = {r["pitch_id"]: r for r in map(json.loads, (ROOT / "data/pitches.jsonl").read_text().splitlines()) if r}

# Note renvoyée par le faux modèle, par soumission.
NOTES = {"SUB-0001": 4, "SUB-0002": 5, "SUB-0003": 2}


def fake_model(model, system, user):
    sid = re.search(r"pitch_id: (SUB-\d+)", user).group(1)
    n = NOTES.get(sid, 3)
    text = json.dumps({
        "pitch_id": sid, "scores": {c: n for c in ("team", "market", "product", "traction", "business_model")},
        "total_score": 5 * n, "strengths": [], "risks": [], "missing_information": [],
        "recommendation": "review", "evidence": ["x"],
    })
    return sp.ModelReply(text=text, input_tokens=1000, output_tokens=400, model_version="fake", done_reason="stop")


class Calls:
    def __init__(self):
        self.n = 0

    def __call__(self, *args):
        self.n += 1
        return fake_model(*args)


def draft(text="", pdf=None, ref="telegram:1:1"):
    attachments = [PendingAttachment("deck.pdf", lambda: pdf)] if pdf is not None else []
    return Draft(channel="telegram", received_at="2026-09-24T10:00:00Z", sender_handle="@founder",
                 text=text, links=[], source_ref=ref, attachments=attachments)


def blank_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@pytest.fixture
def inbox(tmp_path):
    box = Inbox(tmp_path / "inbox")
    box.add(draft("Deck attached.", pdf=(ROOT / "data/pdfs/P001.pdf").read_bytes(), ref="t:1"))   # SUB-0001
    box.add(draft(PITCHES["P002"]["pitch_text"], ref="t:2"))                                     # SUB-0002
    box.add(draft(PITCHES["P003"]["pitch_text"], ref="t:3"))                                     # SUB-0003
    box.add(draft(PITCHES["P025"]["pitch_text"], ref="t:4"))                                     # SUB-0004, piège
    box.add(draft("See scan.", pdf=blank_pdf(), ref="t:5"))                                      # SUB-0005, scanné
    box.add(draft("Hi, interested?", ref="t:6"))                                                 # SUB-0006, trop court
    return box


def test_chaque_soumission_finit_dans_sa_file(inbox, monkeypatch):
    monkeypatch.setitem(sp.BACKENDS, "ollama", Calls())
    results = {p["submission_id"]: p["status"] for p in process_inbox(inbox)}
    assert results == {
        "SUB-0001": "scored", "SUB-0002": "scored", "SUB-0003": "scored",
        "SUB-0004": "review", "SUB-0005": "unreadable", "SUB-0006": "unreadable",
    }


def test_le_pdf_joint_est_lu(inbox, monkeypatch):
    monkeypatch.setitem(sp.BACKENDS, "ollama", Calls())
    process_inbox(inbox)
    payload = json.loads((inbox.root / "SUB-0001" / SCORE_FILE).read_text())
    assert [s["status"] for s in payload["extraction"]["sources"]] == ["ok", "ok"]
    assert payload["extraction"]["words"] > 300


def test_classement_et_selection_hors_pieges(inbox, monkeypatch):
    monkeypatch.setitem(sp.BACKENDS, "ollama", Calls())
    process_inbox(inbox)
    queue = load_queue(inbox)
    assert [p["submission_id"] for p in queue.ranked] == ["SUB-0002", "SUB-0001", "SUB-0003"]
    assert "SUB-0004" not in queue.selected
    assert [p["submission_id"] for p in queue.review] == ["SUB-0004"]
    assert set(queue.review[0]["run"]["guard_families"]) >= {"addressed_to_ai", "override"}
    assert len(queue.unreadable) == 2


def test_relancer_ne_renote_rien(inbox, monkeypatch):
    calls = Calls()
    monkeypatch.setitem(sp.BACKENDS, "ollama", calls)
    process_inbox(inbox)
    first = calls.n
    assert first == 4                 # les deux illisibles n'appellent pas le modèle
    assert process_inbox(inbox) == [] and calls.n == first
    assert pending(inbox) == []


def test_nouvelle_soumission_en_attente_puis_notee(inbox, monkeypatch):
    monkeypatch.setitem(sp.BACKENDS, "ollama", Calls())
    process_inbox(inbox)
    inbox.add(draft(PITCHES["P004"]["pitch_text"], ref="t:7"))
    assert load_queue(inbox).waiting == ["SUB-0007"]
    process_inbox(inbox)
    assert load_queue(inbox).waiting == []


def test_modele_sans_sortie_exploitable(inbox, monkeypatch):
    monkeypatch.setitem(sp.BACKENDS, "ollama",
                        lambda m, s, u: sp.ModelReply(text="", input_tokens=0, output_tokens=0, model_version="fake"))
    process_inbox(inbox, limit=1)
    assert json.loads((inbox.root / "SUB-0001" / SCORE_FILE).read_text())["status"] == "error"
    assert [p["submission_id"] for p in load_queue(inbox).errors] == ["SUB-0001"]
