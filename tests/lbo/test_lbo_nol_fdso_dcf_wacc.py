"""Comprehensive unit, benchmark parity, and stress verification tests for Institutional LBO Reference Section 382 NOL, Corporate AMT, Convertible Dilution / FDSO, and Decomposed WACC / CAPM / DCF / Sensitivity schedules."""

from __future__ import annotations

import ast
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import TYPE_CHECKING

import f8
import pytest

from models.lbo import (
    DEFAULT_DELIVERABLE_PATH,
    EXIT_PERIOD_KEY,
    POST_CLOSE_PERIOD_KEYS,
    STUB_PERIOD_KEY,
    TIMELINE_COL_KEYS,
    build_convertible_fdso_schedule,
    build_dcf_schedule,
    build_dcf_sensitivity,
    build_lbo_transaction_model,
    build_nol_amt_schedule,
    build_pre_deal_capm_schedule,
    build_wacc_schedule,
    compile_lbo_transaction_model,
    emit_lbo_workbook,
)
from models.lbo.assumptions import (
    DealAssumptions,
    FinancingAssumptions,
    LboAssumptions,
    get_driver_metadata_records,
)
from models.lbo.dcf_wacc import (
    DCF_SCHEDULE_COL_KEYS,
    DCF_SENSITIVITY_COL_KEYS,
    PRE_DEAL_CAPM_COL_KEYS,
    WACC_COL_KEYS,
)
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
LBO_MODEL_SHEET_TABLES: tuple[str, ...] = (
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "working_capital_schedule",
    "debt_sweep_schedule",
    "da_schedule",
    "nol_amt_schedule",
    "convertible_fdso_schedule",
    "credit_stats",
    "operating_schedule",
)
ALL_MODEL_TABLES: tuple[str, ...] = (
    "dashboard_sources_uses",
    "dashboard_entry_valuation",
    "dashboard_implied_multiples",
    "dashboard_returns_summary",
    "dashboard_credit_profile",
    "dashboard_integrity_checks",
    "option_tranches",
    "valuation_and_fdso",
    "sources_uses",
    "tranche_fees_oid",
    "ppa_schedule",
    "transaction_bs",
    *LBO_MODEL_SHEET_TABLES,
    "dcf_schedule",
    "exit_valuation",
    "returns_waterfall",
    "equity_dilution",
    "pre_deal_capm_schedule",
    "wacc_schedule",
    "dcf_sensitivity",
)


@pytest.fixture(scope="module")
def compiled_model() -> f8.CompiledModel:
    """Compile default Institutional LBO model (Financing Case 6 = LBO C, Operating Case 3 = Analyst)."""
    return compile_lbo_transaction_model()


def _assert_zero_error_cells_in_tables(
    compiled: f8.CompiledModel, table_ids: tuple[str, ...]
) -> None:
    for table_id in table_ids:
        auditor = compiled.table(table_id)
        for row_id in auditor.rows:
            for col_id in auditor.measure_columns:
                val = compiled.value(table_id, row_id, col_id)
                assert val not in EXCEL_ERROR_TOKENS, (
                    f"Excel error {val!r} at ({table_id}, {row_id}, {col_id})"
                )


