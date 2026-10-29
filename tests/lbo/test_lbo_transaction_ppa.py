"""Comprehensive unit and benchmark verification tests for Institutional LBO Reference Transaction & PPA."""

from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from models.lbo import (
    ANNUAL_PROJECTION_KEYS,
    EXIT_PERIOD_KEY,
    build_lbo_transaction_model,
    compile_lbo_transaction_model,
    emit_lbo_workbook,
)
from models.lbo.assumptions import (
    CASE_KEYS,
    NEW_FINANCING_TRANCHE_KEYS,
    TRANCHE_KEYS,
    BaselineAssumptions,
    DealAssumptions,
    FinancingAssumptions,
    LboAssumptions,
    OperatingAssumptions,
    OptionTrancheTerms,
    TrancheTerms,
    get_driver_metadata_records,
)
from tests.lbo.conftest import BenchmarkRegistry, BenchmarkTable

if TYPE_CHECKING:
    import f8

MODELS_LBO_DIR = Path("models/lbo")
ALLOWED_NUMERIC_LITERALS: frozenset[int] = frozenset(
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 365}
)

IS_ROW_MAP: dict[str, str] = {
    "fractional_years": "is_fractional_years",
    "sales": "is_net_sales",
    "cogs": "is_cogs",
    "gross_profit": "is_gross_profit",
    "sga": "is_sga",
    "ebitda": "is_ebitda",
    "depreciation": "is_depreciation",
    "ebita": "is_ebita",
    "amortization": "is_amortization",
    "sbc": "is_sbc",
    "ebit": "is_ebit",
    "interest_existing_debt": "is_interest_existing_debt",
    "interest_income": "is_interest_cash",
    "net_interest_expense": "is_interest_expense_net",
    "non_operating_income": "is_other_income_expense",
    "ebt": "is_ebt",
    "tax_provision": "is_tax_provision",
    "preferred_dividend": "is_pref_a_dividend",
    "noncontrolling_interest": "is_noncontrolling_interest",
    "equity_income": "is_equity_income_affiliates",
    "gaap_net_income_common": "is_gaap_net_income_common",
    "after_tax_amortization": "is_after_tax_amortization",
    "after_tax_sbc": "is_after_tax_sbc",
    "cash_net_income_common": "is_cash_net_income_common",
    "standalone_gaap_eps": "is_standalone_gaap_eps",
    "standalone_cash_eps": "is_standalone_cash_eps",
    "capex": "is_capex",
    "common_dividend_per_share": "is_common_dividend_per_share",
}

WC_ROW_MAP: dict[str, str] = {
    "accounts_receivable": "wc_accounts_receivable",
    "inventories": "wc_inventories",
    "dta_current": "wc_dta_current",
    "prepaid_expenses": "wc_prepaid_expenses",
    "non_cash_ca": "wc_non_cash_current_assets",
    "accounts_payable": "wc_accounts_payable",
    "accrued_liabilities": "wc_accrued_liabilities",
    "client_deposits": "wc_client_deposits",
    "other_current_liabilities": "wc_other_current_liabilities",
    "non_debt_cl": "wc_non_debt_current_liabilities",
    "net_working_capital": "wc_net_working_capital",
    "sales": "wc_sales",
    "cogs": "wc_cogs",
    "purchases": "wc_purchases",
    "ar_pct_sales": "wc_ar_pct_sales",
    "inv_pct_cogs": "wc_inv_pct_cogs",
    "dta_pct_sales": "wc_dta_pct_sales",
    "prepaid_pct_cogs": "wc_prepaid_pct_cogs",
    "ap_pct_cogs": "wc_ap_pct_cogs",
    "accrued_pct_cogs": "wc_accrued_pct_cogs",
    "deposits_pct_sales": "wc_deposits_pct_sales",
    "other_cl_pct_cogs": "wc_other_cl_pct_cogs",
    "ar_days": "wc_ar_days",
    "ap_days": "wc_ap_days",
    "inv_days": "wc_inv_days",
}

