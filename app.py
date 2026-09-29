"""Unicornext — Streamlit investor workspace. Run: streamlit run app.py."""
from __future__ import annotations

import base64
from collections import Counter
from pathlib import Path
import uuid

import streamlit as st
import streamlit.components.v1 as components

from src import ui
from src.extract import extract_submission
from src.intake import (INTAKE_RUNS, SUBMISSIONS, append_jsonl, load_dossiers,
                        load_shortlist, save_shortlist, new_submission, queue)
from src.score_pitch import append_run, score_pitch
from src.ui_copy import COPY
from src.startup_ideas import startup_idea

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(page_title="Unicornext · V1", page_icon="✦", layout="wide")
st.html(ASSETS / "unicornext.css")
st.html(f"<style>{ui.icons_css()}\n{ui.nav_icon_css()}</style>")
components.html(ui.sonar_html((ASSETS / "sonar.js").read_text(encoding="utf-8")), height=0)
LOGO = base64.b64encode((ASSETS / "unicornext-logo.png").read_bytes()).decode()
st.sidebar.html(f'<img class="brand-logo" src="data:image/png;base64,{LOGO}" alt="Unicornext">')

# La langue se choisit en bas de la barre latérale : on la lit d'abord dans l'état, le sélecteur vient après.
language = st.session_state.get("language", "fr")
t = dict(COPY[language])
def tr(fr, en):
    return fr if language == "fr" else en


t.update({
    "review_count": tr("Intégrité du contenu", "Content integrity"),
    "review": tr("Tentatives de manipulation", "Manipulation attempts"),
    "guard": tr("Une instruction de manipulation a été détectée. Elle ne constitue pas une preuve et a été ignorée dans l’évaluation. Ce dossier participe au classement sur la base de son contenu économique.", "A manipulation instruction was detected. It is not evidence and was ignored in the assessment. This pitch is ranked on its business content."),
    "review_rec": tr("À approfondir", "Explore further"), "reject": tr("Non prioritaire", "Low priority"),
    "shortlist": tr("Priorité élevée", "High priority"), "ranked": tr("Analysé", "Assessed"),
    "flagged": tr("Intégrité : alerte", "Integrity alert"), "priority": tr("Top sélection", "Top picks"),
    "recommendation": tr("Synthèse IA", "AI assessment"),
    "ranking": tr("Classement complet", "Full ranking"),
    "disclaimer": tr("Scores IA fondés sur les informations déclarées dans les pitchs. Ils mesurent la solidité du dossier, pas une probabilité de succès.", "AI scores based on claims in each pitch. They assess the pitch, not the probability of success."),
})

pages = {"dashboard": tr("Vue d’ensemble", "Overview"), "search": tr("Explorer les startups", "Explore startups"),
         "detail": tr("Fiche startup", "Startup profile"), "shortlist": "Shortlist", "submit": t["submit"]}
page = st.sidebar.radio(tr("Espace investisseur", "Investor workspace"), list(pages), format_func=pages.get, key="page")
st.sidebar.divider()
st.sidebar.selectbox("Language / Langue", ["fr", "en"], format_func=lambda x: "Français" if x == "fr" else "English", key="language")
st.sidebar.caption(tr("V1 · Évaluations IA · corpus de démonstration", "V1 · AI assessments · demo corpus"))
st.sidebar.caption(t["disclaimer"])
st.sidebar.caption(tr("Espace local · shortlist partagée sur cet ordinateur", "Local workspace · shortlist shared on this computer"))


def empty(title, description, icon_name="inbox"):
    st.html(ui.empty_state(title, description, icon_name))


def go(pid):
    st.session_state["active_pitch"] = pid
    st.session_state["page"] = "detail"


def toggle(pid):
    try:
        saved = load_shortlist()
        if pid in saved:
            saved.remove(pid)
            notice = tr("Dossier retiré de la shortlist", "Removed from shortlist")
        else:
            saved.append(pid)
            notice = tr("Dossier ajouté à la shortlist", "Added to shortlist")
        save_shortlist(saved)
        st.session_state["toast"] = notice
    except (OSError, ValueError):
        st.session_state["save_error"] = tr("Impossible de sauvegarder la shortlist. Réessaie.", "Could not save the shortlist. Please retry.")


