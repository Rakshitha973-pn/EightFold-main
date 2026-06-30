"""Pydantic models for parsed and canonical candidate profiles."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProvenanceEntry(BaseModel):
    """Describes where an output field came from."""

    field: str
    source: str
    method: str


class Location(BaseModel):
    """Normalized candidate location."""

    city: str | None = None
    region: str | None = None
    country: str | None = None


class Links(BaseModel):
    """Normalized candidate links grouped by destination."""

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    """Canonical skill with explainable confidence and sources."""

    name: str
    confidence: float
    sources: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    """A normalized work experience item."""

    company: str | None = None
    title: str | None = None
    start: str | None = None
    end: str | None = None
    summary: str | None = None


class EducationEntry(BaseModel):
    """A normalized education item."""

    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    end_year: int | None = None


class FieldValue(BaseModel):
    """A parsed field value before merging."""

    value: Any
    source: str
    method: str
    confidence: float


class ParsedCandidate(BaseModel):
    """Candidate data extracted from one input source."""

    source_name: str
    source_type: str
    fields: dict[str, list[FieldValue]] = Field(default_factory=dict)

    def add_field(self, field: str, value: Any, method: str, confidence: float) -> None:
        """Add a parsed field when the value is present."""
        if value is None or value == "" or value == []:
            return
        entry = FieldValue(value=value, source=self.source_name, method=method, confidence=confidence)
        self.fields.setdefault(field, []).append(entry)


class CanonicalCandidate(BaseModel):
    """The immutable canonical candidate profile."""

    candidate_id: str
    full_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    location: Location | None = None
    links: Links = Field(default_factory=Links)
    headline: str | None = None
    years_experience: float | None = None
    skills: list[SkillEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    provenance: list[ProvenanceEntry] = Field(default_factory=list)
    overall_confidence: float = 0.0
