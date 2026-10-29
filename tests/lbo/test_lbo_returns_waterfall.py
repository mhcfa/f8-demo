"""Comprehensive unit and benchmark verification tests for Institutional LBO Reference Exit Valuation, Equity Dilution & Contributor Returns Waterfall."""

from __future__ import annotations

import ast
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from models.lbo import (
    DEFAULT_DELIVERABLE_PATH,
    POST_CLOSE_PERIOD_KEYS,
    WATERFALL_CONTRIBUTOR_KEYS,
    compile_lbo_transaction_model,
    emit_lbo_workbook,
)
from models.lbo.assumptions import (
    DealAssumptions,
    FinancingAssumptions,
    LboAssumptions,
    get_driver_metadata_records,
)
from models.lbo.debt_sweep import SCHED_SWEEP_TRANCHE_KEYS
from tests.lbo.conftest import BenchmarkRegistry, BenchmarkTable

if TYPE_CHECKING:
    import f8

MODELS_LBO_DIR = Path("models/lbo")
ALLOWED_NUMERIC_LITERALS: frozenset[int] = frozenset(
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 365}
)
EXCEL_ERROR_TOKENS: frozenset[str] = frozenset(
    {"#REF!", "#NAME?", "#VALUE!", "#NUM!", "#N/A", "#DIV/0!"}
)
DILUTION_COLS: tuple[str, ...] = (
    "initial_investment",
    "undiluted",
    "partial_dilution",
    "full_dilution",
)
WATERFALL_COLS: tuple[str, ...] = (
    "initial_investment",
    *POST_CLOSE_PERIOD_KEYS,
    "metric_value",
)
EXIT_VALUATION_ROW_IDS: tuple[str, ...] = (
    "ebitda_annualized",
    "forward_ebitda_multiple",
    "enterprise_value_ebitda",
    "less_net_debt",
    "total_equity_value_ebitda",
    "gaap_ni_annualized",
    "forward_gaap_pe_multiple",
    "total_equity_value_gaap_pe",
    "cash_ni_annualized",
    "forward_cash_pe_multiple",
    "total_equity_value_cash_pe",
    "active_exit_equity_value",
    *(f"prepay_rate_{tk}" for tk in SCHED_SWEEP_TRANCHE_KEYS),
)


@pytest.fixture(scope="module")
def compiled_model() -> f8.CompiledModel:
    """Compile default Institutional LBO model (Financing Case 6 = LBO C, Operating Case 3 = Analyst)."""
    return compile_lbo_transaction_model()


def _assert_zero_error_cells(compiled: f8.CompiledModel) -> None:
    for table_id in ("equity_dilution", "exit_valuation", "returns_waterfall"):
        auditor = compiled.table(table_id)
        for row_id in auditor.rows:
            for col_id in auditor.measure_columns:
                val = compiled.value(table_id, row_id, col_id)
                assert val not in EXCEL_ERROR_TOKENS, (
                    f"Excel error {val!r} at ({table_id}, {row_id}, {col_id})"
                )


