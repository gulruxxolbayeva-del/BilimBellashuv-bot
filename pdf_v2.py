from __future__ import annotations

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Question", parent=styles["BodyText"], fontSize=11, leading=15, spaceAfter=5))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#5B677A")))
    return styles


def _p(text, style):
    safe = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe.replace("\n", "<br/>"), style)


def build_test_pdf(path: str | Path, title: str, questions: list[dict], kind: str = "quiz", answers: str = "hidden"):
    """Create a printable quiz/written test PDF.

    answers: hidden, inline, or key. The creator chooses this setting.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    story = [_p(title, styles["Title"]), Spacer(1, 4 * mm), _p("BilimBellashuv testi", styles["Small"]), Spacer(1, 6 * mm)]
    for number, q in enumerate(questions, 1):
        story.append(_p(f"{number}. {q.get('text', '')}   ({q.get('points', 1)} ball)", styles["Question"]))
        if kind != "written":
            opts = q.get("options", [])
            data = [[f"{chr(65+i)}.", str(opt)] for i, opt in enumerate(opts)]
            table = Table(data, colWidths=[12 * mm, 160 * mm])
            table.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 10), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story.append(table)
        else:
            story.append(Spacer(1, 3 * mm))
            story.append(_p("Javob: ________________________________________________________________", styles["BodyText"]))
            story.append(Spacer(1, 8 * mm))
        if answers == "inline":
            story.append(_p(f"To‘g‘ri javob: {q.get('correct_answer', q.get('accepted', ''))}", styles["Small"]))
        story.append(Spacer(1, 5 * mm))
    if answers == "key":
        story.append(PageBreak())
        story.append(_p("Javoblar kaliti", styles["Heading2"]))
        for number, q in enumerate(questions, 1):
            story.append(_p(f"{number}. {q.get('correct_answer', q.get('accepted', ''))}", styles["BodyText"]))
    SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm).build(story)
    return path


def build_certificate(path: str | Path, participant: str, title: str, result: str, date_text: str, body_text: str = ""):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    story = [Spacer(1, 25 * mm), _p("DIPLOM", styles["Title"]), Spacer(1, 12 * mm), _p(participant, styles["Heading1"]), Spacer(1, 8 * mm), _p(f"{title} testidagi natijasi: {result}", styles["Heading2"]), Spacer(1, 10 * mm)]
    if body_text:
        story.append(_p(body_text, styles["BodyText"]))
        story.append(Spacer(1, 10 * mm))
    story.append(_p(date_text, styles["Small"]))
    SimpleDocTemplate(str(path), pagesize=A4, rightMargin=25 * mm, leftMargin=25 * mm, topMargin=20 * mm, bottomMargin=20 * mm).build(story)
    return path
