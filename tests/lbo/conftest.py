"""Shared pytest fixtures and lightweight benchmark registry for institutional financial models."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "benchmark.json"


@dataclass(frozen=True, slots=True)
class BenchmarkCell:
    """Duck-typed benchmark cell mirroring AuditedCell."""

    value: float | None
    raw_text: str | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkRow:
    """Duck-typed benchmark row mirroring AuditedRow."""

    id: str
    cells: dict[str, BenchmarkCell]


class BenchmarkTable:
    """Duck-typed benchmark table mirroring AuditedTable."""

    def __init__(
        self,
        table_id: str,
        row_order: list[str],
        cells: dict[str, dict[str, float | None]],
        raw_texts: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.id: str = table_id
        raw_texts = raw_texts or {}
        rows: list[BenchmarkRow] = []
        rows_by_id: dict[str, BenchmarkRow] = {}

        for r_id in row_order:
            r_cells: dict[str, BenchmarkCell] = {}
            r_raw = raw_texts.get(r_id, {})
            for c_id, val in cells.get(r_id, {}).items():
                rt = r_raw.get(c_id, str(val) if val is not None else None)
                r_cells[c_id] = BenchmarkCell(value=val, raw_text=rt)
            brow = BenchmarkRow(id=r_id, cells=r_cells)
            rows.append(brow)
            rows_by_id[r_id] = brow

        self.rows: list[BenchmarkRow] = rows
        self._rows_by_id: dict[str, BenchmarkRow] = rows_by_id

    def get_cell(self, row_id: str, col_id: str) -> BenchmarkCell | None:
        brow = self._rows_by_id.get(row_id)
        if brow is None:
            return None
        return brow.cells.get(col_id)

    def val(self, row_id: str, col_id: str) -> float | None:
        cell = self.get_cell(row_id, col_id)
        return cell.value if cell is not None else None

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[BenchmarkRow]:
        return iter(self.rows)


class BenchmarkRegistry:
    """Duck-typed table registry loading canonical benchmark matrices."""

    def __init__(self, fixture_path: Path | str | None = None) -> None:
        if fixture_path is None:
            resolved_path = FIXTURE_PATH
        else:
            p = Path(fixture_path)
            if p.is_dir():
                resolved_path = p / "benchmark.json"
                if not resolved_path.exists():
                    resolved_path = FIXTURE_PATH
            else:
                resolved_path = p

        with open(resolved_path, encoding="utf-8") as f:
            data: dict[
                str,
                dict[
                    str,
                    list[str] | dict[str, dict[str, float | None]] | dict[str, dict[str, str]],
                ],
            ] = json.load(f)

        self._tables: dict[str, BenchmarkTable] = {}
        for t_id, t_data in data.items():
            row_order = t_data["row_order"]
            cells = t_data["cells"]
            raw_texts = t_data.get("raw_texts")
            assert isinstance(row_order, list)
            assert isinstance(cells, dict)
            assert raw_texts is None or isinstance(raw_texts, dict)
            self._tables[t_id] = BenchmarkTable(
                table_id=t_id,
                row_order=row_order,  # type: ignore[arg-type]
                cells=cells,  # type: ignore[arg-type]
                raw_texts=raw_texts,  # type: ignore[arg-type]
            )

    def get_table(self, table_id: str) -> BenchmarkTable:
        if table_id not in self._tables:
            raise KeyError(f"Table {table_id!r} not found in benchmark registry")
        return self._tables[table_id]

    def val(self, table_id: str, row_id: str, col_id: str) -> float | None:
        table = self.get_table(table_id)
        return table.val(row_id, col_id)

    def __getitem__(self, table_id: str) -> BenchmarkTable:
        return self.get_table(table_id)


@pytest.fixture(scope="session")
def registry() -> BenchmarkRegistry:
    """Session-scoped benchmark registry fixture."""
    return BenchmarkRegistry()


@pytest.fixture(scope="session")
def benchmark_registry() -> BenchmarkRegistry:
    """Session-scoped benchmark registry fixture alias."""
    return BenchmarkRegistry()


__all__ = [
    "BenchmarkCell",
    "BenchmarkRegistry",
    "BenchmarkRow",
    "BenchmarkTable",
    "benchmark_registry",
    "registry",
]
