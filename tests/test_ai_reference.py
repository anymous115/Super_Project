"""Référence IA : validation des réponses et mesure d'accord (docs/AI_REFERENCE.md).

Aucun appel réseau : on teste ce qui décide si une note entre dans la référence.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


annotate_ai = _load("annotate_ai")
build_ai_reference = _load("build_ai_reference")
CRITERIA = annotate_ai.CRITERIA


def answer(**notes):
    return {
        "scores": {c: notes.get(c, 3) for c in CRITERIA},
        "evidence": {c: f"extrait {c}" for c in CRITERIA},
        "recommendation": notes.get("recommendation", "review"),
    }


def row(pitch_id, who, **notes):
    data = annotate_ai.validate(answer(**notes))
    return {"pitch_id": pitch_id, "annotator": who, **data,
            "total_score": round(annotate_ai.weighted_total(data["scores"]), 1)}


class TestReponse:
    def test_json_dans_une_cloture_markdown(self):
        text = '```json\n{"scores": {}}\n```'
        assert annotate_ai.extract_json(text) == {"scores": {}}

    def test_json_entoure_de_texte(self):
        assert annotate_ai.extract_json('Voici : {"a": 1} fin') == {"a": 1}

    def test_pas_de_json(self):
        with pytest.raises(annotate_ai.InvalidAnnotation):
            annotate_ai.extract_json("aucune accolade")

    @pytest.mark.parametrize("note", [4.5, 6, -1, "4", True])
    def test_note_non_entiere_ou_hors_echelle(self, note):
        data = answer()
        data["scores"]["traction"] = note
        with pytest.raises(annotate_ai.InvalidAnnotation):
            annotate_ai.validate(data)

    def test_note_sans_justification(self):
        data = answer()
        data["evidence"]["team"] = "  "
        with pytest.raises(annotate_ai.InvalidAnnotation):
            annotate_ai.validate(data)

    def test_recommandation_inconnue(self):
        with pytest.raises(annotate_ai.InvalidAnnotation):
            annotate_ai.validate(answer(recommendation="invest"))

    def test_le_prompt_ne_montre_aucune_cible(self):
        assert "target" not in annotate_ai.SYSTEM.lower()
        assert "calibration" not in annotate_ai.SYSTEM.lower()


class TestEchantillon:
    def test_chaque_pitch_a_deux_humains(self):
        counts = {}
        for ids in build_ai_reference.VALIDATION_SAMPLE.values():
            for p in ids:
                counts[p] = counts.get(p, 0) + 1
        assert len(counts) == 12
        assert set(counts.values()) == {2}

    def test_echantillon_dans_les_binomes_prevus(self):
        from build_calibration import ANNOTATORS
        for who, ids in build_ai_reference.VALIDATION_SAMPLE.items():
            for p in ids:
                assert who in ANNOTATORS[p], f"{who} n'annote pas {p}"


class TestAccord:
    def test_ia_alignee_est_acceptee(self):
        ai = {p: row(p, "AI", team=t, traction=t) for p, t in [("P1", 1), ("P2", 3), ("P3", 5)]}
        humans = {p: {"A": row(p, "A", team=t, traction=t), "C": row(p, "C", team=t, traction=t)}
                  for p, t in [("P1", 1), ("P2", 3), ("P3", 5)]}
        result = build_ai_reference.agreement(ai, humans)
        assert result["verdict"] == "accepted"
        assert result["ai_human_gap"] == 0

    def test_ia_inversee_est_rejetee(self):
        ai = {p: row(p, "AI", team=t, traction=t) for p, t in [("P1", 5), ("P2", 3), ("P3", 1)]}
        humans = {p: {"A": row(p, "A", team=t, traction=t), "C": row(p, "C", team=t, traction=t)}
                  for p, t in [("P1", 1), ("P2", 3), ("P3", 5)]}
        assert build_ai_reference.agreement(ai, humans)["verdict"] == "rejected"

    def test_sans_double_annotation_humaine_on_ne_juge_pas(self):
        ai = {"P1": row("P1", "AI")}
        humans = {"P1": {"A": row("P1", "A")}}
        assert build_ai_reference.agreement(ai, humans)["verdict"] == "insufficient"
