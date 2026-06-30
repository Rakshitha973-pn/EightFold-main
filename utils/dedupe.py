"""Order-preserving deduplication helpers."""

from __future__ import annotations

from typing import Iterable, TypeVar

T = TypeVar("T")


def dedupe_preserve_order(values: Iterable[T]) -> list[T]:
    """Return unique values while preserving first-seen order."""
    seen: set[str] = set()
    result: list[T] = []
    for value in values:
        marker = repr(value).lower()
        if marker not in seen:
            seen.add(marker)
            result.append(value)
    return result
