# ShapeStat Guide

## Shape summary overview

ShapeStat prints one logical block per file:

- `path`
- `rows`
- `columns`
- `columns` with per-column type and missing count
- `duplicate_rows`
- `memory_bytes`

## Column type inference

Inferred types:

- `int`: every non-empty value parses as an integer form
- `float`: numeric with a fractional or exponent marker
- `date`: 19-character `YYYY-MM-DD` shape on every non-empty value
- `bool`: true/false-style literals
- `text`: anything else with at least one non-empty value
- `empty`: column has no non-empty values

Type inference does not guarantee schema accuracy; treat it as a triage signal.

## Missing values

A value counts as missing when it is blank after parsing. Empty strings and explicit null-like strings (`null`, `none`, `NaN`) are ignored for type inference but still count toward missing values when blank.

## Duplicate rows

Rows are deduplicated by exact column/value tuples after normalization. A row is flagged as duplicate only if its entire record already appeared earlier.

## JSON mode

`--json` emits one JSON array of objects. Each object contains the full stats payload including raw arrays for column metadata.
