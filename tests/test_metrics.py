"""La règle de sélection et les métriques de classement, vérifiées à la main."""
import math

import pytest

from src.metrics import (
    mae,
    mae_by_criterion,
    percentile,
    rank_pitches,
    rate,
    select,
    selection_size,
    spearman,
    top_k_overlap,
)


class TestSelectionRule:
    """min(50, max(5, ceil(n x 0,10))) — les trois régimes du §5."""

    @pytest.mark.parametrize(
        "volume, expected",
        [
            (20, 5),      # sous 50 : le plancher
            (49, 5),
            (50, 5),      # le point de croisement : 10 % font exactement 5
            (51, 6),      # au-dessus : le régime 10 % prend le relais
            (200, 20),
            (500, 50),
            (2000, 50),   # le plafond
        ],
    )
    def test_les_trois_regimes(self, volume, expected):
        assert selection_size(volume) == expected

    def test_les_regimes_se_rejoignent_sans_saut(self):
        """Aucun effet de seuil autour de n = 50."""
        assert selection_size(50) == selection_size(49) == 5
        assert selection_size(51) - selection_size(50) == 1

    def test_on_ne_selectionne_jamais_plus_que_recu(self):
        assert selection_size(3) == 3
        assert selection_size(0) == 0


class TestClassement:
    def test_egalite_departagee_sur_la_traction_puis_le_marche(self):
        totals = {"P001": 70.0, "P002": 70.0, "P003": 70.0}
        notes = {
            "P001": {"traction": 3, "market": 5},
            "P002": {"traction": 4, "market": 2},
            "P003": {"traction": 3, "market": 4},
        }
        assert rank_pitches(totals, notes) == ["P002", "P001", "P003"]

    def test_ordre_deterministe_sans_notes(self):
        totals = {"P002": 70.0, "P001": 70.0}
        assert rank_pitches(totals) == ["P001", "P002"]

    def test_select_respecte_la_regle(self):
        totals = {f"P{i:03d}": float(100 - i) for i in range(1, 51)}
        chosen = select(totals)
        assert len(chosen) == 5
        assert chosen == ["P001", "P002", "P003", "P004", "P005"]


class TestQualite:
    def test_mae(self):
        assert mae({"a": 10.0, "b": 20.0}, {"a": 12.0, "b": 17.0}) == pytest.approx(2.5)

    def test_mae_par_critere(self):
        predicted = {"P1": {"team": 4, "market": 3, "product": 2, "traction": 1, "business_model": 0}}
        reference = {"P1": {"team": 3, "market": 3, "product": 4, "traction": 1, "business_model": 2}}
        result = mae_by_criterion(predicted, reference)
        assert result["team"] == pytest.approx(1.0)
        assert result["market"] == pytest.approx(0.0)
        assert result["product"] == pytest.approx(2.0)

    def test_spearman_valeur_connue(self):
        """rho = 1 - 6 x somme(d^2) / (n(n^2-1)) = 1 - 24/120 = 0,8."""
        predicted = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        reference = {"a": 2, "b": 1, "c": 4, "d": 3, "e": 5}
        assert spearman(predicted, reference) == pytest.approx(0.8)

    def test_spearman_aux_extremes(self):
        identiques = {"a": 1, "b": 2, "c": 3}
        assert spearman(identiques, identiques) == pytest.approx(1.0)
        assert spearman(identiques, {"a": 3, "b": 2, "c": 1}) == pytest.approx(-1.0)

    def test_spearman_gere_les_ex_aequo(self):
        """Des ex aequo traités par rangs moyens, pas par ordre d'apparition."""
        predicted = {"a": 1, "b": 1, "c": 2}
        reference = {"a": 1, "b": 1, "c": 2}
        assert spearman(predicted, reference) == pytest.approx(1.0)

    def test_spearman_refuse_une_variance_nulle(self):
        with pytest.raises(ValueError):
            spearman({"a": 1, "b": 1}, {"a": 1, "b": 2})

    def test_top_k_overlap(self):
        reference = {f"P{i:03d}": float(100 - i) for i in range(1, 51)}
        parfait = dict(reference)
        assert top_k_overlap(parfait, reference) == pytest.approx(1.0)

        # Un seul dossier de la sélection remplacé : 4 sur 5.
        abime = dict(reference)
        abime["P005"], abime["P040"] = abime["P040"], abime["P005"]
        assert top_k_overlap(abime, reference) == pytest.approx(0.8)

    def test_rate(self):
        assert rate([True, True, False, False]) == pytest.approx(0.5)
        assert rate([]) == 0.0


class TestPerformance:
    def test_percentile(self):
        serie = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert percentile(serie, 50) == pytest.approx(5.5)
        assert percentile(serie, 0) == 1
        assert percentile(serie, 100) == 10

    def test_percentile_serie_vide(self):
        with pytest.raises(ValueError):
            percentile([], 50)