class TestC1WaccDcfAssumptionsAndAstHygiene:
    """Verify C1: WACC/DCF driver assumptions, metadata completeness, and AST literal/import hygiene."""

    def test_wacc_dcf_assumptions_defaults_and_immutability(self) -> None:
        assumptions = LboAssumptions()
        deal = assumptions.deal

        assert deal.pre_tx_levered_beta == pytest.approx(0.86, abs=1e-12)
        assert deal.risk_free_rate == pytest.approx(0.045, abs=1e-12)
        assert deal.market_risk_premium == pytest.approx(0.04, abs=1e-12)
        assert deal.manual_wacc == pytest.approx(0.12, abs=1e-12)
        assert deal.wacc_selector == 1
        assert deal.dcf_wacc_step == pytest.approx(0.01, abs=1e-12)
        assert deal.dcf_terminal_ebitda_multiples == (4.5, 5.0, 5.5)
        assert deal.dcf_terminal_growth_rates == (0.0, 0.005, 0.01)

        with pytest.raises(FrozenInstanceError):
            deal.manual_wacc = 0.10  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            deal.wacc_selector = 2  # type: ignore[misc]

    def test_wacc_dcf_driver_metadata_completeness(self) -> None:
        records = get_driver_metadata_records(LboAssumptions())
        by_name = {rec["name"]: rec for rec in records}
        expected_fields = (
            "deal.pre_tx_levered_beta",
            "deal.risk_free_rate",
            "deal.market_risk_premium",
            "deal.manual_wacc",
            "deal.wacc_selector",
            "deal.dcf_wacc_step",
            "deal.dcf_terminal_ebitda_multiples",
            "deal.dcf_terminal_growth_rates",
        )
        for field_name in expected_fields:
            assert field_name in by_name, f"Missing driver metadata record for {field_name}"
            rec = by_name[field_name]
            assert rec["rationale"] and rec["basis"]
            assert rec["category"] == "wacc_dcf"
        assert len(get_driver_metadata_records(DealAssumptions())) >= 40

    def test_zero_unauthorized_literals_and_zero_ingestion_imports(self) -> None:
        py_files = sorted(MODELS_LBO_DIR.glob("*.py"))
        assert len(py_files) >= 10
        for py_file in py_files:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool)
                ):
                    assert node.value in ALLOWED_NUMERIC_LITERALS, (
                        f"Forbidden inline numeric literal {node.value} in {py_file}:{node.lineno}"
                    )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(("f8_ingest", "f9")), (
                            f"Forbidden ingestion import {alias.name} in {py_file}:{node.lineno}"
                        )
                if isinstance(node, ast.ImportFrom) and node.module is not None:
                    assert not node.module.startswith(("f8_ingest", "f9")), (
                        f"Forbidden ingestion import {node.module} in {py_file}:{node.lineno}"
                    )
                if isinstance(node, ast.JoinedStr):
                    for val in node.values:
                        if isinstance(val, ast.FormattedValue) and isinstance(
                            val.value, ast.Constant
                        ):
                            assert not isinstance(val.value.value, (int, float)), (
                                f"Forbidden numeric literal interpolation in f-string in {py_file}:{node.lineno}"
                            )

    def test_standalone_builder_invocation_support(self) -> None:
        model = f8.Model("Test")
        sheet = model.add_sheet("Test")
        assumptions = LboAssumptions()
        nol_tbl = build_nol_amt_schedule(sheet, assumptions)
        conv_tbl = build_convertible_fdso_schedule(sheet, assumptions)
        capm_tbl = build_pre_deal_capm_schedule(sheet, assumptions)
        wacc_tbl = build_wacc_schedule(sheet, assumptions)
        dcf_tbl = build_dcf_schedule(sheet, assumptions)
        sens_tbl = build_dcf_sensitivity(sheet, assumptions)
        assert nol_tbl is not None
        assert conv_tbl is not None
        assert capm_tbl is not None
        assert wacc_tbl is not None
        assert dcf_tbl is not None
        assert sens_tbl is not None

    def test_c1_expanding_slice_formulas_and_removed_unrolled_tuples(
        self, compiled_model: f8.CompiledModel
    ) -> None:
        import models.lbo.debt_sweep as debt_sweep_mod
        import models.lbo.operating_da as operating_da_mod

        assert not hasattr(debt_sweep_mod, "SCHED_AMORT_POST_CLOSE_EXPRS")
        assert not hasattr(operating_da_mod, "FC_AMORT_POST_CLOSE_EXPRS")
        assert not hasattr(operating_da_mod, "CAPEX_COHORT_SUBSEQUENT_COL_EXPRS")
        assert not hasattr(operating_da_mod, "WRITEUP_SCHEDULE_POST_CLOSE_EXPRS")

        for _tk, _opt_r, _opt_lbl, active_opt_expr in debt_sweep_mod.SWEEP_OPT_NON_REVOLVER_SPECS:
            assert (
                'SUM(debt_sweep_schedule["sweep_opt_revolver"..row.prev, @col])' in active_opt_expr
            )

        for col_id in POST_CLOSE_PERIOD_KEYS[1:]:
            sched_cell = compiled_model.inspect_cell(
                "debt_sweep_schedule", "debt_sched_amort_term_loan_a", col_id
            )
            assert f'"{STUB_PERIOD_KEY}"..col.prev' in (sched_cell["formula_expr"] or "")

            fc_cell = compiled_model.inspect_cell("da_schedule", "da_amort_fc_term_loan_a", col_id)
            assert f'"{STUB_PERIOD_KEY}"..col.prev' in (fc_cell["formula_expr"] or "")

            coh_cell = compiled_model.inspect_cell("da_schedule", "da_capex_cohort_1", col_id)
            assert f'"{STUB_PERIOD_KEY}"..col.prev' in (coh_cell["formula_expr"] or "")

            ppe_cell = compiled_model.inspect_cell("da_schedule", "da_ppe_writeup_schedule", col_id)
            assert f'"{STUB_PERIOD_KEY}"..col.prev' in (ppe_cell["formula_expr"] or "")

            int_cell = compiled_model.inspect_cell(
                "da_schedule", "da_intangibles_writeup_schedule", col_id
            )
            assert f'"{STUB_PERIOD_KEY}"..col.prev' in (int_cell["formula_expr"] or "")

        opt_cell = compiled_model.inspect_cell(
            "debt_sweep_schedule", "sweep_opt_term_loan_a", STUB_PERIOD_KEY
        )
        assert '"sweep_opt_revolver"..row.prev' in (opt_cell["formula_expr"] or "")

    def test_c2_batch_set_cells_and_zero_for_loop_set_cell(self) -> None:
        py_files = sorted(MODELS_LBO_DIR.glob("*.py"))
        files_with_set_cells: set[str] = set()
        for py_file in py_files:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "set_cells"
                ):
                    files_with_set_cells.add(py_file.name)
                if isinstance(node, ast.For):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                            assert child.func.attr != "set_cell", (
                                f"Found set_cell inside for-loop in {py_file}:{child.lineno}"
                            )
        expected_set_cells_modules = {
            "cap_table.py",
            "dashboard.py",
            "dcf_wacc.py",
            "debt_sweep.py",
            "operating_da.py",
            "returns.py",
            "statements.py",
            "tax_dilution.py",
            "transaction.py",
        }
        assert expected_set_cells_modules.issubset(files_with_set_cells)


