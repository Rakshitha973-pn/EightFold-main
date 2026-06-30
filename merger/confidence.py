"""Deterministic confidence scoring."""

from __future__ import annotations

from models.candidate import FieldValue


def score_field(selected: FieldValue | None, values: list[FieldValue]) -> float:
    """Score one output field based on source confidence, agreement, and conflict."""
    if selected is None:
        return 0.0
    score = selected.confidence
    unique_values = {repr(value.value).lower() for value in values}
    sources = {value.source for value in values}
    if len(sources) > 1 and len(unique_values) == 1:
        score += 0.03
    if len(unique_values) > 1:
        score -= 0.05
    return max(0.0, min(round(score, 2), 1.0))


def overall_confidence(field_scores: list[float]) -> float:
    """Calculate overall confidence as the average populated-field confidence."""
    populated = [score for score in field_scores if score > 0]
    if not populated:
        return 0.0
    return round(sum(populated) / len(populated), 2)
