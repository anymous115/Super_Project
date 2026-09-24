"""Tableau de bord vivant de l'avancement du projet.

Lancer avec : streamlit run dashboard.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from src.project_status import PhaseProgress, ProjectSnapshot, collect_project_status


ROOT = Path(__file__).resolve().parent
STATE_ICON = {"Terminée": "✅", "Terminé": "✅", "En cours": "🟠", "À faire": "⚪"}


st.set_page_config(
    page_title="Pilotage · Unicornext",
    page_icon="📊",
    layout="wide",
)


def percent(value: float) -> str:
    return f"{round(value * 100)} %"


def phase_card(phase: PhaseProgress) -> None:
    st.markdown(f"#### {STATE_ICON[phase.state]} {phase.number}. {phase.name}")
    st.progress(phase.progress, text=percent(phase.progress))
    done = sum(task.progress >= 1 for task in phase.tasks)
    st.caption(f"{done}/{len(phase.tasks)} jalons terminés")


def task_table(phase: PhaseProgress) -> None:
    rows = [
        {
            "État": f"{STATE_ICON[task.state]} {task.state}",
            "Jalon": task.label,
            "Avancement": percent(task.progress),
            "Preuve": task.evidence,
            "Prochaine action": "—" if task.progress >= 1 else task.next_action,
        }
        for task in phase.tasks
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def render_header(snapshot: ProjectSnapshot) -> None:
    left, right = st.columns([4, 1])
    with left:
        st.title("Pilotage du projet")
        st.caption(
            "Unicornext · état calculé depuis les fichiers du dépôt "
            f"· branche `{snapshot.branch}` · commit `{snapshot.commit}`"
        )
    with right:
        if st.button("↻ Actualiser", width="stretch"):
            st.rerun()
    st.caption("Suivi interne de la réalisation du projet. L’interface destinée aux investisseurs est accessible ci-dessous.")
    st.link_button(
        "Ouvrir Unicornext — application investisseur",
        os.environ.get("UNICORNEXT_APP_URL", "http://127.0.0.1:8502"),
        type="primary",
    )


def render_overview(snapshot: ProjectSnapshot) -> None:
    current = snapshot.current_phase
    incomplete = sum(task.progress < 1 for phase in snapshot.phases for task in phase.tasks)
    cols = st.columns(4)
    cols[0].metric("Avancement global", percent(snapshot.progress))
    cols[1].metric("Phase active", f"{current.number}. {current.name}" if current else "Terminé")
    cols[2].metric("Jalons restants", incomplete)
    cols[3].metric("Pitchs scorés", f"{snapshot.metrics['scored_pitches']} / 50")
    st.progress(snapshot.progress)

    if snapshot.metrics["v1_mode"]:
        st.info("V1 : validation humaine obligatoire supprimée. Les notes directes IA alimentent l’application ; les appels du benchmark restent mesurés séparément.")
    st.subheader("Pipeline du projet")
    phase_columns = st.columns(3)
    for index, phase in enumerate(snapshot.phases):
        with phase_columns[index % 3]:
            phase_card(phase)

    st.subheader("À faire maintenant")
    actions = snapshot.next_actions[:6]
    if not actions:
        st.success("Tous les jalons suivis sont terminés.")
    for index, action in enumerate(actions, start=1):
        st.markdown(
            f"**{index}. Phase {action['phase']} · {action['task']}**  \n"
            f"{action['action']} — *{percent(action['progress'])}*"
        )


def render_data(snapshot: ProjectSnapshot) -> None:
    metrics = snapshot.metrics
    cols = st.columns(3)
    cols[0].metric("Pitchs rédigés", f"{metrics['drafted_pitches']} / 50")
    cols[1].metric("Évaluations IA V1", f"{metrics['direct_assessments']} / 50")
    cols[2].metric("PDF", f"{metrics['pdfs']} / 50")
    task_table(snapshot.phases[1])
    st.info(
        "Les scores de calibration guident la rédaction et servent de repère de cohérence "
        "au moteur. Ce sont des intentions d'écriture, pas une vérité."
    )


def render_pipeline(snapshot: ProjectSnapshot) -> None:
    cols = st.columns(4)
    cols[0].metric("Tests écrits", snapshot.metrics["tests"])
    cols[1].metric("Appels enregistrés", snapshot.metrics["engine_runs"])
    cols[2].metric("JSON valides", snapshot.metrics["valid_runs"])
    cols[3].metric("Injections contenues", snapshot.metrics["traps_contained"])
    st.subheader("Filtre anti-injection · corpus courant")
    guard_cols = st.columns(2)
    guard_cols[0].metric(
        "Pièges détectés",
        f"{snapshot.metrics['guard_caught']} / {snapshot.metrics['guard_traps']}",
    )
    guard_cols[1].metric("Faux positifs", snapshot.metrics["guard_false_positives"])
    st.caption("Mesure directe de src/guard.py sur les pitchs du dépôt. Les injections contenues par le moteur sont comptées séparément après scoring V2.")
    st.subheader("Phase 3 · Pipeline")
    task_table(snapshot.phases[2])
    st.subheader("Phase 4 · Moteur")
    task_table(snapshot.phases[3])


def render_deliverables(snapshot: ProjectSnapshot) -> None:
    st.subheader("Phase 5 · Produit")
    st.metric(
        "PDF extraits fidèlement",
        f"{snapshot.metrics['pdf_fidelity_passed']} / {snapshot.metrics['pdf_checked']}",
    )
    st.caption("Comparaison des mots extraits avec pitch_text, dans le même ordre ; seuil de fidélité : 98 %.")
    task_table(snapshot.phases[4])
    st.subheader("Phase 6 · Livraison")
    task_table(snapshot.phases[5])


def render_activity(snapshot: ProjectSnapshot) -> None:
    st.subheader("Derniers changements Git")
    if snapshot.recent_commits:
        st.dataframe(snapshot.recent_commits, width="stretch", hide_index=True)
    else:
        st.info("Historique Git indisponible.")
    st.download_button(
        "Télécharger l’état en JSON",
        data=json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2),
        file_name="project-status.json",
        mime="application/json",
    )


snapshot = collect_project_status(ROOT)
render_header(snapshot)

overview, data_tab, pipeline_tab, delivery_tab, activity_tab = st.tabs(
    ["Vue d’ensemble", "Données", "Pipeline & moteur", "Produit & livraison", "Activité Git"]
)
with overview:
    render_overview(snapshot)
with data_tab:
    render_data(snapshot)
with pipeline_tab:
    render_pipeline(snapshot)
with delivery_tab:
    render_deliverables(snapshot)
with activity_tab:
    render_activity(snapshot)

st.caption(f"Calculé automatiquement le {snapshot.generated_at}. Recharge la page après chaque pull ou commit.")
