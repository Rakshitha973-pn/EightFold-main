"""Pydantic validation for canonical and projected output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from models.candidate import CanonicalCandidate, EducationEntry, ExperienceEntry, Links, Location, ProvenanceEntry, SkillEntry


class DefaultCandidateOutput(BaseModel):
    """Default assignment schema."""

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
    overall_confidence: float


class ProjectedCandidate(BaseModel):
    """Permissive projected output schema for runtime-shaped JSON."""

    data: dict[str, Any]


def validate_canonical(candidate: CanonicalCandidate) -> CanonicalCandidate:
    """Validate canonical candidate output."""
    data = candidate.model_dump() if hasattr(candidate, "model_dump") else candidate.dict()
    return CanonicalCandidate(**data)


def validate_projected(output: dict[str, Any]) -> dict[str, Any]:
    """Validate projected JSON-like output; enforce default schema when present."""
    if hasattr(DefaultCandidateOutput, "model_fields"):
        default_fields = set(DefaultCandidateOutput.model_fields)
    else:
        default_fields = set(DefaultCandidateOutput.__fields__)
    if default_fields.issubset(output):
        DefaultCandidateOutput(**output)
    else:
        ProjectedCandidate(data=output)
    return output