CF_ROW_MAP: dict[str, str] = {
    "net_income_common": "cf_net_income_common",
    "depreciation": "cf_depreciation",
    "amortization": "cf_amortization_intangibles",
    "amort_financing_costs": "cf_amortization_financing_costs",
    "sbc": "cf_sbc",
    "equity_income": "cf_equity_income_affiliates",
    "cash_div_equity_inv": "cf_cash_dividends_equity_inv",
    "amort_oid": "cf_amortization_oid",
    "loss_unamort_oid": "cf_loss_unamortized_oid",
    "pik_accrual_sub_note": "cf_pik_subordinated_note",
    "is_adjustments": "cf_is_adjustments",
    "change_in_wc": "cf_change_in_wc",
    "change_in_net_dtl": "cf_change_in_net_dtl",
    "change_in_other_lt_assets": "cf_change_in_other_assets",
    "change_in_other_lt_liabilities": "cf_change_in_other_liabilities",
    "bs_adjustments": "cf_bs_adjustments",
    "cfo": "cf_cfo",
    "capex": "cf_capex",
    "asset_sale_proceeds": "cf_asset_sale_proceeds",
    "cfi": "cf_cfi",
    "common_dividend": "cf_common_dividend",
    "cff": "cf_cff",
    "change_in_cash": "cf_change_in_cash",
}


@pytest.fixture(scope="module")
def compiled_model() -> f8.CompiledModel:
    """Compile default Institutional LBO Transaction & PPA model (Case 6 = LBO C)."""
    return compile_lbo_transaction_model()


def _bench_val(bench: BenchmarkTable, row_id: str, col_id: str) -> float | None:
    cell = bench.get_cell(row_id, col_id)
    if cell is None or cell.value is None:
        return None
    return float(cell.value)


