"""
Renders the tailored resume JSON into a clean, ATS-friendly, single-column
PDF using reportlab. No external binaries (LibreOffice, wkhtmltopdf, etc.)
required, which keeps this portable and fast.

Schema expected (from core.prompts):
{
  "name": "string",
  "title": "string",
  "contact": {"email", "phone", "location", "linkedin"},
  "summary": "string",
  "skills": ["string", ...],
  "experience": [{"company", "role", "dates", "location", "bullets": [...]}],
  "projects": [{"name", "description", "bullets": [...]}],
  "education": [{"school", "degree", "dates"}],
  "keywords_emphasized": [...]          # ignored during rendering
}
"""

import io
from xml.sax.saxutils import escape as _xml_escape

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
)

# ── colour palette ──────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1B2A4A")   # headings, name, horizontal rule
TEXT   = colors.HexColor("#222222")    # body text
MUTED  = colors.HexColor("#555555")   # dates, meta, contact line


# ── style factory ───────────────────────────────────────────────────────────
def _styles() -> dict[str, ParagraphStyle]:
    """Build the full set of paragraph styles used in the resume."""
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "ResumeName",
            parent=base["Title"],
            alignment=TA_LEFT,
            fontSize=22,
            leading=26,
            textColor=NAVY,
            spaceAfter=2,
            fontName="Helvetica-Bold",
        ),
        "title": ParagraphStyle(
            "ResumeTitle",
            parent=base["Normal"],
            fontSize=12,
            leading=15,
            textColor=MUTED,
            spaceAfter=4,
            fontName="Helvetica-Oblique",
        ),
        "contact": ParagraphStyle(
            "ResumeContact",
            parent=base["Normal"],
            fontSize=9.5,
            leading=12,
            textColor=MUTED,
            spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=11.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=3,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=TEXT,
        ),
        "bullet": ParagraphStyle(
            "BulletText",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=TEXT,
        ),
        "role": ParagraphStyle(
            "RoleLine",
            parent=base["Normal"],
            fontSize=10.5,
            leading=13,
            textColor=TEXT,
            fontName="Helvetica-Bold",
            spaceBefore=6,
        ),
        "meta": ParagraphStyle(
            "MetaLine",
            parent=base["Normal"],
            fontSize=9,
            leading=11,
            textColor=MUTED,
            spaceAfter=2,
        ),
        "proj_desc": ParagraphStyle(
            "ProjectDescription",
            parent=base["Normal"],
            fontSize=9.5,
            leading=12,
            textColor=MUTED,
            fontName="Helvetica-Oblique",
            spaceAfter=1,
        ),
    }


# ── public API ──────────────────────────────────────────────────────────────
def build_resume_pdf(resume: dict) -> bytes:
    """Take a structured resume dict and return the rendered PDF as bytes.

    Sections are emitted in the order:
        Name / Title / Contact → SUMMARY → SKILLS → EXPERIENCE →
        PROJECTS → EDUCATION
    Any section whose data is empty/missing is silently skipped.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
    )
    s = _styles()
    story: list = []

    # ── header block ────────────────────────────────────────────────────
    story.append(Paragraph(_esc(resume.get("name", "")), s["name"]))

    if resume.get("title"):
        story.append(Paragraph(_esc(resume["title"]), s["title"]))

    contact = resume.get("contact") or {}
    contact_parts = [
        contact.get("email"),
        contact.get("phone"),
        contact.get("location"),
        contact.get("linkedin"),
    ]
    contact_line = "  |  ".join(p for p in contact_parts if p)
    if contact_line:
        story.append(Paragraph(_esc(contact_line), s["contact"]))

    story.append(HRFlowable(width="100%", color=NAVY, thickness=1.2))

    # ── SUMMARY ─────────────────────────────────────────────────────────
    if resume.get("summary"):
        story.append(Paragraph("SUMMARY", s["section"]))
        story.append(Paragraph(_esc(resume["summary"]), s["body"]))

    # ── SKILLS ──────────────────────────────────────────────────────────
    if resume.get("skills"):
        story.append(Paragraph("SKILLS", s["section"]))
        skills_text = " &nbsp;&bull;&nbsp; ".join(_esc(sk) for sk in resume["skills"])
        story.append(Paragraph(skills_text, s["body"]))

    # ── EXPERIENCE ──────────────────────────────────────────────────────
    if resume.get("experience"):
        story.append(Paragraph("EXPERIENCE", s["section"]))
        for job in resume["experience"]:
            role    = _esc(job.get("role", ""))
            company = _esc(job.get("company", ""))
            header  = f"{role} \u2014 {company}" if company else role
            story.append(Paragraph(header, s["role"]))

            meta_parts = [job.get("dates"), job.get("location")]
            meta = "  |  ".join(_esc(p) for p in meta_parts if p)
            if meta:
                story.append(Paragraph(meta, s["meta"]))

            bullets = job.get("bullets") or []
            if bullets:
                story.append(_bullet_list(bullets, s["bullet"]))

    # ── PROJECTS ────────────────────────────────────────────────────────
    if resume.get("projects"):
        story.append(Paragraph("PROJECTS", s["section"]))
        for proj in resume["projects"]:
            story.append(Paragraph(_esc(proj.get("name", "")), s["role"]))
            if proj.get("description"):
                story.append(Paragraph(_esc(proj["description"]), s["proj_desc"]))
            bullets = proj.get("bullets") or []
            if bullets:
                story.append(_bullet_list(bullets, s["bullet"]))

    # ── EDUCATION ───────────────────────────────────────────────────────
    if resume.get("education"):
        story.append(Paragraph("EDUCATION", s["section"]))
        for edu in resume["education"]:
            degree = _esc(edu.get("degree", ""))
            school = _esc(edu.get("school", ""))
            line   = f"{degree} \u2014 {school}" if school else degree
            story.append(Paragraph(line, s["role"]))
            if edu.get("dates"):
                story.append(Paragraph(_esc(edu["dates"]), s["meta"]))

    # ── render & return ─────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── helpers ─────────────────────────────────────────────────────────────────
def _esc(text: str) -> str:
    """XML-escape user text so <, >, & don't break reportlab's Paragraph."""
    return _xml_escape(text)


def _bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    """Render a list of strings as a bulleted ReportLab ListFlowable."""
    return ListFlowable(
        [ListItem(Paragraph(_esc(item), style), spaceAfter=2) for item in items],
        bulletType="bullet",
        start="\u2022",       # bullet character •
        leftIndent=14,
        bulletFontSize=10,
        bulletOffsetY=0,
    )
