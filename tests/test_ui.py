"""Les primitives visuelles : niveaux de score, accessibilité, et surtout l'échappement.

Les noms d'entreprise viennent de fondateurs inconnus (Telegram, e-mail) : rien de ce
qui est dynamique ne doit pouvoir injecter une balise dans la page.
"""
import pytest

from src import ui

PIEGE = '<img src=x onerror="alert(1)">'


@pytest.mark.parametrize("score, attendu", [
    (None, "none"), (0, "low"), (49.9, "low"), (50, "mid"), (74.9, "mid"), (75, "high"), (100, "high"),
])
def test_niveaux_de_score_suivent_les_seuils_du_produit(score, attendu):
    assert ui.tier(score) == attendu


def test_anneau_porte_son_sens_dans_aria_label_et_borne_le_score():
    html = ui.score_ring(82.4, label="Score")
    assert 'role="img"' in html and 'aria-label="Score 82 / 100"' in html and "ring--high" in html
    assert "--pct:100.0" in ui.score_ring(140)
    assert "--pct:0.0" in ui.score_ring(-5)


def test_anneau_sans_score_est_vide_et_lisible():
    html = ui.score_ring(None, label="Score")
    assert "ring--none" in html and "—" in html and "--pct" not in html


def test_chiffre_anime_garde_le_vrai_nombre_pour_les_lecteurs_d_ecran():
    html = ui.stat_card("Scorés", 50, "Analyses", "chart")
    assert '<span class="sr-only">50</span>' in html and "--v:50" in html


def test_aucune_primitive_ne_laisse_passer_une_balise():
    sorties = [
        ui.tag(PIEGE, PIEGE),
        ui.score_ring(80, label=PIEGE),
        ui.stat_card(PIEGE, 3, PIEGE, "inbox", tone=PIEGE),
        ui.dossier_card(status=PIEGE, status_tone="warning", name=PIEGE, idea=PIEGE, sector=PIEGE,
                        pitch_id=PIEGE, score=60, verdict=PIEGE, ring_label=PIEGE),
        ui.featured(PIEGE, PIEGE, PIEGE, PIEGE, 90, PIEGE),
        ui.profile_header(PIEGE, PIEGE, [PIEGE], 70, PIEGE, "high", PIEGE),
        ui.bar_row(PIEGE, 2, 5, PIEGE),
        ui.distribution([(PIEGE, 4), ("20–39", 0)]),
        ui.empty_state(PIEGE, PIEGE),
        ui.page_header(PIEGE, PIEGE, PIEGE),
        ui.hero_title(PIEGE, PIEGE),
        ui.section_head(PIEGE, PIEGE),
    ]
    for html in sorties:
        assert "<img" not in html and 'onerror="' not in html, html[:200]


def test_barre_est_un_indicateur_accessible_et_reste_dans_ses_bornes():
    html = ui.bar_row("Équipe", 4, 5, " / 5")
    assert 'role="meter"' in html and 'aria-valuenow="4"' in html and 'aria-valuemax="5"' in html
    assert "width:80.0%" in html
    assert "width:100.0%" in ui.bar_row("x", 9, 5)
    assert "width:0.0%" in ui.bar_row("x", 3, 0)          # maximum nul : pas de division par zéro


def test_histogramme_vide_ne_dessine_pas_de_fausse_barre():
    html = ui.distribution([("0–19", 0), ("20–39", 0)])
    assert html.count("height:1.5%") == 2                  # un simple repère, pas une colonne trompeuse


def test_histogramme_met_la_plus_haute_tranche_a_pleine_hauteur():
    html = ui.distribution([("a", 10), ("b", 5)])
    assert "height:100.0%" in html and "height:50.0%" in html


def test_navigation_a_une_icone_par_page_et_toutes_existent():
    assert len(ui.NAV_ICONS) == 5 and all(name in ui.ICONS for name in ui.NAV_ICONS)
    css = ui.nav_icon_css()
    assert css.count("mask-image") == 2 * len(ui.NAV_ICONS)
    assert 'role="radiogroup"] label:nth-of-type(1)' in css      # jamais le libellé du groupe


def test_icones_sont_des_masques_css_car_streamlit_retire_les_svg_en_ligne():
    html = ui.icon("inbox", 16)
    assert "<svg" not in html and 'class="ico ico--inbox"' in html and "--size:16px" in html
    css = ui.icons_css()
    assert all(f".ico--{name}" in css for name in ui.ICONS)
    assert "<" not in css and ">" not in css.replace("> ", "")   # DOMPurify supprime un bloc de style contenant un chevron brut


def test_en_tete_de_page_hero_accepte_le_fragment_compose():
    titre = ui.hero_title("Repérez le potentiel.", "Gardez une longueur d’avance.")
    html = ui.page_header("UNICORNEXT", titre, "Sous-titre", hero=True)
    assert '<span class="hl">' in html and 'class="display"' in html
    assert "&lt;" in ui.page_header("x", "<b>", "y") and "<b>" not in ui.page_header("x", "<b>", "y")


def test_le_banc_d_essai_visuel_s_affiche_sans_erreur():
    """scripts/ui_showcase.py montre chaque primitive, y compris le contenu hostile."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file("../scripts/ui_showcase.py").run()
    assert not app.exception
    assert any(b.key == "open_showcase_4" for b in app.button)      # la carte au contenu hostile est bien rendue


def test_amorceur_du_champ_de_points_ne_casse_pas_sa_propre_page():
    """Le script est recopié dans une chaîne JavaScript à l'intérieur d'un <script> : il ne doit
    pas pouvoir fermer cette balise plus tôt, ni laisser de retour à la ligne brut dans la chaîne."""
    from pathlib import Path

    js = (Path(__file__).resolve().parent.parent / "assets" / "sonar.js").read_text(encoding="utf-8")
    html = ui.sonar_html(js)
    assert html.count("</script>") == 1 and html.endswith("</script>")
    assert "\n" not in html                                              # une seule ligne : la chaîne est échappée
    assert "unicornext-sonar-js" in html and "window.parent" in html     # garde contre le double lancement
    assert "</script>" not in ui.sonar_html("var x = '</script><b>';")[:-len("</script>")]