class TestC1AssumptionsArchitecture:
    """Verify C1: frozen assumptions dataclasses, complete metadata, and zero inline driver literals."""

    def test_assumptions_containers_are_frozen(self) -> None:
        assumptions = LboAssumptions()
        with pytest.raises(FrozenInstanceError):
            assumptions.baseline.current_share_price = 15.0  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            assumptions.baseline.option_tranches[0].options_outstanding = 1.0  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            assumptions.deal.active_financing_case = 4  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            assumptions.financing.revolver.financing_fee_rate = 0.05  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            assumptions.operating.annual_cogs_savings = 25.0  # type: ignore[misc]

    def test_every_driver_field_has_complete_metadata(self) -> None:
        assumptions = LboAssumptions()
        records = get_driver_metadata_records(assumptions)
        assert len(records) >= 240
        for rec in records:
            assert rec["rationale"], f"Missing rationale on {rec['name']}"
            assert rec["basis"], f"Missing basis on {rec['name']}"
            assert rec["category"], f"Missing category on {rec['name']}"

    def test_individual_containers_introspection(self) -> None:
        for container in (
            BaselineAssumptions(),
            BaselineAssumptions().option_tranches[0],
            DealAssumptions(),
            FinancingAssumptions(),
            OperatingAssumptions(),
            FinancingAssumptions().senior_note,
        ):
            assert isinstance(
                container,
                (
                    BaselineAssumptions,
                    OptionTrancheTerms,
                    DealAssumptions,
                    FinancingAssumptions,
                    OperatingAssumptions,
                    TrancheTerms,
                ),
            )
            recs = get_driver_metadata_records(container)
            assert len(recs) > 0
            for rec in recs:
                assert rec["rationale"] and rec["basis"] and rec["category"]
        assert BaselineAssumptions().get_mrq_bs_balance("cash") == pytest.approx(146.606, abs=1e-12)
        with pytest.raises(KeyError):
            BaselineAssumptions().get_mrq_bs_balance("nonexistent_row")

    def test_tranche_and_case_accessors(self) -> None:
        fin = FinancingAssumptions()
        for tk in TRANCHE_KEYS:
            tranche = fin.get_tranche(tk)
            assert isinstance(tranche, TrancheTerms)
            if tk in NEW_FINANCING_TRANCHE_KEYS:
                assert tuple(tranche.draws_by_case.keys()) == CASE_KEYS
                assert tranche.draws_by_case == fin.get_draws_by_case(tk)
        for tk in NEW_FINANCING_TRANCHE_KEYS:
            assert tuple(fin.get_draws_by_case(tk).keys()) == CASE_KEYS
        assert DealAssumptions().combined_effective_tax_rate == pytest.approx(
            0.350003, rel=1e-12, abs=1e-12
        )
        op = OperatingAssumptions()
        assert len(op.management_sales_growth) == 10
        assert op.management_sales_growth[:4] == pytest.approx((0.14, 0.045, 0.035, 0.025))
        assert op.downside_sales_growth[:3] == pytest.approx((0.015, 0.005341880341880323, 0.0))
        assert op.management_cogs_pct_sales[:4] == pytest.approx((0.52, 0.515, 0.515, 0.51))
        assert op.downside_cogs_pct_sales[:3] == pytest.approx((0.525, 0.539, 0.542))
        assert op.management_sga_pct_sales[:5] == pytest.approx((0.19, 0.19, 0.189, 0.188, 0.187))

    def test_ssot_registries_and_uniform_builders(self) -> None:
        from models.lbo.model import TABLE_BUILDERS
        from models.lbo.registry import (
            BALANCE_SHEET_ACCOUNT_MAP,
            BALANCE_SHEET_ACCOUNTS,
            NEW_FINANCING_TRANCHE_SPECS,
            NON_REVOLVER_TRANCHE_SPECS,
            SCHED_SWEEP_TRANCHE_SPECS,
            TRANCHE_SPEC_MAP,
            TRANCHE_SPECS,
            TX_BALANCE_SHEET_ACCOUNT_MAP,
            get_bs_account,
            get_tranche_spec,
            get_tx_bs_account,
        )
        from models.lbo.timeline import (
            POST_CLOSE_PERIOD_COLS,
            POST_CLOSE_PERIOD_KEYS,
            PRE_CLOSE_ALL_COLS,
            PRE_CLOSE_QUARTER_COLS,
            PRE_CLOSE_ROLL_COLS,
            PRE_PF_COLS,
            TIMELINE_COL_KEYS,
            TIMELINE_COLUMNS,
        )

        # Timeline verification
        assert len(TIMELINE_COLUMNS) == 18
        assert len(TIMELINE_COL_KEYS) == 18
        assert len(POST_CLOSE_PERIOD_COLS) == 10
        assert len(POST_CLOSE_PERIOD_KEYS) == 10
        assert len(PRE_CLOSE_ALL_COLS) == 5
        assert len(PRE_CLOSE_QUARTER_COLS) == 5
        assert len(PRE_CLOSE_ROLL_COLS) == 4
        assert len(PRE_PF_COLS) == 7

        # Registry verification
        assert len(TRANCHE_SPECS) == 12
        assert len(TRANCHE_SPEC_MAP) == 12
        assert len(NEW_FINANCING_TRANCHE_SPECS) == 11
        assert len(NON_REVOLVER_TRANCHE_SPECS) == 11
        assert len(SCHED_SWEEP_TRANCHE_SPECS) == 10
        assert len(BALANCE_SHEET_ACCOUNTS) == 46
        assert len(BALANCE_SHEET_ACCOUNT_MAP) == 46
        assert len(TX_BALANCE_SHEET_ACCOUNT_MAP) == 46

        assert get_tranche_spec("term_loan_a").name == "Term loan - A"
        assert get_bs_account("bs_cash").label == "Cash & equivalents"
        assert get_tx_bs_account("cash").label == "Cash & equivalents"

        # TABLE_BUILDERS uniform signatures and zero lambdas
        assert len(TABLE_BUILDERS) == 29
        for tid, builder in TABLE_BUILDERS.items():
            assert callable(builder), f"Builder for {tid} is not callable"
            assert not builder.__name__.startswith("<lambda>"), (
                f"Builder for {tid} is a lambda wrapper"
            )
            sig = inspect.signature(builder)
            params = list(sig.parameters.keys())
            assert params == ["sheet", "assumptions"], (
                f"Builder for {tid} has non-uniform signature {params}"
            )

    def test_no_inline_driver_literals_or_forbidden_imports_in_models_lbo(self) -> None:
        for fn in (
            build_lbo_transaction_model,
            compile_lbo_transaction_model,
            emit_lbo_workbook,
        ):
            params = inspect.signature(fn).parameters
            assert "data_dir" not in params
            assert "registry" not in params

        for py_file in sorted(MODELS_LBO_DIR.glob("*.py")):
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


