"""
Renders the tailored resume JSON into a clean, ATS-friendly, single-column
PDF using reportlab. No external binaries (LibreOffice, wkhtmltopdf, etc.)
required, which keeps this portable and fast.
"""

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

ACCENT = colors.HexColor("#1a2b4c")
TEXT = colors.HexColor("#222222")
MUTED = colors.HexColor("#555555")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "name": ParagraphStyle(
            "name", parent=base["Title"], alignment=TA_LEFT, fontSize=22,
            textColor=ACCENT, spaceAfter=2, fontName="Helvetica-Bold",
        ),
        "title": ParagraphStyle(
            "title", parent=base["Normal"], fontSize=12, textColor=MUTED,
            spaceAfter=8, fontName="Helvetica-Oblique",
        ),
        "contact": ParagraphStyle(
            "contact", parent=base["Normal"], fontSize=9.5, textColor=MUTED,
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"], fontSize=12, textColor=ACCENT,
            spaceBefore=12, spaceAfter=4, fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=10, textColor=TEXT,
            leading=13,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontSize=10, textColor=TEXT,
            leading=13,
        ),
        "role": ParagraphStyle(
            "role", parent=base["Normal"], fontSize=10.5, textColor=TEXT,
            fontName="Helvetica-Bold", spaceBefore=6,
        ),
        "meta": ParagraphStyle(
            "meta", parent=base["Normal"], fontSize=9, textColor=MUTED,
        ),
    }
    return styles


def build_resume_pdf(resume: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
    )
    s = _styles()
    story = []

    contact = resume.get("contact", {}) or {}
    contact_line = " | ".join(
        v for v in [contact.get("email"), contact.get("phone"),
                    contact.get("location"), contact.get("linkedin")] if v
    )

    story.append(Paragraph(resume.get("name", ""), s["name"]))
    if resume.get("title"):
        story.append(Paragraph(resume["title"], s["title"]))
    if contact_line:
        story.append(Paragraph(contact_line, s["contact"]))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1.2))

    if resume.get("summary"):
        story.append(Paragraph("SUMMARY", s["section"]))
        story.append(Paragraph(resume["summary"], s["body"]))

    if resume.get("skills"):
        story.append(Paragraph("SKILLS", s["section"]))
        story.append(Paragraph(" &nbsp;•&nbsp; ".join(resume["skills"]), s["body"]))

    if resume.get("experience"):
        story.append(Paragraph("EXPERIENCE", s["section"]))
        for job in resume["experience"]:
            header = f"{job.get('role', '')} — {job.get('company', '')}"
            meta = " | ".join(v for v in [job.get("dates"), job.get("location")] if v)
            story.append(Paragraph(header, s["role"]))
            if meta:
                story.append(Paragraph(meta, s["meta"]))
            bullets = job.get("bullets") or []
            if bullets:
                story.append(_bullet_list(bullets, s["bullet"]))

    if resume.get("projects"):
        story.append(Paragraph("PROJECTS", s["section"]))
        for proj in resume["projects"]:
            story.append(Paragraph(proj.get("name", ""), s["role"]))
            if proj.get("description"):
                story.append(Paragraph(proj["description"], s["body"]))
            bullets = proj.get("bullets") or []
            if bullets:
                story.append(_bullet_list(bullets, s["bullet"]))

    if resume.get("education"):
        story.append(Paragraph("EDUCATION", s["section"]))
        for edu in resume["education"]:
            line = f"{edu.get('degree', '')} — {edu.get('school', '')}"
            story.append(Paragraph(line, s["role"]))
            if edu.get("dates"):
                story.append(Paragraph(edu["dates"], s["meta"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _bullet_list(items, style):
    return ListFlowable(
        [ListItem(Paragraph(item, style), spaceAfter=2) for item in items],
        bulletType="bullet", start="•", leftIndent=14,
    )
