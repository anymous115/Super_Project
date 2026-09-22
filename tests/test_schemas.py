"""Validation des sorties structurées (§7).

Le point central : une sortie invalide est un **échec enregistré**, jamais une
sortie réparée en douce. Le taux de JSON valide est une métrique.
"""
import json

import pytest

from src.schemas import PitchScore, parse_output, strip_wrappers

VALIDE = {
    "pitch_id": "P001",
    "scores": {"team": 4, "market": 5, "product": 3, "traction": 4, "business_model": 3},
    "total_score": 82.0,
    "strengths": ["team has shipped before"],
    "risks": ["long sales cycle"],
    "missing_information": ["no churn figure"],
    "recommendation": "shortlist",
    "evidence": ["\"revenue of $2.8M\""],
}


def brut(**changes):
    payload = json.loads(json.dumps(VALIDE))
    payload.update(changes)
    return json.dumps(payload)


class TestTotal:
    def test_le_total_est_recalcule_dans_le_code(self):
        """4/5/3/4/3 -> 16 + 25 + 9 + 20 + 9 = 79, quoi que dise le modèle."""
        score = PitchScore.model_validate(VALIDE)
        assert score.computed_total() == pytest.approx(79.0)
        assert score.total_score == 82.0          # ce que le modèle a annoncé
        assert score.total_drift() == pytest.approx(3.0)

    def test_un_total_faux_ne_rend_pas_la_sortie_invalide(self):
        """L'arithmétique du modèle est une mesure, pas un motif de rejet."""
        result = parse_output(brut(total_score=0))
        assert result.ok
        assert result.parsed.computed_total() == pytest.approx(79.0)


class TestValidation:
    def test_sortie_conforme(self):
        result = parse_output(json.dumps(VALIDE))
        assert result.ok
        assert result.valid_json_strict

    @pytest.mark.parametrize("note", [-1, 6, 2.5, "quatre"])
    def test_note_hors_echelle_rejetee(self, note):
        payload = json.loads(json.dumps(VALIDE))
        payload["scores"]["team"] = note
        result = parse_output(json.dumps(payload))
        assert not result.ok
        assert "schéma" in result.error

    def test_recommandation_hors_liste_rejetee(self):
        result = parse_output(brut(recommendation="strong buy"))
        assert not result.ok

    def test_champ_manquant_rejete(self):
        payload = json.loads(json.dumps(VALIDE))
        del payload["missing_information"]
        assert not parse_output(json.dumps(payload)).ok

    def test_champ_en_trop_rejete(self):
        assert not parse_output(brut(confidence=0.9)).ok

    def test_sortie_vide_rejetee(self):
        result = parse_output("")
        assert not result.ok
        assert result.error == "réponse vide"


class TestEnveloppes:
    """Les deux taux rapportés côte à côte : strict, et après nettoyage."""

    def test_texte_autour_du_json_nest_pas_strict(self):
        raw = "Voici mon évaluation :\n" + json.dumps(VALIDE)
        result = parse_output(raw)
        assert not result.valid_json_strict
        assert not result.valid_json_cleaned      # ce préambule n'est pas une enveloppe connue
        assert not result.ok

    def test_cloture_markdown_nettoyee_mais_pas_stricte(self):
        raw = "```json\n" + json.dumps(VALIDE) + "\n```"
        result = parse_output(raw)
        assert not result.valid_json_strict
        assert result.valid_json_cleaned
        assert result.ok

    def test_bloc_think_nettoye_mais_pas_strict(self):
        """deepseek-r1 émet son raisonnement avant la réponse."""
        raw = "<think>Let me work through the grid.</think>\n" + json.dumps(VALIDE)
        result = parse_output(raw)
        assert not result.valid_json_strict
        assert result.valid_json_cleaned
        assert result.ok

    def test_strip_wrappers_laisse_le_json_intact(self):
        assert json.loads(strip_wrappers(json.dumps(VALIDE)))["pitch_id"] == "P001"
