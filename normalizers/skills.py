"""Skill normalization using a deterministic synonym dictionary."""

from __future__ import annotations

import re

from utils.dedupe import dedupe_preserve_order


SKILL_SYNONYMS = {
    "c++": "C++",
    "cpp": "C++",
    "c plus plus": "C++",

    "javascript": "JavaScript",
    "js": "JavaScript",
    "java script": "JavaScript",

    "python": "Python",
    "py": "Python",

    "sql": "SQL",

    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",

    "machine learning": "Machine Learning",
    "ml": "Machine Learning",

    "data analysis": "Data Analysis",

    "pandas": "Pandas",
}


def normalize_skill(raw_skill: str) -> str | None:
    """
    Normalize a single skill.

    Invalid skills containing no alphabetic characters are ignored.
    """

    if not raw_skill:
        return None

    cleaned = " ".join(raw_skill.strip().split())

    if not cleaned:
        return None

    # Reject skills with no alphabetic characters
    if not re.search(r"[A-Za-z]", cleaned):
        return None

    return SKILL_SYNONYMS.get(cleaned.lower(), cleaned.title())


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """
    Normalize and deduplicate skills while preserving order.
    """

    normalized = []

    for skill in raw_skills:
        canonical = normalize_skill(skill)

        if canonical:
            normalized.append(canonical)

    return dedupe_preserve_order(normalized)