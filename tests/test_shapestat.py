from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure local flat package import wins without install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shapestat


def _write_csv(path: Path, rows: list[dict[str, str | None]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if v is None else v) for k, v in row.items()})


def test_compute_basic() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "sample.csv"
        _write_csv(path, [
            {"id": "1", "name": "alpha", "score": "10"},
            {"id": "2", "name": "beta", "score": "20"},
        ])
        stats = shapestat.compute(path)
        assert stats.rows == 2
        assert stats.columns == 3
        assert stats.column_types == {"id": "int", "name": "text", "score": "int"}
        assert stats.duplicate_rows == 0
        assert stats.missing_by_column == {"id": 0, "name": 0, "score": 0}


def test_compute_duplicates_and_missing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "dupes.csv"
        _write_csv(path, [
            {"id": "1", "value": "a"},
            {"id": "2", "value": "b"},
            {"id": "1", "value": "a"},
            {"id": "3", "value": None},
        ])
        stats = shapestat.compute(path)
        assert stats.rows == 4
        assert stats.duplicate_rows == 1
        assert stats.missing_by_column == {"id": 0, "value": 1}
        assert stats.column_types == {"id": "int", "value": "text"}


def test_compute_empty_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "empty.csv"
        path.write_text("", encoding="utf-8")
        stats = shapestat.compute(path)
        assert stats.rows == 0
        assert stats.columns == 0
        assert stats.column_types == {}
        assert stats.duplicate_rows == 0


def test_compute_header_only_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "headers.csv"
        path.write_text("a,b,c\n", encoding="utf-8")
        stats = shapestat.compute(path)
        assert stats.rows == 0
        assert stats.columns == 3
        assert stats.column_types == {"a": "empty", "b": "empty", "c": "empty"}


def test_compute_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        shapestat.compute(missing)


def test_cli_help_exits_zero() -> None:
    rc = shapestat.main(["--help"])
    assert rc == 0


def test_cli_missing_path_returns_nonzero() -> None:
    rc = shapestat.main(["/tmp/__nonexistent_shapestat_path__.csv"])
    assert rc == 1


def test_cli_text_output() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "demo.csv"
        _write_csv(path, [
            {"id": "1", "flag": "true"},
            {"id": "2", "flag": "false"},
        ])
        rc = shapestat.main([str(path)])
        assert rc == 0


def test_cli_json_output() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "demo.csv"
        _write_csv(path, [{"id": "1", "flag": "true"}])
        rc = shapestat.main(["--json", str(path)])
        assert rc == 0
