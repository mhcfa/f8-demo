"""Comprehensive unit and benchmark verification tests for Unified 18-Column Institutional LBO Reference Statements & Credit."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from models.lbo import (
    POST_CLOSE_PERIOD_KEYS,
    STUB_PERIOD_KEY,
    TIMELINE_COL_KEYS,
    compile_lbo_transaction_model,
)
from models.lbo.assumptions import (
    DealAssumptions,
    FinancingAssumptions,
    LboAssumptions,
    OperatingAssumptions,
    get_driver_metadata_records,
)
from models.lbo.debt_sweep import NON_REVOLVER_TRANCHE_KEYS
from tests.lbo.conftest import BenchmarkRegistry, BenchmarkTable

if TYPE_CHECKING:
    import f8

MODELS_LBO_DIR = Path("models/lbo")
ALLOWED_NUMERIC_LITERALS: frozenset[int] = frozenset(
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 365}
)
POST_CLOSE_BENCH_COLS: tuple[str, ...] = ("pf_close", *POST_CLOSE_PERIOD_KEYS)


@pytest.fixture(scope="module")
def compiled_model() -> f8.CompiledModel:
    """Compile default Institutional LBO model (Financing Case 6 = LBO C, Operating Case 3 = Analyst)."""
    return compile_lbo_transaction_model()


@pytest.fixture(scope="module")
def compiled_no_deal_model() -> f8.CompiledModel:
    """Compile Institutional LBO model under Financing Case 1 (No Deal) for standalone EPS verification."""
    assumptions = LboAssumptions(deal=replace(DealAssumptions(), active_financing_case=1))
    return compile_lbo_transaction_model(assumptions=assumptions)


def _bench_val(bench: BenchmarkTable, row_id: str, col_id: str) -> float | None:
    cell = bench.get_cell(row_id, col_id)
    if cell is None or cell.value is None:
        return None
    return float(cell.value)


def _assert_section_tie_out(
    compiled: f8.CompiledModel,
    bench: BenchmarkTable,
    table_id: str,
    row_prefix: str,
    exclude_rows: frozenset[str] = frozenset(),
) -> int:
    count = 0
    for row in bench.rows:
        if not row.id.startswith(row_prefix) or row.id in exclude_rows:
            continue
        for col_id in TIMELINE_COL_KEYS:
            expected = _bench_val(bench, row.id, col_id)
            if expected is None:
                assert compiled.value(table_id, row.id, col_id) is None, (
                    f"Expected None at ({table_id}, {row.id}, {col_id})"
                )
            else:
                actual = compiled.num(table_id, row.id, col_id)
                assert actual == pytest.approx(expected, rel=1e-11, abs=1e-11), (
                    f"Mismatch at ({table_id}, {row.id}, {col_id}): {actual} vs {expected}"
                )
                count += 1
    return count


class TestC1Stage3AssumptionsAndZeroInlineLiterals:
    """Verify C1: Stage 3 driver fields, frozen immutability, metadata completeness, and AST literal check."""

    def test_stage3_assumptions_values_and_immutability(self) -> None:
        assumptions = LboAssumptions()
        op = assumptions.operating
        fin = assumptions.financing
        assert op.post_close_fractional_years == (
            0.75,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        )
        assert op.capex_useful_life_years == pytest.approx(7.0, abs=1e-12)
        assert op.capex_salvage_value == pytest.approx(0.0, abs=1e-12)
        assert op.sponsor_management_fee_annual == pytest.approx(0.0, abs=1e-12)
        assert len(fin.libor_curve) == 10
        assert fin.cash_interest_rate == pytest.approx(0.01, abs=1e-12)
        assert fin.revolver_undrawn_commitment_fee_rate == pytest.approx(0.005, abs=1e-12)
        assert fin.preferred_a.pik_pct_schedule[:5] == (1.0, 1.0, 1.0, 0.25, 0.0)
        assert fin.seller_note.pik_pct_schedule[:4] == (1.0, 1.0, 0.25, 0.0)

        with pytest.raises(FrozenInstanceError):
            op.capex_useful_life_years = 10.0  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            fin.cash_interest_rate = 0.02  # type: ignore[misc]

    def test_all_stage3_metadata_populated(self) -> None:
        records = get_driver_metadata_records(LboAssumptions())
        assert len(records) >= 180
        for rec in records:
            assert rec["rationale"], f"Missing rationale on {rec['name']}"
            assert rec["basis"], f"Missing basis on {rec['name']}"
            assert rec["category"], f"Missing category on {rec['name']}"
        assert len(get_driver_metadata_records(OperatingAssumptions())) >= 19
        assert len(get_driver_metadata_records(FinancingAssumptions())) >= 160

    def test_zero_inline_driver_literals_across_all_lbo_modules(self) -> None:
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


class TestC2PostCloseThreeStatementsWcDaAndTaxParity:
    """Verify C2: income_statement, balance_sheet, cash_flow_statement, working_capital_schedule, da_schedule, and nol_amt_schedule parity across all 18 columns."""

    def test_post_close_income_statement_parity(
        self,
        compiled_model: f8.CompiledModel,
        compiled_no_deal_model: f8.CompiledModel,
        registry: BenchmarkRegistry,
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "income_statement", "is_")
        assert checked == 661

        for r_id in ("is_standalone_gaap_eps", "is_standalone_cash_eps"):
            for inactive_col in ("standalone_close", "deal_adjustments", "pf_close"):
                assert compiled_no_deal_model.value("income_statement", r_id, inactive_col) is None
            for col_id in POST_CLOSE_PERIOD_KEYS:
                expected = _bench_val(bench, r_id, col_id)
                assert expected is not None
                actual = compiled_no_deal_model.num("income_statement", r_id, col_id)
                assert actual == pytest.approx(expected, rel=1e-11, abs=1e-11)

    def test_eps_accretion_dilution_across_scenarios(
        self,
        compiled_model: f8.CompiledModel,
        compiled_no_deal_model: f8.CompiledModel,
    ) -> None:
        pre_cols = (
            "mrq",
            "mrq_plus_1",
            "mrq_plus_2",
            "mrq_plus_3",
            "mrq_plus_4",
        )
        for r_id in (
            "is_pf_gaap_eps",
            "is_gaap_accretion_dollars",
            "is_gaap_accretion_pct",
            "is_pf_cash_eps",
            "is_cash_accretion_dollars",
            "is_cash_accretion_pct",
        ):
            for col_id in pre_cols:
                assert compiled_model.value("income_statement", r_id, col_id) == "NA"
            for inactive_col in ("standalone_close", "deal_adjustments", "pf_close"):
                assert compiled_model.value("income_statement", r_id, inactive_col) is None

        for col_id in POST_CLOSE_PERIOD_KEYS:
            assert compiled_model.value("income_statement", "is_pf_gaap_eps", col_id) == "NM"
            assert compiled_model.value("income_statement", "is_pf_cash_eps", col_id) == "NM"
        for col_id in POST_CLOSE_PERIOD_KEYS[:5]:
            for r_id in (
                "is_gaap_accretion_dollars",
                "is_gaap_accretion_pct",
                "is_cash_accretion_dollars",
                "is_cash_accretion_pct",
            ):
                assert compiled_model.value("income_statement", r_id, col_id) == "NM"
        for col_id in POST_CLOSE_PERIOD_KEYS[5:]:
            for r_id in (
                "is_gaap_accretion_dollars",
                "is_gaap_accretion_pct",
                "is_cash_accretion_dollars",
                "is_cash_accretion_pct",
            ):
                assert compiled_model.value("income_statement", r_id, col_id) == "NA"

        for col_id in POST_CLOSE_PERIOD_KEYS[:5]:
            for r_id in (
                "is_gaap_accretion_dollars",
                "is_gaap_accretion_pct",
                "is_cash_accretion_dollars",
                "is_cash_accretion_pct",
            ):
                assert compiled_no_deal_model.num(
                    "income_statement", r_id, col_id
                ) == pytest.approx(0.0, abs=1e-12)

        cm_refi_a = compile_lbo_transaction_model(
            LboAssumptions(deal=replace(DealAssumptions(), active_financing_case=2))
        )
        assert cm_refi_a.num(
            "income_statement", "is_gaap_accretion_pct", STUB_PERIOD_KEY
        ) == pytest.approx(0.3112005513468159, rel=1e-11, abs=1e-11)
        assert cm_refi_a.num(
            "income_statement", "is_gaap_accretion_pct", POST_CLOSE_PERIOD_KEYS[2]
        ) == pytest.approx(0.4300333637788717, rel=1e-11, abs=1e-11)
        assert cm_refi_a.num(
            "income_statement", "is_cash_accretion_pct", STUB_PERIOD_KEY
        ) == pytest.approx(0.20707253351834415, rel=1e-11, abs=1e-11)

        cm_refi_b = compile_lbo_transaction_model(
            LboAssumptions(deal=replace(DealAssumptions(), active_financing_case=3))
        )
        assert cm_refi_b.num(
            "income_statement", "is_gaap_accretion_pct", STUB_PERIOD_KEY
        ) == pytest.approx(0.2824151441374919, rel=1e-11, abs=1e-11)
        assert cm_refi_b.num(
            "income_statement", "is_gaap_accretion_pct", POST_CLOSE_PERIOD_KEYS[2]
        ) == pytest.approx(0.3354439870680244, rel=1e-11, abs=1e-11)

    def test_key_ratios_drivers_and_capex_salvage_wiring(
        self, compiled_model: f8.CompiledModel
    ) -> None:
        assert compiled_model.num("income_statement", "is_sales_growth", "mrq") == pytest.approx(
            0.04166666666666696, abs=1e-12
        )
        assert compiled_model.num(
            "operating_schedule", "flat_sales_growth", STUB_PERIOD_KEY
        ) == pytest.approx(0.04166666666666696, abs=1e-12)
        assert compiled_model.value("income_statement", "is_gaap_earnings_growth", "mrq") is None
        assert compiled_model.value("income_statement", "is_cash_earnings_growth", "mrq") is None
        assert compiled_model.num("income_statement", "is_gaap_earnings_growth", "mrq_plus_1") > 0.0
        assert compiled_model.num("income_statement", "is_gross_margin", "mrq") == pytest.approx(
            52.0 / 106.7, rel=1e-12, abs=1e-12
        )
        assert compiled_model.num("income_statement", "is_ebitda_margin", "mrq") == pytest.approx(
            31.8 / 106.7, rel=1e-12, abs=1e-12
        )
        assert compiled_model.num("income_statement", "is_roic", "mrq") == pytest.approx(
            0.2023467834669806, rel=1e-12, abs=1e-12
        )
        assert compiled_model.num("income_statement", "is_roic", "mrq_plus_3") == pytest.approx(
            0.19621359345624043, rel=1e-12, abs=1e-12
        )
        assert compiled_model.num("income_statement", "is_roe", "mrq") == pytest.approx(
            0.3427590365139546, rel=1e-12, abs=1e-12
        )
        assert compiled_model.num("income_statement", "is_roa", "mrq") == pytest.approx(
            0.0776178673831393, rel=1e-12, abs=1e-12
        )

        assert (
            compiled_model.value("income_statement", "is_gaap_earnings_growth", STUB_PERIOD_KEY)
            is None
        )
        assert (
            compiled_model.value("income_statement", "is_cash_earnings_growth", STUB_PERIOD_KEY)
            is None
        )
        for col_id in POST_CLOSE_PERIOD_KEYS:
            assert compiled_model.num(
                "income_statement", "is_sales_growth", col_id
            ) == pytest.approx(
                compiled_model.num("operating_schedule", "active_sales_growth", col_id),
                abs=1e-12,
            )
            assert compiled_model.num("income_statement", "is_roic", col_id) == pytest.approx(
                compiled_model.num("credit_stats", "credit_roic", col_id), abs=1e-12
            )
            assert compiled_model.num("income_statement", "is_roe", col_id) == pytest.approx(
                compiled_model.num("credit_stats", "credit_roe", col_id), abs=1e-12
            )
            assert compiled_model.num("income_statement", "is_roa", col_id) == pytest.approx(
                compiled_model.num("credit_stats", "credit_roa", col_id), abs=1e-12
            )
            assert compiled_model.num(
                "income_statement", "is_effective_tax_rate", col_id
            ) == pytest.approx(
                compiled_model.num("nol_amt_schedule", "blended_tax_rate", col_id), abs=1e-12
            )

        salvage_cm = compile_lbo_transaction_model(
            LboAssumptions(operating=replace(OperatingAssumptions(), capex_salvage_value=3.5))
        )
        assert salvage_cm.num(
            "da_schedule", "da_capex_cohort_1", STUB_PERIOD_KEY
        ) < compiled_model.num("da_schedule", "da_capex_cohort_1", STUB_PERIOD_KEY)

    def test_post_close_balance_sheet_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "balance_sheet", "bs_")
        assert checked == 828

    def test_post_close_cash_flow_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "cash_flow_statement", "cf_")
        assert checked == 588

    def test_post_close_working_capital_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "working_capital_schedule", "wc_")
        assert checked == 426

    def test_da_schedule_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "da_schedule", "da_")
        assert checked == 173

    def test_post_close_tax_and_dtl_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "nol_amt_schedule", "tax_")
        assert checked == 296


class TestC3DebtRollForwardAndCashSweepParity:
    """Verify C3: sweep_* and debt_* rows across all 12 tranches match benchmark_statements_and_credit.json across all 18 columns."""

    def test_cash_sweep_waterfall_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "debt_sweep_schedule", "sweep_")
        assert checked == 312

    def test_twelve_tranche_debt_rollforward_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "debt_sweep_schedule", "debt_")
        assert checked == 2315


class TestC4CreditStatisticsAndRatiosParity:
    """Verify C4: credit_* rows match benchmark_statements_and_credit.json across all 18 columns."""

    def test_credit_statistics_parity(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        checked = _assert_section_tie_out(compiled_model, bench, "credit_stats", "credit_")
        assert checked == 436


class TestC5AccountingIdentitiesAndScenarioStress:
    """Verify C5: accounting identities hold across all 6 financing cases x 4 operating cases across all 18 columns."""

    @pytest.mark.parametrize("financing_case", [1, 2, 3, 4, 5, 6])
    @pytest.mark.parametrize("operating_case", [1, 2, 3, 4])
    def test_all_financing_and_operating_cases_preserve_identities(
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

        for col_id in TIMELINE_COL_KEYS:
            assert compiled.num("balance_sheet", "bs_balance_check", col_id) == pytest.approx(
                0.0, abs=1e-11
            )

        pre_roll_cols = ("mrq", "mrq_plus_1", "mrq_plus_2", "mrq_plus_3", "mrq_plus_4")
        for idx in range(1, len(pre_roll_cols)):
            prev_col = pre_roll_cols[idx - 1]
            col_id = pre_roll_cols[idx]
            prev_cash = compiled.num("balance_sheet", "bs_cash", prev_col)
            chg_cash = compiled.num("cash_flow_statement", "cf_change_in_cash", col_id)
            cur_cash = compiled.num("balance_sheet", "bs_cash", col_id)
            assert cur_cash == pytest.approx(prev_cash + chg_cash, abs=1e-11)

        for idx, col_id in enumerate(POST_CLOSE_BENCH_COLS):
            assert compiled.num("balance_sheet", "bs_net_dtl", col_id) == pytest.approx(
                compiled.num("nol_amt_schedule", "tax_net_dtl_end", col_id), abs=1e-11
            )
            for tk in NON_REVOLVER_TRANCHE_KEYS:
                book = compiled.num("debt_sweep_schedule", f"debt_{tk}_book_end", col_id)
                face = compiled.num("debt_sweep_schedule", f"debt_{tk}_face_end", col_id)
                oid = compiled.num("debt_sweep_schedule", f"debt_{tk}_oid_end", col_id)
                assert book == pytest.approx(face - oid, abs=1e-11)
                bs_row = "bs_existing_lt_debt" if tk == "legacy_debt" else f"bs_{tk}"
                assert compiled.num("balance_sheet", bs_row, col_id) == pytest.approx(
                    book, abs=1e-11
                )

            if idx > 0:
                prev_col = POST_CLOSE_BENCH_COLS[idx - 1]
                prev_cash = compiled.num("balance_sheet", "bs_cash", prev_col)
                chg_cash = compiled.num("cash_flow_statement", "cf_change_in_cash", col_id)
                cur_cash = compiled.num("balance_sheet", "bs_cash", col_id)
                assert cur_cash == pytest.approx(prev_cash + chg_cash, abs=1e-11)
                assert compiled.num(
                    "debt_sweep_schedule", "sweep_beg_cash", col_id
                ) == pytest.approx(prev_cash, abs=1e-11)

                tax_prov = compiled.num("income_statement", "is_tax_provision", col_id)
                book_tax = compiled.num("nol_amt_schedule", "tax_book_tax_expense", col_id)
                cash_tax = compiled.num("nol_amt_schedule", "tax_total_cash_taxes", col_id)
                def_tax = compiled.num("nol_amt_schedule", "tax_deferred_tax_expense", col_id)
                assert tax_prov == pytest.approx(book_tax, abs=1e-11)
                assert book_tax == pytest.approx(cash_tax + def_tax, abs=1e-11)
