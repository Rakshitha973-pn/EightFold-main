# Eightfold Candidate Transformer - One-Page Design

## Problem Framing

Downstream hiring products need one trustworthy candidate profile from messy sources. The engine must prefer being honestly empty over confidently wrong, so every output value should be normalized, deduplicated, explainable, and validated before JSON is returned.

## Pipeline

The pipeline is `Parse → Normalize → Merge → Provenance & Confidence → Projection → Validation → JSON Output`. A recruiter CSV parser handles structured rows. A resume parser handles unstructured PDF/text-like resumes through `pdfplumber`, `pypdf`, or a text fallback. Parsers emit source-tagged field values rather than writing directly to the final schema, which keeps extraction separate from canonical modeling.

## Canonical Schema And Normalization

The canonical profile uses the assignment schema: `candidate_id`, `full_name`, `emails`, `phones`, `location`, `links`, `headline`, `years_experience`, `skills`, `experience`, `education`, `provenance`, and `overall_confidence`. Phones are normalized to E.164. Dates are normalized to `YYYY-MM` when present. Skills are canonicalized with a deterministic synonym dictionary, so `cpp` becomes `C++` and `js` becomes `JavaScript`. Location is represented as `{ city, region, country }`, and links are grouped as `{ linkedin, github, portfolio, other[] }`.

## Merge And Confidence Policy

Single-value conflicts are resolved deterministically by source priority: resume beats CSV, then higher extraction confidence breaks ties. Lists such as emails, phones, and links are merged and deduplicated while preserving priority order. Skills become `{ name, confidence, sources[] }` objects so agreement across sources is visible. The `candidate_id` is deterministic, generated from stable identity fields instead of a random UUID. Overall confidence is the average of populated field confidence scores.

## Runtime Custom Output Config

The projection layer reshapes the canonical candidate at runtime without modifying the underlying canonical model. The default config emits the full canonical schema. The custom config can select fields, rename output paths, read from canonical paths such as `emails[0]` and `skills[].name`, apply per-field normalization, include or hide provenance/confidence, and choose missing-value behavior with null, omit, or error. The canonical model is validated first; projected output is validated before it is written.

## Edge Cases And Scope

Handled edge cases include missing CSV/resume files, malformed CSV files, text-like files with a `.pdf` extension, missing optional PDF/phone dependencies, invalid phone numbers, duplicate skills/emails, and source conflicts. Deliberately out of scope under time pressure: production-grade resume section parsing, multi-candidate entity resolution across many CSV rows, country inference beyond simple aliases, and live GitHub or LinkedIn API ingestion.
