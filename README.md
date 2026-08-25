# ShapeStat

**Summarize CSV/TSV file shape, column types, missing counts, and duplicate rows.**

ShapeStat is a small CLI and library that profiles delimited data files in seconds. It is useful for data QA, ingestion pipelines, and exploratory analysis where you need a quick shape summary before loading data into a database or notebook.

## Features

- Row and column counts
- Column-level missing value counts
- Per-column type inference: `int`, `float`, `date`, `bool`, `text`, `empty`
- Duplicate row detection by exact content
- Memory footprint of the source file
- Text and JSON output modes
- Multi-file support in a single invocation

## Installation

```bash
python -m pip install -e .
```

## Usage

```bash
shapestat data.csv
shapestat --json sales.csv users.tsv
```

Sample output:

```
path: data.csv
rows: 4
columns: 3
columns:
  id: type=int, missing=0
  name: type=text, missing=0
  score: type=float, missing=1
duplicate_rows: 0
memory_bytes: 128
```

## Project Structure

```
shapestat/
  README.md
  pyproject.toml
  shapestat.py
  tests/
    test_shapestat.py
  docs/
    guide.md
```

## Notes

- The type inference is best-effort and designed for quick triage, not strict schema enforcement.
- Files are read fully into memory; very large files may take longer.

## License

MIT
