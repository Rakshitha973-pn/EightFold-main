# Multi-Source Candidate Data Transformer

This project turns messy candidate inputs into one clean, canonical, schema-valid profile. It handles one structured source, a recruiter CSV export, and one unstructured source, a resume file. The engine normalizes values, merges conflicting data deterministically, records provenance, assigns confidence, applies a runtime output config, validates the result, and writes JSON.

## What Is Included

- Structured source: `sample_inputs/recruiter.csv`
- Unstructured source: `sample_inputs/resume.pdf`
- Default schema output: `sample_outputs/candidate.json`
- Custom config output: `sample_outputs/custom_candidate.json`
- One-page design document: `DESIGN.md`
- Tests covering merge policy, projection config, validation, phone normalization, and skill normalization

## Project Structure

```text
EightFold-main/
│
├── config/            # Runtime configuration files
├── merger/            # Merge logic and confidence scoring
├── models/            # Pydantic data models
├── normalizers/       # Phone, skill, and date normalization
├── parsers/           # CSV and resume parsers
├── projection/        # Runtime output projection
├── sample_inputs/     # Sample recruiter CSV and resume
├── sample_outputs/    # Generated JSON outputs
├── tests/             # Unit tests
├── tools/             # Utility scripts
├── utils/             # Shared helper functions
├── validator/         # Schema validation
├── DESIGN.md
├── main.py
├── README.md
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The code has defensive fallbacks for missing optional PDF/phone packages, but installing the requirements is the expected way to run it.

## Assumptions

- One recruiter CSV and one resume are processed per execution.
- Resume information has higher priority than recruiter CSV for candidate-authored fields such as headline and skills.
- Invalid or malformed values are ignored rather than inferred, ensuring the engine never invents missing information.
- Unknown countries are represented as null unless mapped to a valid ISO-3166 Alpha-2 code.

## Run Default Output

```bash
python main.py --csv sample_inputs/recruiter.csv --resume sample_inputs/resume.pdf --config config/default.json --output sample_outputs/candidate.json
```

## Run Custom Config Output

```bash
python main.py --csv sample_inputs/recruiter.csv --resume sample_inputs/resume.pdf --config config/custom.json --output sample_outputs/custom_candidate.json
```

The custom config demonstrates assignment-style projection:

- Selects a subset of fields.
- Reads from canonical paths such as `emails[0]` and `skills[].name`.
- Renames fields like `primary_email` and `confidence`.
- Applies per-field normalization such as `E164` and `canonical`.
- Omits provenance while retaining confidence.

## Run Tests

```bash
python -m unittest discover tests
```

## Default Output Schema

The default profile follows the assignment shape:

- `candidate_id`: deterministic string generated from stable candidate identity values.
- `full_name`: string or null.
- `emails`: string array.
- `phones`: E.164 string array.
- `location`: `{ city, region, country }`, with country as ISO-3166 alpha-2 when known.
- `links`: `{ linkedin, github, portfolio, other[] }`.
- `headline`: string or null.
- `years_experience`: number or null.
- `skills`: `{ name, confidence, sources[] }[]`.
- `experience`: `{ company, title, start, end, summary }[]`, dates normalized to `YYYY-MM` when present.
- `education`: `{ institution, degree, field, end_year }[]`.
- `provenance`: `{ field, source, method }[]`.
- `overall_confidence`: number.

## Validation

The projected JSON is validated using Pydantic before being written to disk.

Malformed or missing values are handled according to the runtime configuration:

- `null`
- `omit`
- `error`

This ensures invalid input does not crash the pipeline.

## Design Notes

The pipeline follows these stages:

**Parse → Normalize → Merge → Confidence Scoring → Projection → Validation → JSON Output**

Resume values take priority for candidate-authored fields such as headline and skills, while recruiter CSV values are preferred for recruiter-managed information where appropriate.

List fields are merged, deduplicated, and ordered by source priority. Every selected value records provenance, making merge decisions transparent and explainable.

Malformed or missing inputs never crash the pipeline. Missing values are represented as `null`, omitted, or treated as errors depending on the runtime configuration.

## Time Complexity

| Component | Complexity |
|-----------|------------|
| CSV Parsing | O(n) |
| Resume Parsing | O(n) |
| Normalization | O(n) |
| Merge Engine | O(n) |
| Projection | O(n) |
| Validation | O(n) |

where *n* is the number of extracted fields or records.

## Edge Cases Tested

- Missing email
- Missing phone number
- Invalid email format
- Invalid phone number
- Unknown country names
- Duplicate skills across sources
- Missing education details
- Invalid years of experience
- Empty resume
- Malformed recruiter CSV

## Trade-offs

- Used deterministic rule-based parsing instead of NLP to keep the solution explainable and predictable.
- Used a fixed skill synonym dictionary instead of external APIs to avoid network dependencies.
- Candidate IDs are generated using UUIDv5 to ensure deterministic and repeatable outputs for identical inputs.
- Prioritized readability and maintainability over more complex heuristics.

## Future Improvements

- Support multiple resumes in a single execution.
- Add LinkedIn and GitHub profile ingestion.
- Replace regex-based extraction with NLP models.
- Expand country and skill normalization dictionaries.
- Add asynchronous processing for larger datasets.
