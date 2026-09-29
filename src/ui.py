"""Primitives visuelles d'Unicornext (voir DESIGN.md, section 5).

Chaque fonction renvoie du HTML, sans dépendance à Streamlit : `app.py` le
passe à `st.html`, les tests le lisent tel quel.

Tout texte dynamique est échappé. Les noms d'entreprise et les extraits de
pitchs viennent de fondateurs inconnus (Telegram, e-mail) : aucun ne doit
pouvoir injecter de balise dans la page.
"""
from __future__ import annotations

import json
from html import escape
from typing import Optional, Sequence, Tuple
from urllib.parse import quote

# Seuils du produit (docs/UNICORNEXT_V1.md) : haute priorité, à approfondir, non prioritaire.
HIGH_FROM = 75
MID_FROM = 50

# --- Icônes (Lucide, licence ISC) : le contenu de <svg>, dessiné sur 24 × 24 ---------

ICONS = {
    "dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/>'
                 '<rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "explore": '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>',
    "profile": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/>'
               '<path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/>'
               '<path d="M10 14h4"/><path d="M10 18h4"/>',
    "shortlist": '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>',
    "submit": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "chart": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
              '<path d="M12 8v4"/><path d="M12 16h.01"/>',
    "arrow": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
}

# L'ordre des pages de la barre latérale (app.py) : une icône par entrée du radio.
NAV_ICONS = ("dashboard", "explore", "profile", "shortlist", "submit")


def _mask_url(name: str) -> str:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" '
           f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')
    return "data:image/svg+xml," + quote(svg, safe="")


def icon(name: str, size: int = 18) -> str:
    """Une icône. Streamlit retire les <svg> en ligne : elle est dessinée par un masque CSS (`icons_css`)."""
    return f'<span class="ico ico--{name}" style="--size:{size}px" aria-hidden="true"></span>'


def icons_css() -> str:
    """Les masques de toutes les icônes. À injecter une fois dans un bloc de style."""
    return "\n".join(f'.ico--{name}{{-webkit-mask-image:url("{_mask_url(name)}");mask-image:url("{_mask_url(name)}")}}'
                     for name in ICONS)


def nav_icon_css() -> str:
    """Une icône par entrée de la navigation, en masque CSS sur le libellé du radio."""
    return "\n".join(
        f'[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:nth-of-type({position}) > div:last-child::before'
        f'{{-webkit-mask-image:url("{_mask_url(name)}");mask-image:url("{_mask_url(name)}")}}'
        for position, name in enumerate(NAV_ICONS, start=1))


# --- Niveaux de score ---------------------------------------------------------


def tier(score: Optional[float]) -> str:
    """`high` ≥ 75, `mid` 50–74, `low` en dessous, `none` sans score."""
    if score is None:
        return "none"
    if score >= HIGH_FROM:
        return "high"
    return "mid" if score >= MID_FROM else "low"


def _count(value: float) -> str:
    """Un chiffre qui compte jusqu'à sa valeur (CSS pur). Le vrai nombre reste lisible."""
    n = int(round(value))
    return f'<span class="sr-only">{n}</span><span class="count" style="--v:{n}" aria-hidden="true"></span>'


# --- Primitives ---------------------------------------------------------------


def tag(text: str, tone: str = "neutral", dot: bool = False) -> str:
    marker = '<span class="tag__dot" aria-hidden="true"></span>' if dot else ""
    return f'<span class="tag tag--{escape(tone)}">{marker}{escape(text)}</span>'


def score_ring(score: Optional[float], size: str = "md", surface: str = "light", label: str = "Score") -> str:
    """L'anneau de score, signature du produit. `size` : sm, md, lg. `surface` : light, dark."""
    if score is None:
        return (f'<div class="ring ring--{size} ring--none ring--{surface}" role="img" '
                f'aria-label="{escape(label)} —"><span class="ring__value" aria-hidden="true">—</span></div>')
    pct = max(0.0, min(100.0, float(score)))
    return (f'<div class="ring ring--{size} ring--{tier(pct)} ring--{surface}" role="img" '
            f'aria-label="{escape(label)} {round(pct)} / 100" style="--pct:{pct:.1f}">'
            f'<span class="ring__value" aria-hidden="true"><span class="count" style="--v:{round(pct)}"></span></span></div>')


def stat_card(label: str, value: float, note: str, icon_name: str, tone: str = "default", index: int = 0) -> str:
    return (f'<div class="stat stat--{escape(tone)}" style="--i:{min(index, 6)}">'
            f'<div class="stat__top"><span class="stat__icon">{icon(icon_name, 16)}</span>'
            f'<span class="stat__label">{escape(label)}</span></div>'
            f'<div class="stat__value">{_count(value)}</div>'
            f'<div class="stat__note">{escape(note)}</div></div>')


def stat_row(cards: Sequence[str]) -> str:
    return '<div class="stats">' + "".join(cards) + "</div>"


