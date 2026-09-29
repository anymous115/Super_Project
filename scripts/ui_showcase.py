"""Toutes les primitives d'Unicornext, dans tous leurs états (DESIGN.md, section 5).

    streamlit run scripts/ui_showcase.py

Sert de banc d'essai visuel : on y vérifie chaque composant à 375, 768 et 1280 px avant de le
poser dans une page. Aucune donnée réelle : tout est écrit ici, y compris les cas limites
(nom très long, contenu hostile) que l'app doit encaisser.
"""
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
import streamlit.components.v1 as components  # noqa: E402

from src import ui  # noqa: E402

ASSETS = ROOT / "assets"

st.set_page_config(page_title="Unicornext · composants", page_icon="✦", layout="wide")
st.html(ASSETS / "unicornext.css")
st.html(f"<style>{ui.icons_css()}\n{ui.nav_icon_css()}</style>")
components.html(ui.sonar_html((ASSETS / "sonar.js").read_text(encoding="utf-8")), height=0)
logo = base64.b64encode((ASSETS / "unicornext-logo.png").read_bytes()).decode()
st.sidebar.html(f'<img class="brand-logo" src="data:image/png;base64,{logo}" alt="Unicornext">')
st.sidebar.radio("Espace investisseur", ["a", "b", "c", "d", "e"],
                 format_func=lambda k: {"a": "Vue d’ensemble", "b": "Explorer", "c": "Fiche", "d": "Shortlist", "e": "Déposer"}[k])
st.sidebar.caption("Banc d'essai des composants. Cette navigation ne mène nulle part.")

PIEGE = '<img src=x onerror="alert(1)">Startup piégée'
LONG = "Compagnie internationale de transformation des matières premières et de logistique du dernier kilomètre"

st.html(ui.page_header("UNICORNEXT / COMPOSANTS", "Banc d’essai visuel",
                       "Chaque primitive, chaque état. Le contenu hostile doit s’afficher comme du texte, jamais comme du HTML."))

st.html(ui.section_head("Tags", "Le libellé porte le sens, la couleur le renforce."))
st.html('<div style="display:flex;gap:12px;flex-wrap:wrap">'
        + ui.tag("Priorité élevée", "high", dot=True) + ui.tag("À approfondir", "mid", dot=True)
        + ui.tag("Non prioritaire", "low", dot=True) + ui.tag("Intégrité : alerte", "warning", dot=True)
        + ui.tag("À scorer", "neutral", dot=True) + "</div>")

st.html(ui.section_head("Anneau de score", "Trois tailles, trois niveaux, un état vide, deux fonds."))
st.html('<div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap">'
        + ui.score_ring(88, "lg") + ui.score_ring(62, "md") + ui.score_ring(31, "sm") + ui.score_ring(None, "md")
        + '<div style="background:#14171A;padding:24px;border-radius:20px;display:flex;gap:24px">'
        + ui.score_ring(88, "lg", "dark") + ui.score_ring(62, "md", "dark") + ui.score_ring(31, "sm", "dark") + "</div></div>")

st.html(ui.section_head("Cartes KPI", "Une seule carte « signal » par rangée."))
st.html(ui.stat_row([
    ui.stat_card("Dossiers reçus", 50, "Dans le pipeline", "inbox", index=0),
    ui.stat_card("Scorés", 48, "Analyses disponibles", "chart", tone="signal", index=1),
    ui.stat_card("Intégrité du contenu", 5, "Alertes informatives", "shield", index=2),
    ui.stat_card("Shortlist", 0, "Dossiers conservés", "shortlist", index=3),
]))