class TestC1AssumptionsAndZeroInlineLiterals:
    """Verify C1: Stage 3 exit valuation, dilution, and prepayment premium assumptions and AST literal gate."""

    def test_stage3_returns_assumptions_values_and_immutability(self) -> None:
        assumptions = LboAssumptions()
        deal = assumptions.deal
        fin = assumptions.financing

        timeline = assumptions.timeline

        assert deal.exit_valuation_method == 1
        assert deal.exit_year == 4
        assert deal.exit_ebitda_multiple == pytest.approx(5.0, abs=1e-12)
        assert deal.exit_pe_multiple == pytest.approx(14.0, abs=1e-12)
        assert deal.mgmt_performance_equity_pct == pytest.approx(0.005, abs=1e-12)
        assert len(timeline.returns_schedule_dates) == 11
        assert timeline.returns_schedule_dates[0] == (2022, 12, 31)
        assert timeline.returns_schedule_dates[1] == (2023, 9, 30)
        assert timeline.returns_schedule_dates[4] == (2026, 9, 30)
        assert timeline.returns_schedule_dates[-1] == (2032, 9, 30)

        assert fin.subordinated_note.equity_kicker_pct == pytest.approx(0.02, abs=1e-12)
        assert fin.preferred_a.equity_kicker_pct == pytest.approx(0.0025, abs=1e-12)
        assert fin.mezzanine.equity_kicker_pct == pytest.approx(0.0, abs=1e-12)
        assert fin.subordinated_note.prepayment_premium_schedule == (
            0.05,
            0.03,
            0.02,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
        assert fin.mezzanine.prepayment_premium_schedule == (
            0.02,
            0.02,
            0.02,
            0.02,
            0.02,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
        for tk in SCHED_SWEEP_TRANCHE_KEYS:
            if tk not in {"subordinated_note", "mezzanine"}:
                assert fin.get_tranche(tk).prepayment_premium_schedule == (0.0,) * 10

        with pytest.raises(FrozenInstanceError):
            deal.exit_ebitda_multiple = 6.0  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            fin.subordinated_note.equity_kicker_pct = 0.05  # type: ignore[misc]

    def test_stage3_returns_metadata_completeness(self) -> None:
        records = get_driver_metadata_records(LboAssumptions())
        by_name = {rec["name"]: rec for rec in records}
        expected_fields = (
            "deal.exit_valuation_method",
            "deal.exit_year",
            "deal.exit_ebitda_multiple",
            "deal.exit_pe_multiple",
            "deal.mgmt_performance_equity_pct",
            "timeline.returns_schedule_dates",
            "financing.subordinated_note.equity_kicker_pct",
            "financing.subordinated_note.prepayment_premium_schedule",
            "financing.mezzanine.prepayment_premium_schedule",
            "financing.preferred_a.equity_kicker_pct",
        )
        for field_name in expected_fields:
            assert field_name in by_name, f"Missing driver metadata record for {field_name}"
            rec = by_name[field_name]
            assert rec["rationale"] and rec["basis"] and rec["category"]
        assert len(get_driver_metadata_records(DealAssumptions())) >= 31
        assert len(get_driver_metadata_records(FinancingAssumptions())) >= 180

    def test_zero_unauthorized_numeric_literals_in_models_lbo(self) -> None:
        py_files = sorted(MODELS_LBO_DIR.glob("*.py"))
        assert len(py_files) >= 8
        for py_file in py_files:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(("f8_ingest", "f9")), (
                            f"Forbidden ingestion import {alias.name} in {py_file}:{node.lineno}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    assert not (node.module and node.module.startswith(("f8_ingest", "f9"))), (
                        f"Forbidden ingestion import {node.module} in {py_file}:{node.lineno}"
                    )
                elif (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool)
                ):
                    assert node.value in ALLOWED_NUMERIC_LITERALS, (
                        f"Forbidden inline numeric literal {node.value} in {py_file}:{node.lineno}"
                    )


class TestC2EquityDilutionAndExitValuationParity:
    """Verify C2: equity_dilution (14x4) and exit_valuation (22x10) match benchmark_returns_waterfall.json."""

    def test_equity_dilution_table_benchmark_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench: BenchmarkTable = registry.get_table("benchmark_returns_waterfall")
        alloc_rows = [r for r in bench.rows if r.id.startswith("alloc_")]
        assert len(alloc_rows) == 14

        checked = 0
        for row in alloc_rows:
            for col_id in DILUTION_COLS:
                cell = bench.get_cell(row.id, col_id)
                assert cell is not None and cell.value is not None
                actual = compiled_model.num("equity_dilution", row.id, col_id)
                assert actual == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                    f"Mismatch at (equity_dilution, {row.id}, {col_id})"
                )
                checked += 1
        assert checked == 56

    def test_exit_valuation_and_prepayment_rates_benchmark_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench: BenchmarkTable = registry.get_table("benchmark_returns_waterfall")
        assert len(EXIT_VALUATION_ROW_IDS) == 22
        assert tuple(compiled_model.table("exit_valuation").measure_columns) == (
            "pf_close",
            *POST_CLOSE_PERIOD_KEYS,
        )

        checked = 0
        for row_id in EXIT_VALUATION_ROW_IDS:
            assert compiled_model.value("exit_valuation", row_id, "pf_close") is None
            for col_id in POST_CLOSE_PERIOD_KEYS:
                cell = bench.get_cell(row_id, col_id)
                assert cell is not None and cell.value is not None
                actual = compiled_model.num("exit_valuation", row_id, col_id)
                assert actual == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                    f"Mismatch at (exit_valuation, {row_id}, {col_id})"
                )
                checked += 1
        assert checked == 220


class TestC3ReturnsWaterfallParity:
    """Verify C3: returns_waterfall (44 contributor rows across 6 participants) matches benchmark_returns_waterfall.json."""

    def test_returns_waterfall_all_44_contributor_rows_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench: BenchmarkTable = registry.get_table("benchmark_returns_waterfall")
        waterfall_rows = [
            r
            for r in bench.rows
            if not r.id.startswith("alloc_") and r.id not in EXIT_VALUATION_ROW_IDS
        ]
        assert len(waterfall_rows) == 44

        checked_non_null = 0
        for row in waterfall_rows:
            for col_id in WATERFALL_COLS:
                cell = bench.get_cell(row.id, col_id)
                actual = compiled_model.value("returns_waterfall", row.id, col_id)
                if cell is None:
                    assert actual is None, (
                        f"Expected None at (returns_waterfall, {row.id}, {col_id}), got {actual!r}"
                    )
                elif cell.value is None:
                    assert actual == cell.raw_text, (
                        f"Expected {cell.raw_text!r} at ({row.id}, {col_id}), got {actual!r}"
                    )
                    checked_non_null += 1
                elif row.id.endswith("_irr"):
                    actual_num = compiled_model.num("returns_waterfall", row.id, col_id)
                    assert actual_num == pytest.approx(float(cell.value), abs=1e-8), (
                        f"IRR mismatch at {row.id}: {actual_num} vs {cell.value}"
                    )
                    checked_non_null += 1
                else:
                    actual_num = compiled_model.num("returns_waterfall", row.id, col_id)
                    assert actual_num == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                        f"Cash flow/MoIC mismatch at ({row.id}, {col_id}): {actual_num} vs {cell.value}"
                    )
                    checked_non_null += 1
        assert checked_non_null == 284


