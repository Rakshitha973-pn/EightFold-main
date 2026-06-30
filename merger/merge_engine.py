"""Deterministic merge engine for parsed candidate data."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from merger.confidence import overall_confidence, score_field
from merger.provenance import create_provenance
from models.candidate import CanonicalCandidate, EducationEntry, ExperienceEntry, FieldValue, Links, Location, ParsedCandidate, ProvenanceEntry, SkillEntry
from utils.dedupe import dedupe_preserve_order

SOURCE_PRIORITY = {"resume": 2, "csv": 1}
LIST_FIELDS = ("emails", "phones")
SINGLE_FIELDS = ("full_name", "location", "headline", "years_experience")


def merge_candidates(parsed_candidates: list[ParsedCandidate]) -> CanonicalCandidate:
    """Merge parsed candidates into one canonical candidate profile."""
    grouped = _group_fields(parsed_candidates)
    provenance: list[ProvenanceEntry] = []
    field_scores: list[float] = []

    single_values = {}
    for field in SINGLE_FIELDS:
        selected = _select_highest_priority(grouped.get(field, []))
        single_values[field] = selected.value if selected else None
        _track(field, selected, grouped.get(field, []), provenance, field_scores)

    list_values = {}
    for field in LIST_FIELDS:
        selected_values, selected_entry = _merge_list_field(grouped.get(field, []))
        list_values[field] = selected_values
        _track(field, selected_entry, grouped.get(field, []), provenance, field_scores)

    links, links_entry = _merge_links(grouped.get("links", []))
    _track("links", links_entry, grouped.get("links", []), provenance, field_scores)
    skills, skills_entry = _merge_skills(grouped.get("skills", []))
    _track("skills", skills_entry, grouped.get("skills", []), provenance, field_scores)

    experience, experience_entry = _merge_model_list(grouped.get("experience", []), ExperienceEntry)
    education, education_entry = _merge_model_list(grouped.get("education", []), EducationEntry)
    _track("experience", experience_entry, grouped.get("experience", []), provenance, field_scores)
    _track("education", education_entry, grouped.get("education", []), provenance, field_scores)

    return CanonicalCandidate(
        candidate_id=_stable_candidate_id(single_values["full_name"], list_values["emails"], list_values["phones"]),
        full_name=single_values["full_name"],
        emails=list_values["emails"],
        phones=list_values["phones"],
        location=Location(**single_values["location"]) if single_values["location"] else None,
        links=links,
        headline=single_values["headline"],
        years_experience=single_values["years_experience"],
        skills=skills,
        experience=experience,
        education=education,
        provenance=provenance,
        overall_confidence=overall_confidence(field_scores),
    )


def _group_fields(parsed_candidates: list[ParsedCandidate]) -> dict[str, list[FieldValue]]:
    grouped: dict[str, list[FieldValue]] = {}
    for candidate in parsed_candidates:
        for field, values in candidate.fields.items():
            grouped.setdefault(field, []).extend(values)
    return grouped


def _select_highest_priority(values: list[FieldValue]) -> FieldValue | None:
    if not values:
        return None
    return sorted(values, key=lambda item: (SOURCE_PRIORITY.get(_source_type(item.source), 0), item.confidence), reverse=True)[0]


def _merge_list_field(values: list[FieldValue]) -> tuple[list[str], FieldValue | None]:
    if not values:
        return [], None
    sorted_values = sorted(values, key=lambda item: SOURCE_PRIORITY.get(_source_type(item.source), 0), reverse=True)
    merged: list[str] = []
    for entry in sorted_values:
        merged.extend(str(value) for value in entry.value)
    return dedupe_preserve_order(merged), sorted_values[0]


def _merge_model_list(values: list[FieldValue], model_class: type[ExperienceEntry] | type[EducationEntry]):
    if not values:
        return [], None
    selected = _select_highest_priority(values)
    return [model_class(**value) for value in selected.value], selected


def _merge_links(values: list[FieldValue]) -> tuple[Links, FieldValue | None]:
    merged, selected = _merge_list_field(values)
    links = Links()
    for link in merged:
        lowered = link.lower()
        if "linkedin.com" in lowered and not links.linkedin:
            links.linkedin = link
        elif "github.com" in lowered and not links.github:
            links.github = link
        elif not links.portfolio and ("portfolio" in lowered or "://" in lowered):
            links.portfolio = link
        else:
            links.other.append(link)
    return links, selected


def _merge_skills(values: list[FieldValue]) -> tuple[list[SkillEntry], FieldValue | None]:
    if not values:
        return [], None
    sorted_values = sorted(values, key=lambda item: SOURCE_PRIORITY.get(_source_type(item.source), 0), reverse=True)
    by_skill: dict[str, list[FieldValue]] = {}
    order: list[str] = []
    for entry in sorted_values:
        for raw_skill in entry.value:
            skill_name = str(raw_skill)
            if skill_name not in by_skill:
                order.append(skill_name)
            by_skill.setdefault(skill_name, []).append(entry)
    skills = []
    for skill_name in order:
        entries = by_skill[skill_name]
        score = max(entry.confidence for entry in entries)
        if len({entry.source for entry in entries}) > 1:
            score += 0.03
        score = max(0.0, min(round(score, 2), 1.0))
        sources = dedupe_preserve_order(entry.source for entry in entries)
        skills.append(SkillEntry(name=skill_name, confidence=score, sources=sources))
    return skills, sorted_values[0]


def _source_type(source_name: str) -> str:
    return "resume" if source_name.lower().endswith(".pdf") else "csv"


def _track(field: str, selected: FieldValue | None, values: list[FieldValue], provenance: list[ProvenanceEntry], field_scores: list[float]) -> None:
    entry = create_provenance(field, selected)
    if entry:
        provenance.append(entry)
    field_scores.append(score_field(selected, values))


def _stable_candidate_id(full_name: str | None, emails: list[str], phones: list[str]) -> str:
    identity = "|".join([full_name or "", ",".join(sorted(emails)), ",".join(sorted(phones))]).lower()
    if not identity.strip("|,"):
        identity = "empty-candidate"
    return str(uuid5(NAMESPACE_URL, identity))