def dossier_card(*, status: str, status_tone: str, name: str, idea: str, sector: str, pitch_id: str,
                 score: Optional[float], verdict: str, ring_label: str = "Score", index: int = 0) -> str:
    return (f'<div class="dcard" style="--i:{min(index, 6)}">'
            f'<div class="dcard__status">{tag(status, status_tone, dot=True)}</div>'
            f'<div class="dcard__row"><div class="dcard__id">'
            f'<h3 class="dcard__name">{escape(name)}</h3>'
            f'<div class="dcard__meta"><span>{escape(sector)}</span><span class="dcard__sep" aria-hidden="true"></span>'
            f'<span class="dcard__pid">{escape(pitch_id)}</span></div></div>'
            f'{score_ring(score, "sm", label=ring_label)}</div>'
            f'<p class="dcard__idea">{escape(idea)}</p>'
            f'<div class="dcard__verdict">{escape(verdict)}</div></div>')


def featured(kicker: str, name: str, idea: str, sector: str, score: Optional[float], ring_label: str = "Score") -> str:
    """La carte à l'encre du dossier en tête du classement."""
    return (f'<div class="feat"><div class="feat__kicker">{escape(kicker)}</div>'
            f'<div class="feat__row"><div class="feat__id"><h3 class="feat__name">{escape(name)}</h3>'
            f'<div class="feat__sector">{escape(sector)}</div></div>'
            f'{score_ring(score, "lg", "dark", ring_label)}</div>'
            f'<p class="feat__idea">{escape(idea)}</p></div>')


def profile_header(name: str, idea: str, meta: Sequence[str], score: Optional[float],
                   status: str, status_tone: str, ring_label: str = "Score") -> str:
    chips = "".join(f'<span class="profile__chip">{escape(item)}</span>' for item in meta if item)
    return (f'<div class="profile"><div class="profile__main">{tag(status, status_tone, dot=True)}'
            f'<h2 class="profile__name">{escape(name)}</h2>'
            f'<p class="profile__idea">{escape(idea)}</p><div class="profile__meta">{chips}</div></div>'
            f'{score_ring(score, "lg", label=ring_label)}</div>')


def bar_row(label: str, value: float, maximum: float, suffix: str = "", index: int = 0) -> str:
    percent = max(0.0, min(100.0, value / maximum * 100)) if maximum else 0.0
    shown = f"{value:g}{suffix}"
    return (f'<div class="bar" style="--i:{min(index, 6)}"><div class="bar__label"><span>{escape(label)}</span>'
            f'<strong>{escape(shown)}</strong></div>'
            f'<div class="bar__track" role="meter" aria-label="{escape(label)}" aria-valuenow="{value:g}" '
            f'aria-valuemin="0" aria-valuemax="{maximum:g}"><div class="bar__fill" style="width:{percent:.1f}%"></div></div></div>')


def distribution(buckets: Sequence[Tuple[str, int]]) -> str:
    """Un histogramme : une colonne par tranche de score, colorée par la rampe (DESIGN.md §2)."""
    peak = max((n for _, n in buckets), default=0) or 1
    columns = "".join(
        f'<div class="dist__col" style="--i:{i}"><span class="dist__value">{n}</span>'
        f'<div class="dist__slot"><div class="dist__bar dist__bar--{i + 1}" aria-hidden="true" '
        f'style="height:{max(n / peak * 100, 3 if n else 1.5):.1f}%"></div></div>'
        f'<span class="dist__label">{escape(label)}</span></div>'
        for i, (label, n) in enumerate(buckets))
    return f'<div class="dist" role="group">{columns}</div>'


def empty_state(title: str, description: str, icon_name: str = "inbox") -> str:
    return (f'<div class="empty" role="status"><span class="empty__icon">{icon(icon_name, 22)}</span>'
            f'<div><strong>{escape(title)}</strong><p>{escape(description)}</p></div></div>')


def page_header(eyebrow: str, title: str, subtitle: str, hero: bool = False) -> str:
    """`title` est du texte ; la variante `hero` accepte un fragment déjà composé (`hero_title`)."""
    heading = title if hero else escape(title)
    klass = "display" if hero else "h1"
    return (f'<header class="page-head"><div class="eyebrow">{escape(eyebrow)}</div>'
            f'<h1 class="{klass}">{heading}</h1><p class="lede">{escape(subtitle)}</p></header>')


def hero_title(before: str, highlight: str) -> str:
    """L'accroche de la vue d'ensemble : une ligne, puis le passage en dégradé licorne."""
    return f'{escape(before)}<br><span class="hl">{escape(highlight)}</span>'


def section_head(title: str, caption: str = "") -> str:
    note = f'<p>{escape(caption)}</p>' if caption else ""
    return f'<div class="section-head"><h2>{escape(title)}</h2>{note}</div>'


def sonar_html(js: str) -> str:
    """L'amorceur du champ de points (assets/sonar.js).

    Streamlit ne laisse pas passer de `<script>` dans `st.html` : ce fragment est destiné à
    `components.html(..., height=0)`. Son iframe ne fait qu'une chose, recopier le script dans la
    page principale, où il tourne ensuite seul, une seule fois. Il survit ainsi aux rechargements
    de l'iframe, qui ne l'interrompent plus.
    """
    code = json.dumps(js).replace("</", "<\\/")
    return ("<script>(function(){var p=window.parent;if(p.document.getElementById('unicornext-sonar-js'))return;"
            "var s=p.document.createElement('script');s.id='unicornext-sonar-js';"
            f"s.textContent={code};p.document.head.appendChild(s);}})();</script>")
