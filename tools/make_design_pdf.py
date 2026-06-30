"""Generate the one-page Eightfold design PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "YourFullName_YourEmail_Eightfold.pdf"


def main() -> None:
    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.fontSize = 16
    heading = styles["Heading2"]
    heading.fontSize = 10
    body = styles["BodyText"]
    body.fontSize = 8.4
    body.leading = 10.5

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=34,
        bottomMargin=34,
    )
    story = [
        Paragraph("Eightfold Candidate Transformer - One-Page Design", title),
        Spacer(1, 6),
    ]
    sections = [
        ("Problem Framing", "Downstream hiring products need one trustworthy candidate profile from messy sources. The engine prefers being honestly empty over confidently wrong, so every value is normalized, deduplicated, explainable, and validated before JSON is returned."),
        ("Pipeline", "The pipeline is parse -> normalize -> merge -> confidence -> project -> validate -> write. A recruiter CSV parser handles structured rows. A resume parser handles unstructured PDF/text-like resumes through pdfplumber, pypdf, or a text fallback. Parsers emit source-tagged field values instead of writing directly to final JSON."),
        ("Canonical Schema And Normalization", "The canonical profile follows the assignment schema: candidate_id, full_name, emails, phones, location, links, headline, years_experience, skills, experience, education, provenance, and overall_confidence. Phones are E.164, dates are YYYY-MM when present, skills are canonicalized, location is { city, region, country }, and links are grouped as { linkedin, github, portfolio, other[] }."),
        ("Merge And Confidence Policy", "Single-value conflicts are deterministic: resume beats CSV, then higher confidence breaks ties. Lists are merged and deduplicated while preserving priority order. Skills become { name, confidence, sources[] } objects, so agreement across sources is visible. candidate_id is deterministic from stable identity fields, not random."),
        ("Runtime Custom Output Config", "Projection is separate from the canonical record. Config can select fields, rename output paths, read paths such as emails[0] and skills[].name, apply per-field normalization, include or hide provenance/confidence, and choose missing behavior with null, omit, or error. Canonical and projected outputs are validated before writing."),
        ("Edge Cases And Scope", "Handled: missing CSV/resume files, malformed CSV, text-like .pdf files, missing optional PDF/phone dependencies, invalid phones, duplicate emails/skills, and conflicting values. Left out under time pressure: production resume parsing, multi-candidate entity resolution, rich country inference, and live GitHub/LinkedIn API ingestion."),
    ]
    for section_title, section_body in sections:
        heading.textColor = colors.HexColor("#1f4e79")
        story.append(Paragraph(section_title, heading))
        story.append(Paragraph(section_body, body))
        story.append(Spacer(1, 5))
    doc.build(story)


if __name__ == "__main__":
    main()