class TestC2NolAmtScheduleParityAndStress:
    """Verify C2: nol_amt_schedule (55x18) matches benchmark_tax_nol_amt_fdso.json and responds dynamically to NOL/AMT stress."""

    def test_nol_amt_schedule_full_benchmark_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench: BenchmarkTable = registry.get_table("benchmark_tax_nol_amt_fdso")
        nol_rows = bench.rows[:55]
        assert len(nol_rows) == 55
        assert nol_rows[0].id == "federal_tax_rate"
        assert nol_rows[-1].id == "amt_credit_cf_end"

        checked_total = 0
        checked_non_null = 0
        for row in nol_rows:
            for col_id in TIMELINE_COL_KEYS:
                cell = bench.get_cell(row.id, col_id)
                actual_val = compiled_model.value("nol_amt_schedule", row.id, col_id)
                if cell is None or cell.value is None:
                    assert actual_val is None, (
                        f"Expected None at (nol_amt_schedule, {row.id}, {col_id}), got {actual_val!r}"
                    )
                else:
                    actual_num = compiled_model.num("nol_amt_schedule", row.id, col_id)
                    assert actual_num == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                        f"Mismatch at (nol_amt_schedule, {row.id}, {col_id}): {actual_num} vs {cell.value}"
                    )
                    checked_non_null += 1
                checked_total += 1
        assert checked_total == 55 * 18
        assert checked_non_null == 790

    def test_lbo_model_sheet_tables_and_nol_amt_ties(
        self, compiled_model: f8.CompiledModel
    ) -> None:
        for table_id in LBO_MODEL_SHEET_TABLES:
            auditor = compiled_model.table(table_id)
            assert tuple(auditor.measure_columns) == TIMELINE_COL_KEYS

        for col_id in POST_CLOSE_PERIOD_KEYS:
            assert compiled_model.num(
                "income_statement", "is_tax_provision", col_id
            ) == pytest.approx(
                compiled_model.num("nol_amt_schedule", "tax_book_tax_expense", col_id),
                rel=1e-12,
                abs=1e-12,
            )
            assert compiled_model.num("balance_sheet", "bs_net_dtl", col_id) == pytest.approx(
                compiled_model.num("nol_amt_schedule", "tax_net_dtl_end", col_id),
                rel=1e-12,
                abs=1e-12,
            )
        assert compiled_model.num("balance_sheet", "bs_net_dtl", "pf_close") == pytest.approx(
            compiled_model.num("nol_amt_schedule", "tax_net_dtl_end", "pf_close"),
            rel=1e-12,
            abs=1e-12,
        )

    def test_nol_sec382_and_amt_credit_stress(self) -> None:
        stressed = LboAssumptions(
            deal=replace(
                DealAssumptions(),
                existing_nol=100.0,
                amt_credit_carryforward=15.0,
            )
        )
        compiled = compile_lbo_transaction_model(assumptions=stressed)
        _assert_zero_error_cells_in_tables(
            compiled, ("nol_amt_schedule", "income_statement", "balance_sheet")
        )

        # Opening unencumbered NOL is 100.0 at MRQ, used during MRQ+1..MRQ+3 pre-close, and remaining converts to encumbered NOL at pf_close
        assert compiled.num("nol_amt_schedule", "unencumbered_nol_end", "mrq") == pytest.approx(
            100.0, abs=1e-9
        )
        standalone_nol = compiled.num(
            "nol_amt_schedule", "unencumbered_nol_end", "standalone_close"
        )
        assert 0.0 < standalone_nol < 100.0
        assert compiled.num("nol_amt_schedule", "encumbered_nol_end", "pf_close") == pytest.approx(
            standalone_nol, abs=1e-9
        )
        assert compiled.num(
            "nol_amt_schedule", "unencumbered_nol_end", "pf_close"
        ) == pytest.approx(0.0, abs=1e-9)

        # Post-close Section 382 limit and encumbered NOL usage
        total_post_close_nol_used = sum(
            compiled.num("nol_amt_schedule", "encumbered_nol_used", col_id)
            for col_id in POST_CLOSE_PERIOD_KEYS
        )
        assert total_post_close_nol_used < 0.0

        # AMT credit carryforward is utilized in profitable post-close years
        assert compiled.num("nol_amt_schedule", "amt_credit_cf_end", "pf_close") == pytest.approx(
            compiled.num("nol_amt_schedule", "amt_credit_cf_end", "standalone_close"),
            abs=1e-9,
        )
        total_amt_credit_used = sum(
            compiled.num("nol_amt_schedule", "amt_credit_cf_used", col_id)
            for col_id in POST_CLOSE_PERIOD_KEYS
        )
        assert total_amt_credit_used < 0.0

        # Balance sheet still balances across all post-close periods
        for col_id in ("pf_close", *POST_CLOSE_PERIOD_KEYS):
            assert compiled.num("balance_sheet", "bs_balance_check", col_id) == pytest.approx(
                0.0, abs=1e-9
            )


