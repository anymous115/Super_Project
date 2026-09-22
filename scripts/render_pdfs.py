#!/usr/bin/env python3
"""Rend chaque pitch en PDF depuis `pitch_text` (§6 du protocole).

    python3 scripts/render_pdfs.py            # les 50
    python3 scripts/render_pdfs.py P005 P046  # quelques-uns

**Le PDF n'est pas une seconde entrée du benchmark.** `pitch_text` est l'entrée
unique : les deux modèles reçoivent la même chaîne de caractères. Les PDF sont
rendus *depuis* ce texte, servent à la démonstration, et la qualité de leur
extraction se mesure à part.

Trois mises en page, attribuées de façon déterministe. Un corpus où tous les
PDF sortent du même gabarit ne teste pas l'extraction : il teste un gabarit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
PITCHES = ROOT / "data" / "pitches.jsonl"
OUT = ROOT / "data" / "pdfs"

try:
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                    Paragraph, SimpleDocTemplate, Spacer)
except ImportError:
    sys.exit("reportlab manquant — pip install -r requirements.txt")

# Les titres de section du gabarit de rédaction.
HEADINGS = {
    "THE PROBLEM", "OUR SOLUTION", "THE MARKET", "COMPETITION", "THE TEAM",
    "TRACTION", "BUSINESS MODEL", "GO-TO-MARKET", "FUNDING",
}

LAYOUTS = ("serif", "deux colonnes", "sans-serif")


def styles_for(layout: str) -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    serif = layout != "sans-serif"
    body_font = "Times-Roman" if serif else "Helvetica"
    head_font = "Times-Bold" if serif else "Helvetica-Bold"
    size = 9.5 if layout == "deux colonnes" else 10.5
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=head_font,
                                fontSize=15, spaceAfter=14, alignment=0),
        "heading": ParagraphStyle("heading", parent=base["Heading2"], fontName=head_font,
                                  fontSize=size + 0.5, spaceBefore=11, spaceAfter=4,
                                  textColor="#222222"),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=body_font,
                               fontSize=size, leading=size * 1.42, spaceAfter=6,
                               alignment=TA_JUSTIFY if serif else 0),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontName=body_font,
                                 fontSize=size, leading=size * 1.42, leftIndent=12,
                                 bulletIndent=3, spaceAfter=3),
    }


def flow(text: str, style: Dict[str, ParagraphStyle]) -> List:
    """Transforme le texte en éléments, en reconnaissant titres et puces."""
    lines = text.split("\n")
    story = [Paragraph(lines[0].replace("—", "&mdash;"), style["title"])]
    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if line in HEADINGS:
            story.append(Paragraph(line.title(), style["heading"]))
        elif line.startswith("- "):
            story.append(Paragraph(line[2:], style["bullet"], bulletText="•"))
        else:
            story.append(Paragraph(line, style["body"]))
    return story


def render(pitch: dict, layout: str, path: Path) -> None:
    style = styles_for(layout)
    story = flow(pitch["pitch_text"], style)
    title = f"{pitch['company_name']} — pitch"

    if layout == "deux colonnes":
        doc = BaseDocTemplate(str(path), pagesize=A4, title=title,
                              leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                              topMargin=2 * cm, bottomMargin=2 * cm)
        gap, width = 0.8 * cm, (doc.width - 0.8 * cm) / 2
        frames = [
            Frame(doc.leftMargin, doc.bottomMargin, width, doc.height, id="gauche"),
            Frame(doc.leftMargin + width + gap, doc.bottomMargin, width, doc.height, id="droite"),
        ]
        doc.addPageTemplates([PageTemplate(id="deux", frames=frames)])
        doc.build(story)
        return

    margin = 2.2 * cm if layout == "serif" else 2.6 * cm
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=title,
                            leftMargin=margin, rightMargin=margin,
                            topMargin=2.2 * cm, bottomMargin=2.2 * cm)
    if layout == "sans-serif":
        story.insert(0, Spacer(1, 1.2 * cm))
    doc.build(story)


def main() -> int:
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
    rows = [json.loads(l) for l in PITCHES.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("pitch_text")]
    if wanted:
        rows = [r for r in rows if r["pitch_id"] in wanted]
        if not rows:
            sys.exit(f"aucun pitch rédigé parmi {', '.join(wanted)}")

    OUT.mkdir(parents=True, exist_ok=True)
    counts = {layout: 0 for layout in LAYOUTS}
    for row in rows:
        # Attribution déterministe : le même pitch sort toujours dans la même mise en page.
        layout = LAYOUTS[int(row["pitch_id"][1:]) % len(LAYOUTS)]
        render(row, layout, OUT / f"{row['pitch_id']}.pdf")
        counts[layout] += 1

    total = sum(counts.values())
    print(f"{total} PDF écrits dans {OUT.relative_to(ROOT)}")
    for layout, n in counts.items():
        print(f"  {layout:<14} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
