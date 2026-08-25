from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class ShapeStats:
    path: str
    rows: int
    columns: int
    column_names: List[str]
    column_types: Dict[str, str]
    memory_bytes: int
    duplicate_rows: int
    missing_by_column: Dict[str, int]


def _read_table(path: Path) -> tuple[list[str], list[dict[str, Optional[str]]]]:
    text = path.read_text(encoding="utf-8-sig")
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = list(reader.fieldnames or [])
    rows: list[dict[str, Optional[str]]] = []
    for row in reader:
        normalized = {k: (v if v is not None else "") for k, v in row.items()}
        rows.append(normalized)
    return headers, rows


def _column_type(values: Iterable[Optional[str]]) -> str:
    non_empty = [str(v).strip() for v in values if v not in (None, "") and str(v).strip() not in ("", "NaN", "nan", "None", "none", "null", "NULL")]
    if not non_empty:
        return "empty"

    def all_numeric(seq: list[str]) -> bool:
        for value in seq:
            try:
                float(value)
            except ValueError:
                return False
        return True

    if all_numeric(non_empty):
        if all("." in v or "e" in v.lower() for v in non_empty):
            return "float"
        return "int"

    if all(len(v) == 19 and v[4] == "-" and v[7] == "-" for v in non_empty):
        return "date"

    if all(v.lower() in ("true", "false", "1", "0", "yes", "no", "on", "off") for v in non_empty):
        return "bool"

    return "text"


def _duplicate_count(rows: Sequence[dict[str, Optional[str]]]) -> int:
    seen = set()
    duplicates = 0
    for row in rows:
        key = tuple((k, "" if v is None else v) for k, v in row.items())
        if key in seen:
            duplicates += 1
        seen.add(key)
    return duplicates


def compute(path: Path) -> ShapeStats:
    headers, rows = _read_table(path)
    missing_by_column: Dict[str, int] = {header: 0 for header in headers}
    for row in rows:
        for header in headers:
            value = row.get(header, "")
            if value in (None, ""):
                missing_by_column[header] += 1

    column_values_by_name: Dict[str, list[Optional[str]]] = {header: [] for header in headers}
    for row in rows:
        for header in headers:
            column_values_by_name[header].append(row.get(header))

    return ShapeStats(
        path=str(path),
        rows=len(rows),
        columns=len(headers),
        column_names=headers,
        column_types={header: _column_type(column_values_by_name[header]) for header in headers},
        memory_bytes=path.stat().st_size,
        duplicate_rows=_duplicate_count(rows),
        missing_by_column=missing_by_column,
    )


def _format_stats(stats: ShapeStats) -> str:
    lines = [
        f"path: {stats.path}",
        f"rows: {stats.rows}",
        f"columns: {stats.columns}",
        "columns:",
    ]
    for name in stats.column_names:
        ctype = stats.column_types[name]
        missing = stats.missing_by_column[name]
        lines.append(f"  {name}: type={ctype}, missing={missing}")
    lines.append(f"duplicate_rows: {stats.duplicate_rows}")
    lines.append(f"memory_bytes: {stats.memory_bytes}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize CSV/TSV shape and column statistics.")
    parser.add_argument("paths", nargs="+", type=Path, help="Input delimited files")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")

    if argv and "--help" in argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    outputs = []
    exit_code = 0
    for path in args.paths:
        if not path.exists() or not path.is_file():
            print(f"missing: {path}", file=sys.stderr)
            exit_code = 1
            continue
        stats = compute(path)
        outputs.append(stats)

    if args.json:
        print(json.dumps([stat.__dict__ for stat in outputs], indent=2))
    else:
        for stat in outputs:
            print(_format_stats(stat))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
