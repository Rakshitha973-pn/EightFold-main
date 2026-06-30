"""Phone number normalization."""

from __future__ import annotations

import re

try:
    import phonenumbers
except ModuleNotFoundError:  # pragma: no cover - exercised only without optional dependency
    phonenumbers = None


def normalize_phone(raw_phone: str, default_region: str = "US") -> str | None:
    """Normalize a phone number to E.164, returning None when invalid."""
    if not raw_phone:
        return None
    if phonenumbers is None:
        return _fallback_e164(raw_phone, default_region)
    try:
        parsed = phonenumbers.parse(raw_phone, default_region)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(parsed):
        return None
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def _fallback_e164(raw_phone: str, default_region: str) -> str | None:
    digits = re.sub(r"\D", "", raw_phone)
    if not digits:
        return None
    if raw_phone.strip().startswith("+"):
        return f"+{digits}" if 8 <= len(digits) <= 15 else None
    if default_region.upper() == "US" and len(digits) == 10:
        return f"+1{digits}"
    if default_region.upper() == "US" and len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None