class TestC3ConvertibleFdsoScheduleParityAndStress:
    """Verify C3: convertible_fdso_schedule (49x18) matches benchmark_tax_nol_amt_fdso.json and responds dynamically to convertible dilution stress."""

    def test_convertible_fdso_schedule_full_benchmark_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench: BenchmarkTable = registry.get_table("benchmark_tax_nol_amt_fdso")
        conv_rows = bench.rows[55:]
        assert len(conv_rows) == 49
        assert conv_rows[0].id == "conv_face_legacy_debt"
        assert conv_rows[-1].id == "fdso"

        checked_total = 0
        checked_non_null = 0
        for row in conv_rows:
            for col_id in TIMELINE_COL_KEYS:
                cell = bench.get_cell(row.id, col_id)
                actual_val = compiled_model.value("convertible_fdso_schedule", row.id, col_id)
                if cell is None or cell.value is None:
                    assert actual_val is None, (
                        f"Expected None at (convertible_fdso_schedule, {row.id}, {col_id}), got {actual_val!r}"
                    )
                else:
                    actual_num = compiled_model.num("convertible_fdso_schedule", row.id, col_id)
                    assert actual_num == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                        f"Mismatch at (convertible_fdso_schedule, {row.id}, {col_id}): {actual_num} vs {cell.value}"
                    )
                    checked_non_null += 1
                checked_total += 1
        assert checked_total == 49 * 18
        assert checked_non_null == 791

    def test_dilutive_convertible_tranche_stress(self) -> None:
        fin = FinancingAssumptions()
        stressed_sub = replace(fin.subordinated_note, conversion_price=10.0)
        stressed = LboAssumptions(financing=replace(fin, subordinated_note=stressed_sub))
        compiled = compile_lbo_transaction_model(assumptions=stressed)
        _assert_zero_error_cells_in_tables(compiled, ("convertible_fdso_schedule",))

        # Subordinated note has $50M face at close in Case 6 -> 5.0M shares if converted
        assert compiled.num(
            "convertible_fdso_schedule", "conv_shares_subordinated_note", "pf_close"
        ) == pytest.approx(5.0, abs=1e-9)

        # In profitable years while subordinated note is outstanding (e.g. exit year), Basic EPS > marginal conversion EPS so conversion at $10 is dilutive
        basic_eps_exit = compiled.num("convertible_fdso_schedule", "basic_eps", EXIT_PERIOD_KEY)
        if_conv_eps_exit = compiled.num(
            "convertible_fdso_schedule", "eps_if_converted_subordinated_note", EXIT_PERIOD_KEY
        )
        assert if_conv_eps_exit < basic_eps_exit
        assert (
            compiled.num(
                "convertible_fdso_schedule",
                "is_conversion_dilutive_subordinated_note",
                EXIT_PERIOD_KEY,
            )
            == 1
        )
        conv_shares_exit = compiled.num(
            "convertible_fdso_schedule", "convertible_securities_shares", EXIT_PERIOD_KEY
        )
        bso_exit = compiled.num("convertible_fdso_schedule", "bso", EXIT_PERIOD_KEY)
        fdso_exit = compiled.num("convertible_fdso_schedule", "fdso", EXIT_PERIOD_KEY)
        assert conv_shares_exit == pytest.approx(5.0, abs=1e-9)
        assert fdso_exit == pytest.approx(bso_exit + conv_shares_exit, abs=1e-9)