class TestC4OwnershipAndExitParticipationConservation:
    """Verify C4: ownership conservation, exit equity participation conservation, and zero errors across scenarios."""

    @pytest.mark.parametrize("exit_method", [1, 2, 3])
    @pytest.mark.parametrize("exit_year", [2, 3, 4, 5, 6, 7, 8, 9, 10])
    def test_exit_methods_and_exit_years_conserve_ownership_and_exit_equity(
        self, exit_method: int, exit_year: int
    ) -> None:
        assumptions = LboAssumptions(
            deal=replace(
                DealAssumptions(),
                exit_valuation_method=exit_method,
                exit_year=exit_year,
            )
        )
        compiled = compile_lbo_transaction_model(assumptions=assumptions)
        _assert_zero_error_cells(compiled)

        for dil_col in ("undiluted", "partial_dilution", "full_dilution"):
            assert compiled.num("equity_dilution", "alloc_total", dil_col) == pytest.approx(
                1.0, abs=1e-12
            )

        exit_col = POST_CLOSE_PERIOD_KEYS[exit_year - 1]
        expected_method_row = {
            1: "total_equity_value_ebitda",
            2: "total_equity_value_gaap_pe",
            3: "total_equity_value_cash_pe",
        }[exit_method]
        active_eq_val = compiled.num("exit_valuation", "active_exit_equity_value", exit_col)
        assert active_eq_val == pytest.approx(
            compiled.num("exit_valuation", expected_method_row, exit_col),
            rel=1e-12,
            abs=1e-12,
        )

        total_participation = sum(
            compiled.num("returns_waterfall", f"{ck}_equity_participation", exit_col)
            for ck in WATERFALL_CONTRIBUTOR_KEYS
        )
        assert total_participation == pytest.approx(active_eq_val, rel=1e-11, abs=1e-11)

        for p_idx, col_id in enumerate(POST_CLOSE_PERIOD_KEYS, start=1):
            if p_idx != exit_year:
                non_exit_part = sum(
                    compiled.num("returns_waterfall", f"{ck}_equity_participation", col_id)
                    for ck in WATERFALL_CONTRIBUTOR_KEYS
                )
                assert non_exit_part == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.parametrize("financing_case", [1, 2, 3, 4, 5, 6])
    @pytest.mark.parametrize("operating_case", [1, 2, 3, 4])
    def test_financing_and_operating_scenarios_preserve_returns_invariants(
        self, financing_case: int, operating_case: int
    ) -> None:
        assumptions = LboAssumptions(
            deal=replace(
                DealAssumptions(),
                active_financing_case=financing_case,
                active_operating_case=operating_case,
            )
        )
        compiled = compile_lbo_transaction_model(assumptions=assumptions)
        _assert_zero_error_cells(compiled)

        expected_total_ownership = 1.0 if financing_case in {4, 5, 6} else 0.0
        for dil_col in ("undiluted", "partial_dilution", "full_dilution"):
            assert compiled.num("equity_dilution", "alloc_total", dil_col) == pytest.approx(
                expected_total_ownership, abs=1e-12
            )

        exit_col = POST_CLOSE_PERIOD_KEYS[assumptions.deal.exit_year - 1]
        active_eq_val = compiled.num("exit_valuation", "active_exit_equity_value", exit_col)
        total_participation = sum(
            compiled.num("returns_waterfall", f"{ck}_equity_participation", exit_col)
            for ck in WATERFALL_CONTRIBUTOR_KEYS
        )
        assert total_participation == pytest.approx(
            active_eq_val * expected_total_ownership, rel=1e-11, abs=1e-11
        )


class TestC5DeliverableWorkbookEmission:
    """Verify C5: emit_lbo_workbook saves deliverables/lbo_model.xlsx with all 4 sheets."""

    def test_emit_lbo_workbook_creates_valid_four_sheet_xlsx(self, tmp_path: Path) -> None:
        tmp_out = emit_lbo_workbook(output_path=tmp_path / "lbo_model.xlsx")
        assert tmp_out.exists()
        assert tmp_out.stat().st_size > 50_000

        default_out = emit_lbo_workbook()
        assert default_out == DEFAULT_DELIVERABLE_PATH
        assert default_out.exists()
        assert default_out.stat().st_size > 50_000

        with zipfile.ZipFile(default_out, "r") as zf:
            wb_xml = zf.read("xl/workbook.xml")
        root = ET.fromstring(wb_xml)
        ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet_names = [
            s.attrib["name"] for s in root.findall(".//main:sheets/main:sheet", namespaces=ns)
        ]
        assert sheet_names == [
            "Executive Dashboard",
            "Transaction & PPA",
            "LBO Model",
            "Valuation & Returns",
        ]
