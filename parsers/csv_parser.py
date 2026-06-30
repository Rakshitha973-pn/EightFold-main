"""Recruiter CSV parser."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from models.candidate import ParsedCandidate
from normalizers.phone import normalize_phone
from normalizers.skills import normalize_skills

CSV_CONFIDENCE = 0.90

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

def parse_recruiter_csv(csv_path: Path | None) -> list[ParsedCandidate]:
    """Parse recruiter CSV rows into parsed candidate records."""
    if csv_path is None or not csv_path.exists():
        return []
    try:
        frame = pd.read_csv(csv_path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return []

    parsed_candidates: list[ParsedCandidate] = []
    for _, row in frame.iterrows():
        candidate = ParsedCandidate(source_name=csv_path.name, source_type="csv")
        candidate.add_field("full_name",_validate_name(_get(row, "full_name", "name")),"csv",CSV_CONFIDENCE,)
        candidate.add_field("emails",_extract_emails(_get(row, "email", "emails")),"csv",CSV_CONFIDENCE,)
        phones = [normalized for phone in _split_list(_get(row, "phone", "phones")) if (normalized := normalize_phone(phone))]
        candidate.add_field("phones", phones, "csv", CSV_CONFIDENCE)
        candidate.add_field("location", _parse_location(_get(row, "location", "city")), "csv", CSV_CONFIDENCE)
        candidate.add_field("headline", _get(row, "headline", "title"), "csv", CSV_CONFIDENCE)
        candidate.add_field("years_experience", _to_float(_get(row, "years_experience")), "csv", CSV_CONFIDENCE)
        candidate.add_field("skills", normalize_skills(_split_list(_get(row, "skills"))), "csv", CSV_CONFIDENCE)
        candidate.add_field("links", _split_list(_get(row, "links", "linkedin", "github")), "csv", CSV_CONFIDENCE)
        parsed_candidates.append(candidate)
    return parsed_candidates


def _split_list(value: Any) -> list[str]:
    """Split a delimited string into a cleaned list."""
    if value is None or pd.isna(value):
        return []

    return [
        item.strip()
        for item in re.split(r"[;,|]", str(value))
        if item.strip()
    ]

def _get(row: pd.Series, *names: str) -> Any:
    lower_to_actual = {column.lower(): column for column in row.index}
    for name in names:
        actual = lower_to_actual.get(name.lower())
        if actual is not None and not pd.isna(row[actual]):
            return row[actual]
    return None


def _to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_location(value: Any) -> dict[str, str | None] | None:
    if value is None or pd.isna(value):
        return None
    parts = [part.strip() for part in re.split(r"[,|]", str(value)) if part.strip()]
    if not parts:
        return None
    if len(parts) >= 3:
        return {"city": parts[0], "region": parts[1], "country": _country_code(parts[2])}
    if len(parts) == 2:
        return {"city": parts[0], "region": parts[1], "country": None}
    words = parts[0].split()
    if len(words) >= 2:
        return {"city": " ".join(words[:-1]), "region": words[-1], "country": None}
    return {"city": parts[0], "region": None, "country": None}


def _country_code(value: str | None) -> str | None:
    """Convert country names to ISO-3166 Alpha-2 codes."""

    if not value:
        return None

    country = value.strip().upper()

    COUNTRY_MAP = {
        "USA": "US",
        "UNITED STATES": "US",
        "US": "US",

        "INDIA": "IN",
        "IN": "IN",

        "GERMANY": "DE",
        "DE": "DE",

        "CANADA": "CA",
        "CA": "CA",

        "AUSTRALIA": "AU",
        "AU": "AU",

        "UNITED KINGDOM": "GB",
        "UK": "GB",
        "GB": "GB",

        "FRANCE": "FR",
        "FR": "FR",

        "JAPAN": "JP",
        "JP": "JP",

        "CHINA": "CN",
        "CN": "CN",

        "SINGAPORE": "SG",
        "SG": "SG",
    }

    return COUNTRY_MAP.get(country)

def _extract_emails(value: Any) -> list[str]:
    """Validate and normalize email addresses."""

    emails = []

    for email in _split_list(value):
        email = email.lower()

        if EMAIL_PATTERN.fullmatch(email):
            emails.append(email)

    return sorted(set(emails))

def _validate_name(value: Any) -> str | None:
    """Validate candidate name."""

    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    # Must contain at least one alphabetic character
    if not re.search(r"[A-Za-z]", value):
        return None

    return value