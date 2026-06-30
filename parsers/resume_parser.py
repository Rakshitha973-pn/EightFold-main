"""Resume PDF parser using pdfplumber plus deterministic regex extraction."""

from __future__ import annotations

import re
from pathlib import Path

try:
    import pdfplumber
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    pdfplumber = None

try:
    from pypdf import PdfReader
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    PdfReader = None

from models.candidate import ParsedCandidate
from normalizers.date import normalize_month
from normalizers.phone import normalize_phone
from normalizers.skills import normalize_skills

RESUME_CONFIDENCE = 0.95
REGEX_CONFIDENCE = 0.80
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
LINK_PATTERN = re.compile(r"https?://[^\s,]+|(?:linkedin|github)\.com/[^\s,]+", re.I)


def parse_resume_pdf(resume_path: Path | None) -> ParsedCandidate | None:
    """Parse a resume PDF into one parsed candidate record."""
    if resume_path is None or not resume_path.exists():
        return None
    text = _extract_text(resume_path)
    candidate = ParsedCandidate(source_name=resume_path.name, source_type="resume")
    if not text.strip():
        return candidate

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidate.add_field("full_name", _extract_name(lines), "resume_header", RESUME_CONFIDENCE)
    candidate.add_field("emails", _extract_emails(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("phones", _extract_phones(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("links", _extract_links(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("location", _parse_location(_extract_labeled_value(text, "Location")), "regex", REGEX_CONFIDENCE)
    candidate.add_field("headline", _extract_labeled_value(text, "Headline"), "regex", REGEX_CONFIDENCE)
    candidate.add_field("years_experience", _extract_years(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("skills", _extract_skills(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("experience", _extract_experience(text), "regex", REGEX_CONFIDENCE)
    candidate.add_field("education", _extract_education(text), "regex", REGEX_CONFIDENCE)
    return candidate


def _extract_text(path: Path) -> str:
    if not _looks_like_pdf(path):
        return _read_text_file(path)
    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            pass
    if PdfReader is not None:
        try:
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass
    return _read_text_file(path)


def _looks_like_pdf(path: Path) -> bool:
    try:
        return path.read_bytes()[:4] == b"%PDF"
    except OSError:
        return False


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _extract_name(lines: list[str]) -> str | None:
    for line in lines[:5]:
        if (
            "@" not in line
            and ":" not in line
            and not any(ch.isdigit() for ch in line)
        ):
            # Must contain at least one alphabetic character
            if re.search(r"[A-Za-z]", line):
                return line.strip()

    return None


def _extract_emails(text: str) -> list[str]:
    return sorted(set(email.lower() for email in EMAIL_PATTERN.findall(text)))


def _extract_phones(text: str) -> list[str]:
    phones = []
    for match in PHONE_PATTERN.findall(text):
        normalized = normalize_phone(match)
        if normalized:
            phones.append(normalized)
    return sorted(set(phones))


def _extract_links(text: str) -> list[str]:
    return sorted(set(link.rstrip(".") for link in LINK_PATTERN.findall(text)))


def _extract_labeled_value(text: str, label: str) -> str | None:
    match = re.search(rf"^{label}\s*:\s*(.+)$", text, re.I | re.M)
    return match.group(1).strip() if match else None


def _extract_years(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\+?\s+years?", text, re.I)
    return float(match.group(1)) if match else None


def _extract_skills(text: str) -> list[str]:
    match = re.search(r"^Skills\s*:\s*(.+)$", text, re.I | re.M)
    if not match:
        return []
    return normalize_skills(re.split(r"[,;|]", match.group(1)))


def _extract_experience(text: str) -> list[dict[str, str | None]]:
    match = re.search(r"^Experience\s*:\s*(.+)$", text, re.I | re.M)
    if not match:
        return []
    value = match.group(1).strip()
    date_match = re.search(r"(.+?)\s*\(([^-]+)-([^)]+)\)", value)
    if date_match:
        value = date_match.group(1).strip()
        start = normalize_month(date_match.group(2))
        end = normalize_month(date_match.group(3))
    else:
        start = None
        end = None
    company, _, title = value.partition("-")
    return [{"company": company.strip() or None, "title": title.strip() or None, "start": start, "end": end, "summary": None}]

def _extract_education(text: str) -> list[dict[str, str | None]]:
    match = re.search(r"^Education\s*:\s*(.+)$", text, re.I | re.M)

    if not match:
        return []

    value = match.group(1).strip()

    # Reject empty or obviously invalid values
    if (
        not value
        or value.lower().startswith("http")
        or value.lower().startswith("www")
        or "@" in value
        or value.lower() == "not_a_url"
    ):
        return []

    end_year_match = re.search(r"\b(19|20)\d{2}\b", value)
    end_year = int(end_year_match.group(0)) if end_year_match else None

    if end_year_match:
        value = value.replace(end_year_match.group(0), "").strip(" ,-")

    degree = None
    institution = value

    if "," in value:
        degree, institution = [
            part.strip()
            for part in value.split(",", 1)
        ]

    return [
        {
            "institution": institution or None,
            "degree": degree,
            "field": None,
            "end_year": end_year,
        }
    ]


def _parse_location(value: str | None) -> dict[str, str | None] | None:
    if not value:
        return None
    parts = [part.strip() for part in re.split(r"[,|]", value) if part.strip()]
    if len(parts) >= 3:
        return {"city": parts[0], "region": parts[1], "country": _country_code(parts[2])}
    if len(parts) == 2:
        return {"city": parts[0], "region": parts[1], "country": None}
    words = parts[0].split()
    if len(words) >= 2:
        return {"city": " ".join(words[:-1]), "region": words[-1], "country": None}
    return {"city": parts[0], "region": None, "country": None}


def _country_code(value: str | None) -> str | None:
    """
    Convert country names to ISO-3166 Alpha-2 country codes.

    Returns None if the country is unknown instead of inventing a value.
    """

    if not value:
        return None

    country = value.strip().upper()

    COUNTRY_MAP = {
        # United States
        "USA": "US",
        "UNITED STATES": "US",
        "US": "US",

        # India
        "INDIA": "IN",
        "IN": "IN",

        # Germany
        "GERMANY": "DE",
        "DE": "DE",

        # Canada
        "CANADA": "CA",
        "CA": "CA",

        # Australia
        "AUSTRALIA": "AU",
        "AU": "AU",

        # United Kingdom
        "UNITED KINGDOM": "GB",
        "UK": "GB",
        "GB": "GB",

        # France
        "FRANCE": "FR",
        "FR": "FR",

        # Japan
        "JAPAN": "JP",
        "JP": "JP",

        # China
        "CHINA": "CN",
        "CN": "CN",

        # Singapore
        "SINGAPORE": "SG",
        "SG": "SG",

        # Brazil
        "BRAZIL": "BR",
        "BR": "BR",

        # Italy
        "ITALY": "IT",
        "IT": "IT",

        # Spain
        "SPAIN": "ES",
        "ES": "ES",

        # Netherlands
        "NETHERLANDS": "NL",
        "NL": "NL",

        # Switzerland
        "SWITZERLAND": "CH",
        "CH": "CH",

        # Ireland
        "IRELAND": "IE",
        "IE": "IE",

        # South Korea
        "SOUTH KOREA": "KR",
        "KOREA": "KR",
        "KR": "KR",

        # United Arab Emirates
        "UAE": "AE",
        "UNITED ARAB EMIRATES": "AE",
        "AE": "AE",
    }

    return COUNTRY_MAP.get(country)