st.html(ui.section_head("Cartes de dossier", "Normale, signalée, sans score, texte très long, contenu hostile."))
cases = [
    dict(status="Analysé", status_tone="high", name="Keyhold", idea="Un service géré de cybersécurité pour les PME sans équipe dédiée.",
         sector="cybersecurity", pitch_id="P017", score=78, verdict="Priorité élevée"),
    dict(status="Intégrité : alerte", status_tone="warning", name="Remorq", idea="Regroupe les expéditions de plusieurs entreprises dans un même camion.",
         sector="logistics", pitch_id="P006", score=54, verdict="À approfondir"),
    dict(status="À scorer", status_tone="neutral", name="Nouvelle entrée", idea="L’idée de cette startup n’est pas encore résumée en une phrase.",
         sector="—", pitch_id="SUB-0007", score=None, verdict="En attente d’analyse"),
    dict(status="Analysé", status_tone="low", name=LONG, idea=LONG * 3, sector="logistics et transformation", pitch_id="I" + "A1B2C3D4" * 3,
         score=22, verdict="Non prioritaire"),
    dict(status="Analysé", status_tone="mid", name=PIEGE, idea=PIEGE, sector=PIEGE, pitch_id=PIEGE, score=60, verdict=PIEGE),
]
with st.container(key="grid_showcase"):
    for start in range(0, len(cases), 3):
        cols = st.columns(3)
        for col, case in zip(cols, cases[start:start + 3]):
            with col, st.container(key=f"card_showcase_{start}_{cases.index(case)}"):
                st.html(ui.dossier_card(**case))
                st.button("Ouvrir la fiche", key=f"open_showcase_{cases.index(case)}", width="stretch")
                st.button("Ajouter à la shortlist", key=f"save_showcase_{cases.index(case)}", type="tertiary", width="stretch",
                          icon=":material/bookmark_add:")

st.html(ui.section_head("Dossier en tête et fiche"))
a, b = st.columns([1, 1.6], gap="medium")
with a, st.container(key="featured_company"):
    st.html(ui.featured("En tête du classement", "Keyhold", "Un service géré de cybersécurité pour les PME sans équipe dédiée.", "cybersecurity", 78))
    st.button("Découvrir le dossier", key="featured_open", width="stretch", type="primary", icon=":material/arrow_outward:")
with b:
    st.html(ui.profile_header("Keyhold", "Un service géré de cybersécurité pour les PME sans équipe dédiée.",
                              ["cybersecurity", "Corpus", "2026-09-24"], 78, "Analysé", "high"))

st.html(ui.section_head("Barres et histogramme"))
c1, c2 = st.columns(2, gap="medium")
with c1, st.container(key="panel_bars"):
    st.html("".join(ui.bar_row(label, v, 5, " / 5", i) for i, (label, v) in enumerate(
        [("Équipe", 4), ("Marché", 5), ("Produit", 3), ("Traction", 1), ("Modèle économique", 0)])))
with c2, st.container(key="panel_dist"):
    st.html(ui.distribution([("0–19", 2), ("20–39", 4), ("40–59", 21), ("60–79", 23), ("80–100", 0)]))

st.html(ui.section_head("États vides"))
st.html(ui.empty_state("Le pipeline attend ses premières analyses", "Dépose un pitch ou lance le passage du moteur pour alimenter la file."))
st.html(ui.section_head("Histogramme sans donnée"))
st.html(ui.distribution([("0–19", 0), ("20–39", 0), ("40–59", 0), ("60–79", 0), ("80–100", 0)]))

st.html(ui.section_head("Boutons, champs et messages", "Survol, appui, focus au clavier (Tab) et désactivé."))
b1, b2, b3, b4 = st.columns(4)
b1.button("Principal", type="primary", key="b_primary", width="stretch")
b2.button("Secondaire", key="b_secondary", width="stretch")
b3.button("Tertiaire", type="tertiary", key="b_tertiary", width="stretch")
b4.button("Désactivé", disabled=True, key="b_disabled", width="stretch")
with st.container(key="filters"):
    l, r = st.columns([2, 1])
    l.text_input("Champ texte", placeholder="Entreprise, identifiant, secteur…")
    r.selectbox("Liste déroulante", ["Tous les secteurs", "cybersecurity", "logistics"])
    st.radio("Contrôle segmenté", ["Tous", "Top sélection", "Classement complet"], horizontal=True)
st.info("Information : les nouveaux dépôts sont analysés par le moteur local.")
st.warning("Avertissement : une instruction de manipulation a été détectée.")
st.success("Confirmation : dossier enregistré et scoré.")
st.error("Erreur : les dossiers sont indisponibles.")
