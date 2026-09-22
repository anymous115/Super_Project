"""Le corpus tel que le pipeline le voit — la jonction entre données et code."""
import re

from src.metrics import selection_size
from src.prompts import build_prompt
from src.score_pitch import injection_ids, load_pitches


def test_cinquante_pitchs_tous_rediges():
    pitchs = load_pitches()
    assert len(pitchs) == 50
    assert all(p["pitch_text"].strip() for p in pitchs)


def test_ordre_du_fichier_preserve():
    """L'ordre de passage fait partie des conditions contrôlées (§10)."""
    ids = [p["pitch_id"] for p in load_pitches()]
    assert ids == sorted(ids)


def test_cinq_pitchs_a_injection():
    assert injection_ids() == ["P025", "P031", "P036", "P044", "P049"]


def test_aucune_donnee_personnelle_dans_le_corpus():
    fuite = re.compile(r"[\w.+-]+@[\w-]+\.\w+|https?://|\+\d{2}[\s\d]{8,}")
    coupables = [p["pitch_id"] for p in load_pitches() if fuite.search(p["pitch_text"])]
    assert coupables == []


def test_le_piege_ne_se_voit_pas_dans_le_prompt():
    piege = next(p for p in load_pitches() if p["is_injection_test"])
    system, user = build_prompt("V2", piege["pitch_id"], piege["pitch_text"])
    assert "is_injection_test" not in system + user


def test_a_cinquante_pitchs_la_regle_retient_cinq_dossiers():
    assert selection_size(len(load_pitches())) == 5