def recommendation_label(value):
    return t[{"reject": "reject", "review": "review_rec", "shortlist": "shortlist"}[value]] if value else "—"


def status_of(d):
    """Le libellé et la teinte du tag d'état d'un dossier."""
    if d.flagged:
        return t["flagged"], "warning"
    if d.score is None:
        return t["waiting"], "neutral"
    return t["ranked"], ui.tier(d.score)


def ring_label():
    return t["score"].split(" /")[0]


def save_button(d, key, kind="tertiary", width="stretch"):
    saved = d.pitch_id in saved_ids
    st.button(tr("Retirer", "Remove") if saved else tr("Ajouter à la shortlist", "Save to shortlist"),
              key=f"save_{key}", on_click=toggle, args=(d.pitch_id,), width=width, type=kind,
              icon=":material/bookmark_remove:" if saved else ":material/bookmark_add:",
              disabled=shortlist_error,
              help=t["guard"] if d.flagged else None)


def cards(items, prefix):
    with st.container(key=f"grid_{prefix}"):
        for start in range(0, len(items), 3):
            cols = st.columns(3)
            for col, d in zip(cols, items[start:start + 3]):
                with col, st.container(key=f"card_{prefix}_{d.pitch_id}"):
                    status, tone = status_of(d)
                    st.html(ui.dossier_card(
                        status=status, status_tone=tone, name=d.company_name, idea=startup_idea(d),
                        sector=d.sector, pitch_id=d.pitch_id, score=d.score, ring_label=ring_label(),
                        verdict=recommendation_label(d.recommendation) if d.recommendation else tr("En attente d’analyse", "Awaiting analysis")))
                    st.button(tr("Ouvrir la fiche", "Open profile"), key=f"open_{prefix}_{d.pitch_id}", on_click=go, args=(d.pitch_id,), width="stretch", help=d.company_name)
                    save_button(d, f"{prefix}_{d.pitch_id}")


def bar(label, value, maximum, suffix="", index=0):
    st.html(ui.bar_row(label, value, maximum, suffix, index))


def bullets(title, values, key):
    with st.container(key=f"panel_{key}"):
        st.html(ui.section_head(title))
        if values:
            for value in values:
                st.write("• " + value)
        else:
            st.caption(tr("Non renseigné dans cette analyse.", "Not provided in this analysis."))


try:
    with st.spinner(tr("Chargement des dossiers…", "Loading pitches…")):
        dossiers = load_dossiers()
except (OSError, ValueError):
    st.error(tr("Les dossiers sont indisponibles. Vérifie les fichiers de données et réessaie.", "Pitches are unavailable. Check the data files and retry."))
    if st.button(tr("Réessayer", "Retry")):
        st.rerun()
    st.stop()
shortlist_error = False
try:
    saved_ids = load_shortlist()
except (OSError, ValueError):
    saved_ids = []
    shortlist_error = True
    st.error(tr("Shortlist illisible. Le fichier local doit être restauré avant toute modification.", "Shortlist cannot be read. Restore the local file before editing."))
if "toast" in st.session_state:
    st.toast(st.session_state.pop("toast"))
if "save_error" in st.session_state:
    st.error(st.session_state.pop("save_error"))
if "intake_notice" in st.session_state:
    kind, message = st.session_state.pop("intake_notice")
    (st.success if kind == "success" else st.warning)(message)
