"""CLI entry point for the Candidate Profile Transformation Engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from merger.merge_engine import merge_candidates
from parsers.csv_parser import parse_recruiter_csv
from parsers.resume_parser import parse_resume_pdf
from projection.projector import project_candidate
from validator.schema_validator import (
    validate_canonical,
    validate_projected,
)

DEFAULT_OUTPUT_PATH = Path("sample_outputs/candidate.json")


def run_pipeline(
    csv_path: Path | None,
    resume_path: Path | None,
    config_path: Path,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, Any]:
    """Run the complete transformation pipeline."""

    config = _load_config(config_path)

    parsed_candidates = []

    if csv_path:
        parsed_candidates.extend(parse_recruiter_csv(csv_path))

    if resume_path:
        resume_candidate = parse_resume_pdf(resume_path)
        if resume_candidate:
            parsed_candidates.append(resume_candidate)

    canonical = validate_canonical(merge_candidates(parsed_candidates))

    projected = project_candidate(canonical, config)

    validate_projected(projected)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(projected, indent=4),
        encoding="utf-8",
    )

    return projected


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Candidate Profile Transformation Engine"
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path to recruiter CSV",
    )

    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="Path to resume PDF",
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to configuration JSON",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output JSON file",
    )

    return parser


def _load_config(config_path: Path) -> dict[str, Any]:
    """Load runtime configuration."""

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    """CLI entry point."""

    args = build_parser().parse_args()

    output = run_pipeline(
        args.csv,
        args.resume,
        args.config,
        args.output,
    )

    print(json.dumps(output, indent=4))


if __name__ == "__main__":
    main()