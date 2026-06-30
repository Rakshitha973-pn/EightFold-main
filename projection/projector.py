"""Projection layer for runtime output configuration."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from models.candidate import CanonicalCandidate
from normalizers.phone import normalize_phone
from normalizers.skills import normalize_skill


class ProjectionError(ValueError):
    """Raised when projection cannot satisfy the requested config."""


def project_candidate(candidate: CanonicalCandidate, config: dict[str, Any]) -> dict[str, Any]:
    """Project canonical data without mutating the canonical candidate."""
    data = _model_dump(candidate)
    field_specs = config.get("fields") or list(data.keys())
    missing_strategy = config.get(
        "on_missing",
        config.get("missing_value_strategy", "null"),
    )

    output: dict[str, Any] = {}

    for spec in field_specs:
        output_name, source_path, required, expected_type, normalization = _parse_field_spec(
            spec, config
        )

        value = _resolve_path(data, source_path)

        if _is_missing(value):
            if required or missing_strategy == "error":
                raise ProjectionError(f"Missing value for field: {source_path}")

            if missing_strategy == "omit":
                continue

            value = None

        value = _apply_normalization(value, normalization)
        _validate_type(output_name, value, expected_type)

        output[output_name] = value

    if not config.get("include_confidence", True):
        output.pop("overall_confidence", None)

    if not config.get("include_provenance", True):
        output.pop("provenance", None)

    return output


def _parse_field_spec(
    spec: Any,
    config: dict[str, Any],
) -> tuple[str, str, bool, str | None, str | None]:

    if isinstance(spec, dict):
        output_name = spec["path"]
        return (
            output_name,
            spec.get("from", output_name),
            bool(spec.get("required", False)),
            spec.get("type"),
            spec.get("normalize"),
        )

    field = str(spec)
    mappings = config.get("map_fields", {})
    renames = config.get("rename_fields", {})

    return (
        renames.get(field, field),
        mappings.get(field, field),
        False,
        None,
        None,
    )


def _resolve_path(data: Any, path: str) -> Any:
    current = data

    for token in path.split("."):

        if token.endswith("[]"):
            base = token[:-2]
            current = _get_key(current, base)

            if not isinstance(current, list):
                return None

            continue

        array_attr = re.fullmatch(r"(.+)\[(\d+)\]", token)

        if array_attr:
            current = _get_key(current, array_attr.group(1))
            index = int(array_attr.group(2))

            if not isinstance(current, list) or index >= len(current):
                return None

            current = current[index]
            continue

        if isinstance(current, list):
            current = [_get_key(item, token) for item in current]
        else:
            current = _get_key(current, token)

        if current is None:
            return None

    return current


def _get_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def _apply_normalization(value: Any, normalization: str | None) -> Any:
    if value is None or not normalization:
        return value

    normalized = normalization.lower()

    if normalized == "e164":
        if isinstance(value, list):
            return [
                phone
                for item in value
                if (phone := normalize_phone(str(item)))
            ]
        return normalize_phone(str(value))

    if normalized == "canonical":
        if isinstance(value, list):
            return [
                skill
                for item in value
                if (skill := normalize_skill(str(item)))
            ]
        return normalize_skill(str(value))

    return value


def _validate_type(
    field: str,
    value: Any,
    expected_type: str | None,
) -> None:

    if value is None or expected_type is None:
        return

    if expected_type == "string" and not isinstance(value, str):
        raise ProjectionError(f"{field} must be a string")

    if expected_type == "number" and not isinstance(value, (int, float)):
        raise ProjectionError(f"{field} must be a number")

    if (
        expected_type == "string[]"
        and (
            not isinstance(value, list)
            or not all(isinstance(item, str) for item in value)
        )
    ):
        raise ProjectionError(f"{field} must be a string array")


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _is_missing(value: Any) -> bool:
    """
    Only None represents a missing value.

    Empty lists and empty dictionaries are valid outputs
    because they indicate that the field was parsed but
    contains no values.
    """
    return value is None