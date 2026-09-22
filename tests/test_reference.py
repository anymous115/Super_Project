"""Fusion des annotations en référence (§6).

Le seuil de réconciliation est le cœur du protocole d'annotation : un écart de
plus d'un point ne se moyenne pas, il se discute.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("build_reference", ROOT / "scripts" / "build_reference.py")
build_reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_reference)

merge = build_reference.merge
CRITERIA = build_reference.CRITERIA


def annotation(who, **notes):
    scores = {c: notes.get(c, 3) for c in CRITERIA}
    return {
        "pitch_id": "P001",
        "annotator": who,
        "scores": scores,
        "evidence": {c: f"extrait {c}" for c in CRITERIA},
        "recommendation": notes.get("recommendation", "review"),
    }


class TestCompletude:
    def test_une_seule_annotation_ne_suffit_pas(self):
        row = merge("P001", ("A", "B"), {"A": annotation("A")}, {})
        assert row["status"] == "incomplete"
        assert row["missing"] == ["B"]

    def test_aucune_annotation(self):
        row = merge("P001", ("A", "B"), {}, {})
        assert row["status"] == "incomplete"
        assert row["missing"] == ["A", "B"]


class TestSeuil:
    def test_accord_parfait(self):
        row = merge("P001", ("A", "B"), {"A": annotation("A"), "B": annotation("B")}, {})
        assert row["status"] == "agreed"
        assert row["max_gap"] == 0
        assert row["total_score"] == pytest.approx(60.0)   # 3 partout

    def test_un_point_d_ecart_se_moyenne(self):
        """Le seuil est strictement supérieur à 1 : un point passe."""
        found = {"A": annotation("A", team=4), "B": annotation("B", team=3)}
        row = merge("P001", ("A", "B"), found, {})
        assert row["status"] == "agreed"
        assert row["max_gap"] == 1
        assert row["scores"]["team"] == pytest.approx(3.5)

    def test_deux_points_d_ecart_bloquent(self):
        found = {"A": annotation("A", market=5), "B": annotation("B", market=3)}
        row = merge("P001", ("A", "B"), found, {})
        assert row["status"] == "disputed"
        assert row["criteria"] == ["market"]
        assert row["max_gap"] == 2
        assert "total_score" not in row      # rien n'est produit tant que ce n'est pas tranché

    def test_plusieurs_criteres_en_desaccord_sont_tous_listes(self):
        found = {
            "A": annotation("A", market=5, traction=5),
            "B": annotation("B", market=3, traction=1),
        }
        row = merge("P001", ("A", "B"), found, {})
        assert row["criteria"] == ["market", "traction"]
        assert row["max_gap"] == 4


class TestReconciliation:
    def test_un_desaccord_tranche_est_accepte(self):
        found = {"A": annotation("A", market=5), "B": annotation("B", market=1)}
        settled = {"P001": {"pitch_id": "P001",
                            "scores": {c: 3 for c in CRITERIA},
                            "reason": "discuté le 22 septembre"}}
        row = merge("P001", ("A", "B"), found, settled)
        assert row["status"] == "reconciled"
        assert row["scores"]["market"] == 3
        assert row["total_score"] == pytest.approx(60.0)

    def test_la_valeur_tranchee_prime_sur_la_moyenne(self):
        found = {"A": annotation("A", team=4), "B": annotation("B", team=4)}
        settled = {"P001": {"pitch_id": "P001",
                            "scores": {**{c: 3 for c in CRITERIA}, "team": 2},
                            "reason": "relu ensemble"}}
        row = merge("P001", ("A", "B"), found, settled)
        assert row["scores"]["team"] == 2


class TestRecommandation:
    def test_accord_conserve(self):
        found = {"A": annotation("A", recommendation="shortlist"),
                 "B": annotation("B", recommendation="shortlist")}
        row = merge("P001", ("A", "B"), found, {})
        assert row["recommendation"] == "shortlist"
        assert row["recommendation_disputed"] is False

    def test_desaccord_retient_la_plus_prudente_et_le_signale(self):
        found = {"A": annotation("A", recommendation="shortlist"),
                 "B": annotation("B", recommendation="reject")}
        row = merge("P001", ("A", "B"), found, {})
        assert row["recommendation"] == "reject"
        assert row["recommendation_disputed"] is True


class TestTracabilite:
    def test_les_deux_justifications_sont_conservees(self):
        found = {"A": annotation("A"), "B": annotation("B")}
        row = merge("P001", ("A", "B"), found, {})
        assert set(row["evidence"]) == {"A", "B"}
        assert set(row["evidence"]["A"]) == set(CRITERIA)