class TestC2CapTableAndOptions:
    """Verify C2: option_tranches and valuation_and_fdso match cap_table_and_options.json to IEEE-754 tolerance."""

    def test_option_tranches_exact_tie_out(
        self,
        compiled_model: f8.CompiledModel,
        registry: BenchmarkRegistry,
    ) -> None:
        bench = registry.get_table("cap_table_and_options")
        tranche_row_ids = [f"tranche_{i}" for i in range(1, 11)] + ["options_total"]
        option_col_ids = (
            "options_outstanding",
            "outstanding_strike",
            "itm_options",
            "liquidation_proceeds",
            "options_exercisable",
            "exercisable_strike",
            "treasury_method_shares",
        )
        for row_id in tranche_row_ids:
            for col_id in option_col_ids:
                expected = _bench_val(bench, row_id, col_id)
                if expected is None:
                    assert compiled_model.value("option_tranches", row_id, col_id) is None
                else:
                    actual = compiled_model.num("option_tranches", row_id, col_id)
                    assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_valuation_and_fdso_exact_tie_out(
        self,
        compiled_model: f8.CompiledModel,
        registry: BenchmarkRegistry,
    ) -> None:
        bench = registry.get_table("cap_table_and_options")
        val_row_ids = (
            "current_share_price",
            "offer_premium",
            "offer_price_per_share",
            "basic_shares_outstanding",
            "legacy_convertible_face_value",
            "legacy_conversion_price",
            "legacy_convertible_shares",
            "fdso_liquidation",
            "fdso_treasury",
        )
        for row_id in val_row_ids:
            expected = _bench_val(bench, row_id, "scalar_value")
            assert expected is not None
            actual = compiled_model.num("valuation_and_fdso", row_id, "value")
            assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)