groups = queue(dossiers)
criteria = {"team": tr("Équipe", "Team"), "market": tr("Marché", "Market"), "product": tr("Produit", "Product"), "traction": "Traction", "business_model": tr("Modèle économique", "Business model")}
subtitles = {
    "dashboard": tr("Une vue claire de votre pipeline. Les bons dossiers, au bon moment.", "A clear view of your pipeline. The right companies, at the right time."),
    "search": tr("Explorez le pipeline et approfondissez les signaux qui comptent.", "Explore the pipeline and investigate the signals that matter."),
    "detail": tr("Des signaux aux preuves : toutes les dimensions du dossier.", "From signals to evidence: every dimension of the pitch."),
    "shortlist": tr("Vos dossiers à suivre, réunis pour une décision éclairée.", "Your saved companies, together for an informed decision."),
    "submit": tr("Le prochain potentiel commence par un pitch.", "The next opportunity starts with a pitch."),
}
with st.container(key=f"page_{page}"):
    if page == "dashboard":
        st.html(ui.page_header("UNICORNEXT / DEAL INTELLIGENCE",
                               ui.hero_title(tr("Repérez le potentiel.", "Spot the potential."), tr("Gardez une longueur d’avance.", "Stay one step ahead.")),
                               subtitles[page], hero=True))
    else:
        st.html(ui.page_header("UNICORNEXT", pages[page], subtitles[page]))

    if page == "dashboard":
        scored_count = sum(d.score is not None for d in dossiers)
        st.html(ui.stat_row([
            ui.stat_card(t["received"], len(dossiers), tr("Dans le pipeline", "In the pipeline"), "inbox", index=0),
            ui.stat_card(t["scored"], scored_count, tr("Analyses disponibles", "Available analyses"), "chart", tone="signal", index=1),
            ui.stat_card(t["review_count"], len(groups["review"]), tr("Alertes informatives", "Informational alerts"), "shield", index=2),
            ui.stat_card("Shortlist", sum(d.pitch_id in saved_ids for d in dossiers), tr("Dossiers conservés", "Saved companies"), "shortlist", index=3),
        ]))
        st.caption(tr("Entreprises fictives · Évaluations directes de Codex · Justifications et réserves dans chaque fiche.", "Fictional companies · Direct Codex assessments · Evidence and caveats in each profile."))
        report = Path(__file__).parent / "docs/UNICORNEXT_V1_SCORES.md"
        if report.exists():
            st.download_button(tr("Télécharger les 50 analyses", "Download all 50 assessments"), report.read_text(), file_name="unicornext-v1-analyses.md", mime="text/markdown", icon=":material/download:")
        st.write("")
        chart, featured = st.columns([1.65, 1], gap="medium")
        with chart, st.container(key="panel_distribution"):
            st.html(ui.section_head(tr("Le pipeline, en perspective", "Your pipeline, in perspective"),
                                    tr("Nombre de dossiers par tranche de score · sur 100", "Pitches by score range · out of 100")))
            buckets = [("0–19", 0, 20), ("20–39", 20, 40), ("40–59", 40, 60), ("60–79", 60, 80), ("80–100", 80, 101)]
            counts = [sum(d.score is not None and low <= d.score < high for d in dossiers) for _, low, high in buckets]
            st.html(ui.distribution([(label, n) for (label, _, _), n in zip(buckets, counts)]))
            if not any(counts):
                st.caption(t["no_score"])
        with featured, st.container(key="featured_company"):
            if groups["ranked"]:
                leader = groups["ranked"][0]
                st.html(ui.featured(tr("En tête du classement", "Leading the ranking"), leader.company_name, startup_idea(leader), leader.sector, leader.score, ring_label()))
                st.button(tr("Découvrir le dossier", "Explore the profile"), key="featured_open", on_click=go, args=(leader.pitch_id,), width="stretch", type="primary", icon=":material/arrow_outward:")
            else:
                st.html(ui.featured(tr("Prochain dossier", "Next opportunity"), tr("Votre prochain dossier", "Your next opportunity"), t["no_score"], "—", None, ring_label()))
                st.button(t["submit"], on_click=lambda: st.session_state.update(page="submit"), width="stretch", type="primary")
        st.html(ui.section_head(tr("À regarder de plus près", "Worth a closer look"),
                                tr("Les 5 meilleurs dossiers scorés : score pondéré, puis traction et marché en cas d’égalité.", "Top 5 scored pitches: weighted score, then traction and market to break ties.")))
        if groups["selected"]:
            cards(groups["selected"], "priority")
        else:
            empty(tr("Le pipeline attend ses premières analyses", "Your pipeline awaits its first analyses"), t["empty_scored"])
        st.write("")
        left, right = st.columns([1.2, 1], gap="medium")
        with left, st.container(key="panel_sectors"):
            st.html(ui.section_head(tr("Répartition par secteur", "Sector distribution")))
            sectors = Counter(d.sector for d in dossiers)
            st.html("".join(ui.bar_row(label, count, max(sectors.values()), index=i) for i, (label, count) in enumerate(sectors.most_common(6))))
            if len(sectors) > 6:
                st.caption(tr("Les 6 secteurs les plus représentés · tous les secteurs dans l’explorateur.", "Top 6 sectors · explore all sectors in Explore."))
            if not sectors:
                st.caption(tr("Aucun dossier reçu.", "No pitches received."))
        with right, st.container(key="panel_triage"):
            st.html(ui.section_head(tr("Progression du tri", "Triage progress")))
            st.html("".join(ui.bar_row(label, len(groups[group]), len(dossiers), index=i)
                            for i, (label, group) in enumerate([(t["ranking"], "ranked"), (t["pending"], "pending"), (t["review"], "review")])))
            st.caption(tr("Les alertes sont incluses dans les dossiers scorés ou en attente ; elles ne forment pas une catégorie supplémentaire.", "Alerts overlap with scored or pending pitches; they are not an additional category."))
            if groups["pending"]:
                st.caption(t["partial"])
            st.button(tr("Explorer les dossiers", "Explore pitches"), on_click=lambda: st.session_state.update(page="search"), type="primary")

    elif page == "search":
        with st.container(key="filters"):
            left, right = st.columns([2, 1])
            search = left.text_input(t["search"], placeholder=tr("Entreprise, identifiant, secteur…", "Company, ID, sector…"))
            sector = right.selectbox(t["sector"], [t["all"], *sorted({d.sector for d in dossiers})])
            mode = st.radio(t["status"], ["all", "selected", "ranked", "review", "pending"], horizontal=True,
                            format_func=lambda k: {"all": tr("Tous", "All"), "selected": t["priority"], "ranked": t["ranking"], "review": t["review"], "pending": t["pending"]}[k])
        filtered = queue(dossiers, None if sector == t["all"] else sector, search)
        visible = filtered["ranked"] + filtered["pending"] if mode == "all" else filtered[mode]
        st.caption(tr(f"{len(visible)} dossiers affichables sur {len(dossiers)} au total", f"{len(visible)} matching pitches out of {len(dossiers)} total"))
        st.caption(tr("Tous les dossiers scorés participent au classement. Les alertes de manipulation sont informatives et peuvent concerner des dossiers déjà classés.", "All scored pitches are ranked. Manipulation alerts are informational and may apply to pitches already in the ranking."))
        view = st.radio(tr("Affichage", "View"), ["cards", "table"], horizontal=True, format_func=lambda x: tr("Cartes", "Cards") if x == "cards" else tr("Tableau", "Table"))
        if not visible:
            empty(tr("Aucun dossier dans cette vue", "No pitches in this view"), tr("Modifie les filtres ou dépose un nouveau pitch.", "Adjust the filters or submit a new pitch."), "search")
        elif view == "table":
            st.dataframe([{"ID":d.pitch_id,t["company"]:d.company_name,t["sector"]:d.sector,t["score"]:d.score,t["recommendation"]:recommendation_label(d.recommendation),t["channel"]:t.get(d.channel,d.channel),t["status"]:t["flagged"] if d.flagged else t["waiting"] if d.score is None else t["ranked"]} for d in visible], hide_index=True, width="stretch")
            choice = st.selectbox(t["choose"], visible, format_func=lambda d: f"{d.company_name} · {d.pitch_id}")
            st.button(tr("Ouvrir la fiche", "Open profile"), on_click=go, args=(choice.pitch_id,), type="primary")
        else:
            size = st.selectbox(tr("Dossiers par page", "Pitches per page"), [12, 24, "all"], index=2,
                                format_func=lambda value: tr("Tous", "All") if value == "all" else str(value), key="page_size")
            count = len(visible) if size == "all" else size
            total_pages = (len(visible) + count - 1) // count
            current = st.selectbox("Page", range(1, total_pages + 1)) if total_pages > 1 else 1
            st.caption(tr(f"Dossiers {(current-1)*count+1} à {min(current*count,len(visible))} sur {len(visible)}", f"Pitches {(current-1)*count+1}–{min(current*count,len(visible))} of {len(visible)}"))
            cards(visible[(current-1)*count:current*count], "search")

    elif page == "detail":
        if not dossiers:
            empty(tr("Aucune fiche disponible", "No profiles yet"), t["manual_intro"])
        else:
            lookup = {d.pitch_id:d for d in dossiers}
            if st.session_state.get("active_pitch") not in lookup:
                st.session_state["active_pitch"] = dossiers[0].pitch_id
            pid = st.selectbox(t["choose"], list(lookup), format_func=lambda x: f"{lookup[x].company_name} · {x}", key="active_pitch")
            ids = list(lookup)
            position = ids.index(pid)
            st.caption(tr(f"Fiche {position+1} sur {len(ids)} · Tous les dossiers sont inclus", f"Profile {position+1} of {len(ids)} · All pitches are included"))
            previous_col, next_col = st.columns(2)
            previous_col.button(tr("← Fiche précédente", "← Previous profile"), key="previous_profile", disabled=position == 0,
                                on_click=go, args=(ids[max(0, position-1)],), width="stretch")
            next_col.button(tr("Fiche suivante →", "Next profile →"), key="next_profile", disabled=position == len(ids)-1,
                            on_click=go, args=(ids[min(len(ids)-1, position+1)],), width="stretch")
            d = lookup[pid]
            status, tone = status_of(d)
            st.html(ui.profile_header(d.company_name, startup_idea(d), [d.sector, t.get(d.channel, d.channel), d.submitted_at],
                                      d.score, status, tone, ring_label()))
            st.caption(tr("Source de la note : ", "Assessment source: ") + (d.assessment_source or "—"))
            save_button(d, "detail", kind="secondary", width="content")
            if d.flagged:
                st.warning(t["guard"])
                st.write(d.guard_reason)
                for excerpt in d.guard_excerpts:
                    st.code(excerpt, language=None, wrap_lines=True)
            if d.error:
                st.error(f'{t["error"]} {d.error}')
            if d.score is None:
                empty(tr("Analyse à venir", "Analysis pending"), t["no_score"], "chart")
            else:
                previous = st.session_state.get("last_scores", {})
                changed = pid in previous and previous[pid] != d.score
                with st.container(key="score_changed" if changed else "score_current"):
                    st.metric(t["recommendation"], recommendation_label(d.recommendation))
                st.session_state["last_scores"] = {**previous, pid:d.score}
                with st.container(key="panel_criteria"):
                    st.html(ui.section_head(t["criteria"],
                                            tr("Équipe 20 % · Marché 25 % · Produit 15 % · Traction 25 % · Modèle 15 %. Échelle : 0 absent, 1 non étayé, 2 faible, 3 crédible, 4 solide, 5 exceptionnel.", "Team 20% · Market 25% · Product 15% · Traction 25% · Business model 15%. Scale: 0 absent, 1 unsupported, 2 weak, 3 credible, 4 strong, 5 exceptional.")))
                    for i, (key, label) in enumerate(criteria.items()):
                        bar(label, d.scores[key], 5, " / 5", i)
                        if d.criterion_reasons.get(key):
                            st.caption(d.criterion_reasons[key])
                st.write("")
                a,b = st.columns(2, gap="medium")
                with a:
                    bullets(t["strengths"], d.strengths, "strengths")
                    bullets(t["missing"], d.missing_information, "missing")
                with b:
                    bullets(t["risks"], d.risks, "risks")
                    bullets(t["evidence"], d.evidence, "evidence")
                st.caption(t["source_language"])
            with st.expander(t["text"], expanded=d.score is None):
                st.text(d.text)

    elif page == "shortlist":
        saved = [d for d in dossiers if d.pitch_id in saved_ids]
        if not saved:
            empty(tr("Votre prochaine conviction commence ici", "Your next conviction starts here"), tr("Ajoute des startups depuis l’explorateur ou leur fiche pour les retrouver et les comparer.", "Save startups from Explore or their profile to revisit and compare them."), "shortlist")
            st.button(tr("Explorer les startups", "Explore startups"), on_click=lambda: st.session_state.update(page="search"), type="primary")
        else:
            st.html(ui.section_head(tr("Comparer les dossiers", "Compare companies")))
            chosen = st.multiselect(tr("Choisir jusqu’à 3 startups", "Choose up to 3 startups"), [d.pitch_id for d in saved], format_func=lambda pid: next(d.company_name for d in saved if d.pitch_id == pid), max_selections=3)
            if chosen:
                with st.container(key="page_comparison"):
                    cols = st.columns(len(chosen), gap="medium")
                    for col,pid in zip(cols,chosen):
                        d = next(d for d in saved if d.pitch_id == pid)
                        with col, st.container(key=f"panel_compare_{pid}"):
                            st.subheader(d.company_name)
                            st.write(startup_idea(d))
                            st.metric(t["score"], f"{d.score:.0f}" if d.score is not None else "—")
                            if d.flagged:
                                st.warning(t["guard"])
                            if d.score is None:
                                st.caption(t["no_score"])
                            else:
                                for i, (key, label) in enumerate(criteria.items()):
                                    bar(label, d.scores[key], 5, " / 5", i)
                                st.caption(recommendation_label(d.recommendation))
            st.html(ui.section_head(tr("Dossiers conservés", "Saved companies")))
            cards(saved,"shortlist")

    elif page == "submit":
        st.write(t["manual_intro"])
        st.info(tr("Les 50 dossiers de démonstration ont été évalués directement par Codex. Les nouveaux dépôts sont analysés automatiquement par le moteur local qwen2.5:14b ; la source de chaque note est affichée dans la fiche.", "The 50 demo pitches were assessed directly by Codex. New submissions are assessed automatically by the local qwen2.5:14b engine; each profile identifies its assessment source."))
        with st.form("manual_intake", clear_on_submit=False):
            company_name = st.text_input(t["name"])
            sector_name = st.text_input(t["sector_input"])
            message = st.text_area(t["message"], height=180)
            files = st.file_uploader(t["files"], type=["pdf"], accept_multiple_files=True)
            links_text = st.text_area(t["links"], height=80)
            submitted = st.form_submit_button(t["evaluate"], type="primary")
        if submitted:
            event = {
                "text": message,
                "attachments": [{"type": "pdf", "name": f.name, "content": f.getvalue()} for f in files],
                "links": [line.strip() for line in links_text.splitlines() if line.strip()],
            }
            try:
                with st.spinner(t["processing"]):
                    extraction = extract_submission(event)
                    st.markdown(f"#### {t['source_report']}")
                    st.dataframe([vars(source) for source in extraction.sources], hide_index=True, width="stretch")
                    for warning in extraction.warnings:
                        st.warning(warning)
                    if not extraction.ok:
                        st.error(t["too_short"])
                    else:
                        pitch_id = "I" + uuid.uuid4().hex[:8].upper()
                        submission = new_submission(pitch_id, extraction.text, company_name, sector_name, [vars(source) for source in extraction.sources])
                        append_jsonl(SUBMISSIONS, submission)
                        record = score_pitch(submission, "local", "V2", output_language=language, trace=False)
                        append_run(record, INTAKE_RUNS)
                        st.session_state["intake_notice"] = ("success" if record.parsed_output else "warning", t["saved"] if record.parsed_output else t["scoring_failed"])
                        st.rerun()
            except (OSError, ValueError, RuntimeError) as exc:
                st.error(tr("Le traitement n’a pas pu aboutir. Ton formulaire est conservé. Vérifie les sources et le stockage local avant de réessayer.", "Processing could not finish. Your form is preserved. Check sources and local storage before retrying."))