class TestC4DcfWaccScheduleParityAndStress:
    """Verify C4: 4-table decomposition (pre_deal_capm_schedule, wacc_schedule, dcf_schedule, dcf_sensitivity) matches benchmark_dcf_wacc.json and preserves XNPV parity under WACC selector stress."""

    def test_dcf_wacc_four_table_dimensions_and_full_benchmark_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        capm_auditor = compiled_model.table("pre_deal_capm_schedule")
        wacc_auditor = compiled_model.table("wacc_schedule")
        dcf_auditor = compiled_model.table("dcf_schedule")
        sens_auditor = compiled_model.table("dcf_sensitivity")

        assert len(capm_auditor.rows) == 17
        assert tuple(capm_auditor.measure_columns) == PRE_DEAL_CAPM_COL_KEYS
        assert len(wacc_auditor.rows) == 17
        assert tuple(wacc_auditor.measure_columns) == WACC_COL_KEYS
        assert len(dcf_auditor.rows) == 18
        assert tuple(dcf_auditor.measure_columns) == DCF_SCHEDULE_COL_KEYS
        assert len(sens_auditor.rows) == 27
        assert tuple(sens_auditor.measure_columns) == DCF_SENSITIVITY_COL_KEYS

        bench: BenchmarkTable = registry.get_table("benchmark_dcf_wacc")
        assert len(bench.rows) == 85
        non_opt_rows = [r for r in bench.rows if not r.id.startswith("wacc_option_tranche_")]
        assert len(non_opt_rows) == 75

        dcf_row_ids = set(dcf_auditor.rows)
        sens_row_ids = set(sens_auditor.rows)
        capm_row_ids = set(capm_auditor.rows)
        wacc_row_ids = set(wacc_auditor.rows)

        checked_total = 0
        checked_direct_non_null = 0
        checked_benchmark_non_null = 0

        for row in non_opt_rows:
            if row.id in dcf_row_ids:
                target_table = "dcf_schedule"
                target_cols = DCF_SCHEDULE_COL_KEYS
            elif row.id in sens_row_ids:
                target_table = "dcf_sensitivity"
                target_cols = DCF_SENSITIVITY_COL_KEYS
            elif row.id in capm_row_ids:
                target_table = "pre_deal_capm_schedule"
                target_cols = PRE_DEAL_CAPM_COL_KEYS
            else:
                assert row.id in wacc_row_ids, f"Unmapped benchmark row {row.id}"
                target_table = "wacc_schedule"
                target_cols = WACC_COL_KEYS

            for col_id in target_cols:
                if row.id == "wacc":
                    continue
                cell = bench.get_cell(row.id, col_id)
                actual_val = compiled_model.value(target_table, row.id, col_id)
                if cell is None or cell.value is None:
                    assert actual_val is None, (
                        f"Expected None at ({target_table}, {row.id}, {col_id}), got {actual_val!r}"
                    )
                else:
                    actual_num = compiled_model.num(target_table, row.id, col_id)
                    assert actual_num == pytest.approx(float(cell.value), rel=1e-11, abs=1e-11), (
                        f"Mismatch at ({target_table}, {row.id}, {col_id}): {actual_num} vs {cell.value}"
                    )
                    checked_direct_non_null += 1
                    checked_benchmark_non_null += 1
                checked_total += 1

            if row.id == "wacc":
                # Benchmark stores WACC in metric_value / pf_close; in wacc_schedule it is placed in wacc_rate
                bench_wacc = bench.get_cell("wacc", "metric_value")
                assert bench_wacc is not None and bench_wacc.value is not None
                actual_wacc = compiled_model.num("wacc_schedule", "wacc", "wacc_rate")
                assert actual_wacc == pytest.approx(float(bench_wacc.value), rel=1e-11, abs=1e-11)
                expected_total_cap = sum(
                    compiled_model.num("wacc_schedule", r_id, "wacc_amount")
                    for r_id in wacc_auditor.rows
                    if r_id.startswith("wacc_cap_")
                )
                assert compiled_model.num("wacc_schedule", "wacc", "wacc_amount") == pytest.approx(
                    expected_total_cap, rel=1e-11, abs=1e-11
                )
                assert compiled_model.value("wacc_schedule", "wacc", "wacc_taxability") is None
                checked_direct_non_null += 1
                checked_benchmark_non_null += 1
                checked_total += 3

            # Also verify legacy cross-table mirror cells in benchmark_dcf_wacc.json
            for col_id, cell_obj in row.cells.items():
                if cell_obj.value is None or col_id in target_cols or col_id == "sens_col_3":
                    continue
                if row.id == "wacc":
                    continue
                canonical_col = "pf_close" if target_table == "dcf_schedule" else "metric_value"
                actual_num = compiled_model.num(target_table, row.id, canonical_col)
                assert actual_num == pytest.approx(float(cell_obj.value), rel=1e-11, abs=1e-11)
                checked_benchmark_non_null += 1

        assert checked_total == 361
        assert checked_direct_non_null == 278
        assert checked_benchmark_non_null == 282

        # Verify explicit driver rows on wacc_schedule and dcf_sensitivity
        assert compiled_model.num("wacc_schedule", "manual_wacc", "wacc_rate") == pytest.approx(
            0.12, abs=1e-12
        )
        assert compiled_model.num("wacc_schedule", "wacc_selector", "wacc_rate") == pytest.approx(
            1.0, abs=1e-12
        )
        assert compiled_model.num("wacc_schedule", "active_wacc", "wacc_rate") == pytest.approx(
            0.12, abs=1e-12
        )
        assert compiled_model.num("dcf_sensitivity", "wacc_step", "discount_rate") == pytest.approx(
            0.01, abs=1e-12
        )

        # Spot-check headline valuation and WACC anchors
        assert compiled_model.num(
            "dcf_schedule", "dcf_xnpv_ebitda_multiple", "pf_close"
        ) == pytest.approx(771.7097476029089, rel=1e-9, abs=1e-9)
        assert compiled_model.num(
            "dcf_schedule", "dcf_xnpv_ebitda_multiple_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)
        assert compiled_model.num(
            "dcf_schedule", "dcf_xnpv_perpetuity_growth", "pf_close"
        ) == pytest.approx(762.964034839734, rel=1e-9, abs=1e-9)
        assert compiled_model.num(
            "dcf_schedule", "dcf_xnpv_perpetuity_growth_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)
        assert compiled_model.num(
            "pre_deal_capm_schedule", "wacc_capm_cost_of_equity", "metric_value"
        ) == pytest.approx(0.07753619856832258, rel=1e-9, abs=1e-9)
        assert compiled_model.num("wacc_schedule", "wacc", "wacc_rate") == pytest.approx(
            0.07312407887002721, rel=1e-9, abs=1e-9
        )

    def test_wacc_selector_calculated_mode_stress(self) -> None:
        stressed = LboAssumptions(deal=replace(DealAssumptions(), wacc_selector=2))
        compiled = compile_lbo_transaction_model(assumptions=stressed)
        _assert_zero_error_cells_in_tables(
            compiled,
            (
                "pre_deal_capm_schedule",
                "wacc_schedule",
                "dcf_schedule",
                "dcf_sensitivity",
            ),
        )

        calc_wacc = compiled.num("wacc_schedule", "wacc", "wacc_rate")
        assert calc_wacc == pytest.approx(0.07312407887002721, rel=1e-9, abs=1e-9)
        assert compiled.num("wacc_schedule", "active_wacc", "wacc_rate") == pytest.approx(
            calc_wacc, rel=1e-12, abs=1e-12
        )
        assert compiled.num(
            "dcf_sensitivity", "sens_mult_ev_wacc_12", "discount_rate"
        ) == pytest.approx(calc_wacc, rel=1e-12, abs=1e-12)
        assert compiled.num(
            "dcf_sensitivity", "sens_mult_ev_wacc_11", "discount_rate"
        ) == pytest.approx(calc_wacc - 0.01, rel=1e-12, abs=1e-12)
        assert compiled.num(
            "dcf_sensitivity", "sens_mult_ev_wacc_13", "discount_rate"
        ) == pytest.approx(calc_wacc + 0.01, rel=1e-12, abs=1e-12)

        # Lower discount rate increases enterprise value monotonically under both terminal methods
        assert (
            compiled.num("dcf_sensitivity", "sens_mult_ev_wacc_11", "sens_col_2")
            > compiled.num("dcf_sensitivity", "sens_mult_ev_wacc_12", "sens_col_2")
            > compiled.num("dcf_sensitivity", "sens_mult_ev_wacc_13", "sens_col_2")
        )
        assert (
            compiled.num("dcf_sensitivity", "sens_perp_ev_wacc_11", "sens_col_2")
            > compiled.num("dcf_sensitivity", "sens_perp_ev_wacc_12", "sens_col_2")
            > compiled.num("dcf_sensitivity", "sens_perp_ev_wacc_13", "sens_col_2")
        )
        assert (
            compiled.num("dcf_schedule", "dcf_xnpv_ebitda_multiple", "pf_close") > 771.7097476029089
        )
        assert (
            compiled.num("dcf_schedule", "dcf_xnpv_perpetuity_growth", "pf_close")
            > 762.964034839734
        )

        # XNPV vs fractional-year discounting check still rounds to 0.0
        assert compiled.num(
            "dcf_schedule", "dcf_xnpv_ebitda_multiple_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)
        assert compiled.num(
            "dcf_schedule", "dcf_xnpv_perpetuity_growth_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)

    def test_valuation_returns_spatial_layout(self, compiled_model: f8.CompiledModel) -> None:
        """Verify C2, C3, C4: Valuation & Returns vertical stacking, standard timeline width on Col H, and bounds."""
        raw_model = build_lbo_transaction_model()
        vr_sheet = raw_model.get_sheet("Valuation & Returns")

        expected_order = [
            "dcf_schedule",
            "exit_valuation",
            "returns_waterfall",
            "equity_dilution",
            "pre_deal_capm_schedule",
            "wacc_schedule",
            "dcf_sensitivity",
        ]
        assert [t.id for t in vr_sheet.tables] == expected_order

        # Verify all tables are vertically stacked (no right_of offsets)
        for t in vr_sheet.tables:
            assert t.right_of is None

        sh = compiled_model.inspect_sheet("Valuation & Returns")

        # Verify Column H (physical 0-indexed column 7, 1-indexed column 8) is standard timeline width (~12.71), no longer ~50.71
        assert sh["col_widths"][7] == pytest.approx(12.0, abs=0.5)

        cols_by_table: dict[str, set[int]] = {}
        for row in sh["rows"]:
            for cell in row["cells"]:
                tid = cell.get("table_id")
                if tid:
                    cols_by_table.setdefault(tid, set()).add(cell["physical_col"])

        # All tables share Column B (physical column index 1) as their row descriptor axis
        for tid in expected_order:
            assert min(cols_by_table[tid]) == 1

        # Check bounds for all tables on Valuation & Returns
        t_dcf = compiled_model.table("dcf_schedule")
        t_exit = compiled_model.table("exit_valuation")
        t_ret = compiled_model.table("returns_waterfall")
        t_dil = compiled_model.table("equity_dilution")
        t_capm = compiled_model.table("pre_deal_capm_schedule")
        t_wacc = compiled_model.table("wacc_schedule")
        t_sens = compiled_model.table("dcf_sensitivity")

        assert t_dcf.address(t_dcf.rows[0], t_dcf.columns[0]) == "B9"
        assert t_dcf.address(t_dcf.rows[-1], t_dcf.columns[-1]) == "M30"
        assert t_exit.address(t_exit.rows[0], t_exit.columns[0]) == "B39"
        assert t_exit.address(t_exit.rows[-1], t_exit.columns[-1]) == "M60"
        assert t_ret.address(t_ret.rows[0], t_ret.columns[0]) == "B69"
        assert t_ret.address(t_ret.rows[-1], t_ret.columns[-1]) == "N115"
        assert t_dil.address(t_dil.rows[0], t_dil.columns[0]) == "B125"
        assert t_dil.address(t_dil.rows[-1], t_dil.columns[-1]) == "F138"
        assert t_capm.address(t_capm.rows[0], t_capm.columns[0]) == "B147"
        assert t_capm.address(t_capm.rows[-1], t_capm.columns[-1]) == "C165"
        assert t_wacc.address(t_wacc.rows[0], t_wacc.columns[0]) == "B175"
        assert t_wacc.address(t_wacc.rows[-1], t_wacc.columns[-1]) == "E193"
        assert t_sens.address(t_sens.rows[0], t_sens.columns[0]) == "B203"
        assert t_sens.address(t_sens.rows[-1], t_sens.columns[-1]) == "F245"


class TestC5EndToEndCompilationAndWorkbookEmission:
    """Verify C5: full 29-table model compiles cleanly across scenarios and emits 4-sheet .xlsx deliverable."""

    @pytest.mark.parametrize("financing_case", [1, 2, 3, 4, 5, 6])
    @pytest.mark.parametrize("operating_case", [1, 2, 3, 4])
    def test_all_29_tables_compile_without_error_across_scenarios(
        self, financing_case: int, operating_case: int
    ) -> None:
        assert len(ALL_MODEL_TABLES) == 29
        assumptions = LboAssumptions(
            deal=replace(
                DealAssumptions(),
                active_financing_case=financing_case,
                active_operating_case=operating_case,
            )
        )
        compiled = compile_lbo_transaction_model(assumptions=assumptions)
        _assert_zero_error_cells_in_tables(compiled, ALL_MODEL_TABLES)

        # Verify XNPV vs fractional-year discounting parity holds across all scenarios
        assert compiled.num(
            "dcf_schedule", "dcf_xnpv_ebitda_multiple_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)
        assert compiled.num(
            "dcf_schedule", "dcf_xnpv_perpetuity_growth_check", "pf_close"
        ) == pytest.approx(0.0, abs=1e-12)

    def test_emit_four_sheet_deliverable_workbook(self) -> None:
        raw_model = build_lbo_transaction_model()
        assert [s.name for s in raw_model.sheets] == [
            "Executive Dashboard",
            "Transaction & PPA",
            "LBO Model",
            "Valuation & Returns",
        ]
        assert [len(s.tables) for s in raw_model.sheets] == [6, 6, 10, 7]
        assert [t.id for t in raw_model.sheets[2].tables] == list(LBO_MODEL_SHEET_TABLES)

        out_path = emit_lbo_workbook()
        assert out_path == DEFAULT_DELIVERABLE_PATH
        assert out_path.exists()
        assert out_path.stat().st_size > 50_000

        with zipfile.ZipFile(out_path, "r") as zf:
            wb_xml = zf.read("xl/workbook.xml")
            s4_xml = zf.read("xl/worksheets/sheet4.xml")
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

        # Verify Column H (Col min=8) has standard timeline width (~12.71) in emitted deliverable
        s4_root = ET.fromstring(s4_xml)
        col_8_width = None
        for col_el in s4_root.findall(".//main:cols/main:col", namespaces=ns):
            c_min = int(col_el.attrib["min"])
            c_max = int(col_el.attrib["max"])
            if c_min <= 8 <= c_max:
                col_8_width = float(col_el.attrib["width"])
                break
        assert col_8_width is not None
        assert col_8_width == pytest.approx(12.71, abs=0.1)
