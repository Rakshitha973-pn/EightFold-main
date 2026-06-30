"""Date normalization helpers."""

from __future__ import annotations

from dateutil import parser


def normalize_month(raw_date: str | None) -> str | None:
    """Normalize a date-like value to YYYY-MM."""
    if not raw_date:
        return None
    cleaned = raw_date.strip()
    if cleaned.lower() in {"present", "current", "now"}:
        return "Present"
    try:
        parsed = parser.parse(cleaned, fuzzy=True, default=parser.parse("1900-01-01"))
    except (ValueError, TypeError, OverflowError):
        return None
    return f"{parsed.year:04d}-{parsed.month:02d}"
