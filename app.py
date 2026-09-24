"""Unicornext — Streamlit investor workspace. Run: streamlit run app.py."""
from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path
import uuid

import streamlit as st

from src.extract import extract_submission
from src.intake import (INTAKE_RUNS, SUBMISSIONS, append_jsonl, load_dossiers,
                        load_shortlist, save_shortlist, new_submission, queue)
from src.score_pitch import append_run, score_pitch
from src.ui_copy import COPY
from src.startup_ideas import startup_idea

st.set_page_config(page_title="Unicornext · V1", page_icon="✦", layout="wide")
st.html(Path(__file__).parent / "assets/unicornext.css")
st.sidebar.html('<div class="brand"><span class="brand-mark" aria-hidden="true">u↗</span>unicornext</div>')
language = st.sidebar.selectbox("Language / Langue", ["fr", "en"], format_func=lambda x: "Français" if x == "fr" else "English", key="language")
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
st.sidebar.caption(tr("V1 · Évaluations IA · corpus de démonstration", "V1 · AI assessments · demo corpus"))
st.sidebar.caption(t["disclaimer"])
st.sidebar.caption(tr("Espace local · shortlist partagée sur cet ordinateur", "Local workspace · shortlist shared on this computer"))


def empty(title, description):
    st.html(f'<div class="empty" role="status"><strong>{escape(title)}</strong><p>{escape(description)}</p></div>')


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


def save_button(d, key):
    saved = d.pitch_id in saved_ids
    st.button(tr("Retirer", "Remove") if saved else tr("Ajouter à la shortlist", "Save to shortlist"),
              key=f"save_{key}", on_click=toggle, args=(d.pitch_id,), width="stretch",
              disabled=shortlist_error,
              help=t["guard"] if d.flagged else None)


def cards(items, prefix):
    for start in range(0, len(items), 3):
        cols = st.columns(3)
        for col, d in zip(cols, items[start:start + 3]):
            with col, st.container(key=f"card_{prefix}_{d.pitch_id}"):
                status = t["flagged"] if d.flagged else t["ranked"] if d.score is not None else t["waiting"]
                tone = "warning" if d.flagged else "pending" if d.score is None else ""
                score = f"{d.score:.0f}" if d.score is not None else "—"
                st.html(f'<div class="card-head"><span class="monogram" aria-hidden="true">{escape(d.company_name[:2].upper())}</span><span class="tag {tone}">{escape(status)}</span></div><div class="company">{escape(d.company_name)}</div><p class="card-description">{escape(startup_idea(d))}</p><div class="meta">{escape(d.sector)} · {escape(d.pitch_id)}</div><div class="card-score">{score} <small>/ 100 · {escape(t["score"].split(" /")[0])}</small></div>')
                st.caption(recommendation_label(d.recommendation))
                st.button(tr("Ouvrir la fiche", "Open profile"), key=f"open_{prefix}_{d.pitch_id}", on_click=go, args=(d.pitch_id,), width="stretch", help=d.company_name)
                save_button(d, f"{prefix}_{d.pitch_id}")


def bar(label, value, maximum, suffix=""):
    percent = max(0, min(100, value / maximum * 100)) if maximum else 0
    st.html(f'<div class="bar-row"><div class="bar-label"><span>{escape(label)}</span><strong>{value:g}{escape(suffix)}</strong></div><div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:{percent}%"></div></div></div>')


def bullets(title, values):
    with st.container(border=True):
        st.subheader(title)
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
    st.html('<div class="eyebrow">UNICORNEXT / DEAL INTELLIGENCE</div>')
    if page == "dashboard":
        st.html('<h1 class="hero-title">' + tr("Repérez le potentiel.<br>Gardez une <span>longueur d’avance.</span>", "Spot the potential.<br>Stay <span>one step ahead.</span>") + "</h1>")
    else:
        st.title(pages[page])
    st.html(f'<p class="hero-sub">{escape(subtitles[page])}</p>')

