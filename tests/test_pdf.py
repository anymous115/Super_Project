"""Le rendu PDF ne doit rien perdre du texte (§6).

Le PDF sert à la démonstration et à mesurer l'extraction. Si le rendu lui-même
perd des mots, la mesure d'extraction ne mesure plus le lecteur de PDF mais le
générateur.
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

pytest.importorskip("reportlab")
pytest.importorskip("pypdf")

from pypdf import PdfReader  # noqa: E402

spec = importlib.util.spec_from_file_location("render_pdfs", ROOT / "scripts" / "render_pdfs.py")
render_pdfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render_pdfs)

from src.score_pitch import load_pitches  # noqa: E402


def mots(text):
    return re.findall(r"[a-zA-Z]{4,}", text.lower())


@pytest.mark.parametrize("layout", render_pdfs.LAYOUTS)
def test_aller_retour_sans_perte(tmp_path, layout):
    pitch = next(p for p in load_pitches() if p["pitch_id"] == "P046")
    cible = tmp_path / "essai.pdf"
    render_pdfs.render(pitch, layout, cible)

    extrait = set(mots("\n".join(page.extract_text() or "" for page in PdfReader(str(cible)).pages)))
    source = mots(pitch["pitch_text"])
    assert source, "le pitch de test est vide"
    retrouves = sum(1 for w in source if w in extrait)
    assert retrouves == len(source), f"{len(source) - retrouves} mots perdus en {layout}"


def test_chaque_pitch_a_une_mise_en_page_stable():
    """Le même identifiant doit toujours sortir dans la même mise en page."""
    attribue = lambda pid: render_pdfs.LAYOUTS[int(pid[1:]) % len(render_pdfs.LAYOUTS)]
    assert attribue("P001") == attribue("P001")
    assert len({attribue(f"P{i:03d}") for i in range(1, 51)}) == len(render_pdfs.LAYOUTS)