class TestC3PreCloseBaselineRollforward:
    """Verify C3: income_statement, working_capital_schedule, cash_flow_statement, balance_sheet match benchmark across MRQ..pf_close."""

    PRE_CLOSE_COLS: tuple[str, ...] = (
        "mrq",
        "mrq_plus_1",
        "mrq_plus_2",
        "mrq_plus_3",
        "mrq_plus_4",
        "standalone_close",
    )

    def test_pre_close_income_statement_tie_out(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        for bench_row in IS_ROW_MAP.values():
            for col_id in (*self.PRE_CLOSE_COLS, "deal_adjustments", "pf_close"):
                expected = _bench_val(bench, bench_row, col_id)
                if expected is None:
                    assert compiled_model.value("income_statement", bench_row, col_id) is None
                else:
                    assert compiled_model.num(
                        "income_statement", bench_row, col_id
                    ) == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_pre_close_working_capital_tie_out(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        for bench_row in WC_ROW_MAP.values():
            for col_id in (*self.PRE_CLOSE_COLS, "deal_adjustments", "pf_close"):
                expected = _bench_val(bench, bench_row, col_id)
                if expected is None:
                    assert (
                        compiled_model.value("working_capital_schedule", bench_row, col_id) is None
                    )
                else:
                    assert compiled_model.num(
                        "working_capital_schedule", bench_row, col_id
                    ) == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_pre_close_cash_flow_tie_out(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        for bench_row in CF_ROW_MAP.values():
            for col_id in ("mrq_plus_1", "mrq_plus_2", "mrq_plus_3", "mrq_plus_4"):
                expected = _bench_val(bench, bench_row, col_id)
                if expected is not None:
                    assert compiled_model.num(
                        "cash_flow_statement", bench_row, col_id
                    ) == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_pre_close_balance_sheet_tie_out_and_equality(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_statements_and_credit")
        for bench_row_obj in bench.rows:
            if not bench_row_obj.id.startswith("bs_"):
                continue
            for col_id in (*self.PRE_CLOSE_COLS, "deal_adjustments", "pf_close"):
                expected = _bench_val(bench, bench_row_obj.id, col_id)
                if expected is not None:
                    assert compiled_model.num(
                        "balance_sheet", bench_row_obj.id, col_id
                    ) == pytest.approx(expected, rel=1e-12, abs=1e-12)
                assert compiled_model.num(
                    "balance_sheet", "bs_balance_check", col_id
                ) == pytest.approx(0.0, abs=1e-12)


class TestC4SourcesUsesPpaAndTransactionBs:
    """Verify C4: sources_uses, tranche_fees_oid, ppa_schedule, and transaction_bs match benchmark."""

    def test_sources_uses_all_six_cases_and_active_case(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_sources_uses_ppa")
        su_rows = tuple(
            r.id
            for r in bench.rows
            if not r.id.startswith("tx_bs_")
            and r.id
            not in {
                "purchase_price",
                "book_value_equity",
                "excess_purchase_price",
                "ppe_fv_mark",
                "ppe_dtl_created",
                "intangibles_fv_mark",
                "intangibles_dtl_created",
                "total_dtl_created",
                "goodwill_created",
            }
        )
        su_cols = (*CASE_KEYS, "active_case")
        for r_id in su_rows:
            for c_id in su_cols:
                expected = _bench_val(bench, r_id, c_id)
                assert expected is not None
                assert compiled_model.num("sources_uses", r_id, c_id) == pytest.approx(
                    expected, rel=1e-12, abs=1e-12
                )
        for c_id in su_cols:
            assert compiled_model.num("sources_uses", "sources_uses_check", c_id) == pytest.approx(
                0.0, abs=1e-12
            )

    def test_tranche_fees_and_oid_schedule(self, compiled_model: f8.CompiledModel) -> None:
        num = compiled_model.num
        assert num("tranche_fees_oid", "revolver", "capitalized_financing_fee") == pytest.approx(
            1.75, rel=1e-12, abs=1e-12
        )
        assert num("tranche_fees_oid", "term_loan_a", "capitalized_financing_fee") == pytest.approx(
            1.0, rel=1e-12, abs=1e-12
        )
        assert num("tranche_fees_oid", "senior_note", "capitalized_financing_fee") == pytest.approx(
            2.25, rel=1e-12, abs=1e-12
        )
        assert num(
            "tranche_fees_oid", "subordinated_note", "capitalized_financing_fee"
        ) == pytest.approx(1.5, rel=1e-12, abs=1e-12)
        assert num("tranche_fees_oid", "preferred_a", "fee_netted_proceeds") == pytest.approx(
            0.3, rel=1e-12, abs=1e-12
        )
        assert num("tranche_fees_oid", "total", "capitalized_financing_fee") == pytest.approx(
            6.5, rel=1e-12, abs=1e-12
        )
        assert num("tranche_fees_oid", "total", "fee_netted_proceeds") == pytest.approx(
            0.3, rel=1e-12, abs=1e-12
        )
        assert num("tranche_fees_oid", "total", "oid_amount") == pytest.approx(
            8.0, rel=1e-12, abs=1e-12
        )

    def test_ppa_schedule_tie_out(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_sources_uses_ppa")
        ppa_rows = (
            "purchase_price",
            "book_value_equity",
            "excess_purchase_price",
            "ppe_fv_mark",
            "ppe_dtl_created",
            "intangibles_fv_mark",
            "intangibles_dtl_created",
            "total_dtl_created",
            "goodwill_created",
        )
        for r_id in ppa_rows:
            expected = _bench_val(bench, r_id, "active_case")
            assert expected is not None
            assert compiled_model.num("ppa_schedule", r_id, "active_case") == pytest.approx(
                expected, rel=1e-12, abs=1e-12
            )

    def test_transaction_bs_all_11_columns_tie_out(
        self, compiled_model: f8.CompiledModel, registry: BenchmarkRegistry
    ) -> None:
        bench = registry.get_table("benchmark_sources_uses_ppa")
        tx_cols = (
            "pre_deal_close",
            "write_off_intangibles",
            "fv_marks_pretax",
            "new_net_dtl",
            "fv_acquired_bs",
            "ppa_adjustments",
            "acquired_bs",
            "deal_charges",
            "refinance_debt",
            "new_financing",
            "pf_close",
        )
        for row_obj in bench.rows:
            if not row_obj.id.startswith("tx_bs_"):
                continue
            raw_row = row_obj.id[6:]
            model_row = "common_stock" if raw_row == "common_stock_par" else raw_row
            for col_id in tx_cols:
                raw_expected = _bench_val(bench, row_obj.id, col_id)
                expected = raw_expected if raw_expected is not None else 0.0
                assert compiled_model.num("transaction_bs", model_row, col_id) == pytest.approx(
                    expected, rel=1e-12, abs=1e-12
                )
        for balanced_col in (
            "pre_deal_close",
            "acquired_bs",
            "deal_charges",
            "refinance_debt",
            "new_financing",
            "pf_close",
        ):
            assert compiled_model.num("transaction_bs", "bs_check", balanced_col) == pytest.approx(
                0.0, abs=1e-12
            )


class TestC5ScenarioSwitchingInvariants:
    """Verify C5: switching active_financing_case across Cases 1..6 preserves accounting identities."""

    @pytest.mark.parametrize("case_idx", [1, 2, 3, 4, 5, 6])
    def test_all_six_financing_cases_balance_sources_uses_and_pf_bs(self, case_idx: int) -> None:
        assumptions = LboAssumptions(
            deal=replace(DealAssumptions(), active_financing_case=case_idx)
        )
        compiled = compile_lbo_transaction_model(assumptions=assumptions)
        case_key = CASE_KEYS[case_idx - 1]
        assert compiled.num("sources_uses", "case_number", "active_case") == pytest.approx(
            float(case_idx), abs=1e-12
        )
        assert compiled.num("sources_uses", "total_sources", "active_case") == pytest.approx(
            compiled.num("sources_uses", "total_sources", case_key), rel=1e-12, abs=1e-12
        )
        assert compiled.num("sources_uses", "sources_uses_check", "active_case") == pytest.approx(
            0.0, abs=1e-12
        )
        for col_id in (
            "acquired_bs",
            "deal_charges",
            "refinance_debt",
            "new_financing",
            "pf_close",
        ):
            assert compiled.num("transaction_bs", "bs_check", col_id) == pytest.approx(
                0.0, abs=1e-12
            )

    def test_ppa_intangibles_writeoff_and_bargain_purchase_floor(self) -> None:
        writeoff_assumptions = LboAssumptions(
            deal=replace(DealAssumptions(), existing_intangibles_purch_acct_pct=1.0)
        )
        compiled_wo = compile_lbo_transaction_model(assumptions=writeoff_assumptions)
        assert compiled_wo.num("ppa_schedule", "total_dtl_created", "active_case") == pytest.approx(
            35.162523, abs=1e-6
        )
        assert compiled_wo.num("ppa_schedule", "goodwill_created", "active_case") == pytest.approx(
            433.613575, abs=1e-6
        )
        assert compiled_wo.num("transaction_bs", "bs_check", "pf_close") == pytest.approx(
            0.0, abs=1e-12
        )

        bargain_assumptions = LboAssumptions(
            deal=replace(DealAssumptions(), ppe_fair_value_mark=700.0)
        )
        compiled_bp = compile_lbo_transaction_model(assumptions=bargain_assumptions)
        assert compiled_bp.num("ppa_schedule", "goodwill_created", "active_case") == pytest.approx(
            0.0, abs=1e-12
        )
        assert compiled_bp.num("transaction_bs", "bs_check", "pf_close") == pytest.approx(
            0.0, abs=1e-12
        )


class TestC6ExecutiveDashboardSummaryAndChecks:
    """Verify Executive Dashboard summary tables and model integrity checks across scenarios."""

    def test_executive_dashboard_anchors(self, compiled_model: f8.CompiledModel) -> None:
        num = compiled_model.num
        assert num("dashboard_sources_uses", "total_sources", "balance") == pytest.approx(
            847.2795333125, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_sources_uses", "total_uses", "balance") == pytest.approx(
            847.2795333125, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_sources_uses", "total_sources", "pct_of_total") == pytest.approx(
            1.0, abs=1e-12
        )
        assert num("dashboard_sources_uses", "total_uses", "pct_of_total") == pytest.approx(
            1.0, abs=1e-12
        )
        assert num("dashboard_sources_uses", "total_sources", "mult_ltm_ebitda") == pytest.approx(
            847.2795333125 / 129.805, rel=1e-12, abs=1e-12
        )

        assert num(
            "dashboard_entry_valuation", "total_run_rate_cost_savings", "metric_value"
        ) == pytest.approx(30.0, abs=1e-12)
        assert num(
            "dashboard_entry_valuation", "equity_purchase_price", "metric_value"
        ) == pytest.approx(579.812625, rel=1e-12, abs=1e-12)
        assert num("dashboard_entry_valuation", "purchase_price", "metric_value") == pytest.approx(
            565.753165, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_entry_valuation", "net_debt", "metric_value") == pytest.approx(
            47.81165652835301, rel=1e-12, abs=1e-12
        )
        assert num(
            "dashboard_entry_valuation", "pf_enterprise_value", "metric_value"
        ) == pytest.approx(627.6242815283529, rel=1e-12, abs=1e-12)

        assert num(
            "dashboard_implied_multiples", "ltm_ebitda", "implied_multiple"
        ) == pytest.approx(4.835131786359176, rel=1e-12, abs=1e-12)
        assert num(
            "dashboard_implied_multiples", "fy13_pf_ebitda", "implied_multiple"
        ) == pytest.approx(627.6242815283529 / 155.9, rel=1e-12, abs=1e-12)

        assert num(
            "dashboard_returns_summary", "exit_enterprise_value", "metric_value"
        ) == pytest.approx(806.3068012752389, rel=1e-12, abs=1e-12)
        assert num(
            "dashboard_returns_summary", "exit_equity_value", "metric_value"
        ) == pytest.approx(1048.2848441702945, rel=1e-12, abs=1e-12)
        assert num("dashboard_returns_summary", "sponsor_moic", "metric_value") == pytest.approx(
            1.9211225994633099, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_returns_summary", "sponsor_irr", "metric_value") == pytest.approx(
            0.1901477499077573, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_returns_summary", "management_moic", "metric_value") == pytest.approx(
            2.445265021548457, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_returns_summary", "management_irr", "metric_value") == pytest.approx(
            0.26921346940144986, rel=1e-12, abs=1e-12
        )

        assert num("dashboard_credit_profile", "total_debt", "pf_close") == pytest.approx(
            202.0, rel=1e-12, abs=1e-12
        )
        assert num(
            "dashboard_credit_profile", "total_debt", ANNUAL_PROJECTION_KEYS[0]
        ) == pytest.approx(157.938, rel=1e-12, abs=1e-12)
        assert num("dashboard_credit_profile", "total_debt", EXIT_PERIOD_KEY) == pytest.approx(
            164.5084768, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_credit_profile", "net_debt", "pf_close") == pytest.approx(
            102.0, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_credit_profile", "ebitda", "pf_close") == pytest.approx(
            129.805, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_credit_profile", "total_debt_to_ebitda", "pf_close") == pytest.approx(
            1.556180424482878, rel=1e-12, abs=1e-12
        )
        assert num("dashboard_credit_profile", "net_debt_to_ebitda", "pf_close") == pytest.approx(
            0.7857940757289781, rel=1e-12, abs=1e-12
        )
        assert num(
            "dashboard_credit_profile", "ebitda_to_cash_interest", ANNUAL_PROJECTION_KEYS[0]
        ) == pytest.approx(9.055766443709322, rel=1e-12, abs=1e-12)

        assert num(
            "dashboard_integrity_checks", "check_sources_uses_balanced", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert num(
            "dashboard_integrity_checks", "check_balance_sheet_balanced", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert num(
            "dashboard_integrity_checks", "check_revolver_limit_observed", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert num(
            "dashboard_integrity_checks", "check_all_passed", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.parametrize("financing_case", [1, 2, 3, 4, 5, 6])
    @pytest.mark.parametrize("operating_case", [1, 2, 3, 4])
    def test_dashboard_integrity_checks_pass_across_all_scenarios(
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
        assert compiled.num(
            "dashboard_integrity_checks", "check_sources_uses_balanced", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert compiled.num(
            "dashboard_integrity_checks", "check_balance_sheet_balanced", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert compiled.num(
            "dashboard_integrity_checks", "check_revolver_limit_observed", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
        assert compiled.num(
            "dashboard_integrity_checks", "check_all_passed", "metric_value"
        ) == pytest.approx(1.0, abs=1e-12)
