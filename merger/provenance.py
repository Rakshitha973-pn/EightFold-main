"""Provenance helpers."""

from __future__ import annotations

from models.candidate import FieldValue, ProvenanceEntry


def create_provenance(field: str, selected: FieldValue | None) -> ProvenanceEntry | None:
    """Create a provenance entry for a selected field value."""
    if selected is None:
        return None
    return ProvenanceEntry(field=field, source=selected.source, method=selected.method)