if page == "dashboard":
    stats = [(t["received"], len(dossiers), tr("Dans le pipeline", "In the pipeline")),
             (t["scored"], sum(d.score is not None for d in dossiers), tr("Analyses disponibles", "Available analyses")),
             (t["review_count"], len(groups["review"]), tr("Alertes informatives", "Informational alerts")),
             ("Shortlist", sum(d.pitch_id in saved_ids for d in dossiers), tr("Dossiers conservés", "Saved companies"))]
    st.html('<div class="stats">' + ''.join(f'<div class="stat"><div class="stat-label">{escape(label)}</div><div class="stat-value">{value}</div><div class="stat-note">{escape(note)}</div></div>' for label,value,note in stats) + '</div>')
    st.caption(tr("Entreprises fictives · Évaluations directes de Codex · Justifications et réserves dans chaque fiche.", "Fictional companies · Direct Codex assessments · Evidence and caveats in each profile."))
    report = Path(__file__).parent / "docs/UNICORNEXT_V1_SCORES.md"
    if report.exists():
        st.download_button(tr("Télécharger les 50 analyses", "Download all 50 assessments"), report.read_text(), file_name="unicornext-v1-analyses.md", mime="text/markdown")
    chart, featured = st.columns([1.65, 1], gap="medium")
    with chart, st.container(key="market_distribution"):
        st.subheader(tr("Le pipeline, en perspective", "Your pipeline, in perspective"))
        st.caption(tr("Nombre de dossiers par tranche de score · sur 100", "Pitches by score range · out of 100"))
        buckets = [("0–19", 0, 20), ("20–39", 20, 40), ("40–59", 40, 60), ("60–79", 60, 80), ("80–100", 80, 101)]
        counts = [sum(d.score is not None and low <= d.score < high for d in dossiers) for _,low,high in buckets]
        peak = max(counts, default=0) or 1
        st.html('<div class="distribution">' + ''.join(f'<div class="dist-column"><span class="dist-value">{n}</span><div class="dist-bar" aria-hidden="true" style="height:{max(3,n/peak*125)}px"></div><span class="dist-label">{label}</span></div>' for (label,_,_),n in zip(buckets,counts)) + '</div>')
        if not any(counts):
            st.caption(t["no_score"])
    with featured, st.container(key="featured_company"):
        st.html('<div class="feature-kicker">' + tr("En tête du classement", "Leading the ranking") + '</div>')
        if groups["ranked"]:
            leader = groups["ranked"][0]
            st.subheader(leader.company_name)
            st.write(startup_idea(leader))
            st.caption(leader.sector)
            st.html(f'<div class="feature-score">{leader.score:.0f}<small> / 100</small></div>')
            st.button(tr("Découvrir le dossier ↗", "Explore the profile ↗"), key="featured_open", on_click=go, args=(leader.pitch_id,), width="stretch")
        else:
            st.subheader(tr("Votre prochain dossier", "Your next opportunity"))
            st.caption(t["no_score"])
            st.button(t["submit"], on_click=lambda: st.session_state.update(page="submit"), width="stretch")
    st.write("")
    st.subheader(tr("À regarder de plus près", "Worth a closer look"))
    st.caption(tr("Les 5 meilleurs dossiers scorés : score pondéré, puis traction et marché en cas d’égalité.", "Top 5 scored pitches: weighted score, then traction and market to break ties."))
    if groups["selected"]:
        cards(groups["selected"], "priority")
    else:
        empty(tr("Le pipeline attend ses premières analyses", "Your pipeline awaits its first analyses"), t["empty_scored"])
    left, right = st.columns([1.2, 1])
    with left, st.container(border=True):
        st.subheader(tr("Répartition par secteur", "Sector distribution"))
        sectors = Counter(d.sector for d in dossiers)
        for label, count in sectors.most_common(6):
            bar(label, count, max(sectors.values()))
        if len(sectors) > 6:
            st.caption(tr("Les 6 secteurs les plus représentés · tous les secteurs dans l’explorateur.", "Top 6 sectors · explore all sectors in Explore."))
        if not sectors:
            st.caption(tr("Aucun dossier reçu.", "No pitches received."))
    with right, st.container(border=True):
        st.subheader(tr("Progression du tri", "Triage progress"))
        for label, group in [(t["ranking"], "ranked"), (t["pending"], "pending"), (t["review"], "review")]:
            bar(label, len(groups[group]), len(dossiers))
        st.caption(tr("Les alertes sont incluses dans les dossiers scorés ou en attente ; elles ne forment pas une catégorie supplémentaire.", "Alerts overlap with scored or pending pitches; they are not an additional category."))
        if groups["pending"]:
            st.caption(t["partial"])
        st.button(tr("Explorer les dossiers", "Explore pitches"), on_click=lambda: st.session_state.update(page="search"), type="primary")

elif page == "search":
    left, right = st.columns([2, 1])
    search = left.text_input(t["search"], placeholder=tr("Entreprise, identifiant, secteur…", "Company, ID, sector…"))
    sector = right.selectbox(t["sector"], [t["all"], *sorted({d.sector for d in dossiers})])
    filtered = queue(dossiers, None if sector == t["all"] else sector, search)
    mode = st.radio(t["status"], ["all", "selected", "ranked", "review", "pending"], horizontal=True,
                    format_func=lambda k: {"all": tr("Tous", "All"), "selected": t["priority"], "ranked": t["ranking"], "review": t["review"], "pending": t["pending"]}[k])
    visible = filtered["ranked"] + filtered["pending"] if mode == "all" else filtered[mode]
    st.caption(tr(f"{len(visible)} dossiers affichables sur {len(dossiers)} au total", f"{len(visible)} matching pitches out of {len(dossiers)} total"))
    st.caption(tr("Tous les dossiers scorés participent au classement. Les alertes de manipulation sont informatives et peuvent concerner des dossiers déjà classés.", "All scored pitches are ranked. Manipulation alerts are informational and may apply to pitches already in the ranking."))
    view = st.radio(tr("Affichage", "View"), ["cards", "table"], horizontal=True, format_func=lambda x: tr("Cartes", "Cards") if x == "cards" else tr("Tableau", "Table"))
    if not visible:
        empty(tr("Aucun dossier dans cette vue", "No pitches in this view"), tr("Modifie les filtres ou dépose un nouveau pitch.", "Adjust the filters or submit a new pitch."))
    elif view == "table":
        st.dataframe([{"ID":d.pitch_id,t["company"]:d.company_name,t["sector"]:d.sector,t["score"]:d.score,t["recommendation"]:recommendation_label(d.recommendation),t["channel"]:t.get(d.channel,d.channel),t["status"]:t["flagged"] if d.flagged else t["waiting"] if d.score is None else t["ranked"]} for d in visible], hide_index=True, width="stretch")
        choice = st.selectbox(t["choose"], visible, format_func=lambda d: f"{d.company_name} · {d.pitch_id}")
        st.button(tr("Ouvrir la fiche", "Open profile"), on_click=go, args=(choice.pitch_id,))
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
        st.header(d.company_name)
        st.write(startup_idea(d))
        st.caption(f'{d.sector} · {t.get(d.channel,d.channel)}' + (f' · {d.submitted_at}' if d.submitted_at else ''))
        st.caption(tr("Source de la note : ", "Assessment source: ") + (d.assessment_source or "—"))
        save_button(d, "detail")
        if d.flagged:
            st.warning(t["guard"])
            st.write(d.guard_reason)
            for excerpt in d.guard_excerpts:
                st.code(excerpt, language=None, wrap_lines=True)
        if d.error:
            st.error(f'{t["error"]} {d.error}')
        if d.score is None:
            empty(tr("Analyse à venir", "Analysis pending"), t["no_score"])
        else:
            previous = st.session_state.get("last_scores", {})
            changed = pid in previous and previous[pid] != d.score
            with st.container(key="score_changed" if changed else "score_current"):
                a,b = st.columns(2)
                a.metric(t["score"], f"{d.score:.0f}")
                b.metric(t["recommendation"], recommendation_label(d.recommendation))
            st.session_state["last_scores"] = {**previous, pid:d.score}
            with st.container(border=True):
                st.subheader(t["criteria"])
                st.caption(tr("Équipe 20 % · Marché 25 % · Produit 15 % · Traction 25 % · Modèle 15 %. Échelle : 0 absent, 1 non étayé, 2 faible, 3 crédible, 4 solide, 5 exceptionnel.", "Team 20% · Market 25% · Product 15% · Traction 25% · Business model 15%. Scale: 0 absent, 1 unsupported, 2 weak, 3 credible, 4 strong, 5 exceptional."))
                for key,label in criteria.items():
                    bar(label, d.scores[key], 5, " / 5")
                    if d.criterion_reasons.get(key):
                        st.caption(d.criterion_reasons[key])
            a,b = st.columns(2)
            with a:
                bullets(t["strengths"], d.strengths)
                bullets(t["missing"], d.missing_information)
            with b:
                bullets(t["risks"], d.risks)
                bullets(t["evidence"], d.evidence)
            st.caption(t["source_language"])
        with st.expander(t["text"], expanded=d.score is None):
            st.text(d.text)

elif page == "shortlist":
    saved = [d for d in dossiers if d.pitch_id in saved_ids]
    if not saved:
        empty(tr("Votre prochaine conviction commence ici", "Your next conviction starts here"), tr("Ajoute des startups depuis l’explorateur ou leur fiche pour les retrouver et les comparer.", "Save startups from Explore or their profile to revisit and compare them."))
        st.button(tr("Explorer les startups", "Explore startups"), on_click=lambda: st.session_state.update(page="search"), type="primary")
    else:
        st.subheader(tr("Comparer les dossiers", "Compare companies"))
        chosen = st.multiselect(tr("Choisir jusqu’à 3 startups", "Choose up to 3 startups"), [d.pitch_id for d in saved], format_func=lambda pid: next(d.company_name for d in saved if d.pitch_id == pid), max_selections=3)
        if chosen:
            with st.container(key="page_comparison"):
                cols = st.columns(len(chosen))
                for col,pid in zip(cols,chosen):
                    d = next(d for d in saved if d.pitch_id == pid)
                    with col, st.container(border=True):
                        st.subheader(d.company_name)
                        st.write(startup_idea(d))
                        st.metric(t["score"], f"{d.score:.0f}" if d.score is not None else "—")
                        if d.flagged:
                            st.warning(t["guard"])
                        if d.score is None:
                            st.caption(t["no_score"])
                        else:
                            for key,label in criteria.items():
                                bar(label,d.scores[key],5," / 5")
                            st.caption(recommendation_label(d.recommendation))
        st.subheader(tr("Dossiers conservés", "Saved companies"))
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
