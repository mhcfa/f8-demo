"""Unified 18-column Income Statement, Balance Sheet, and Cash Flow Statement builders."""

from __future__ import annotations

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.assumptions.financing import TRANCHE_KEYS
from models.lbo.registry import (
    BALANCE_SHEET_ACCOUNTS,
    NEW_FINANCING_TRANCHE_SPECS,
)
from models.lbo.timeline import (
    CONCURRENT_PROJECTION_KEYS,
    FINAL_PERIOD_KEY,
    POST_CLOSE_PERIOD_KEYS,
    PRE_CLOSE_ALL_COLS,
    STUB_PERIOD_KEY,
    add_timeline_columns,
)

DEBT_TRANCHE_KEYS: tuple[str, ...] = TRANCHE_KEYS[:10]

INACTIVE_IS_COLS: tuple[str, ...] = (
    "standalone_close",
    "deal_adjustments",
    "pf_close",
)

INACTIVE_CF_COLS: tuple[str, ...] = (
    "mrq",
    "standalone_close",
    "deal_adjustments",
    "pf_close",
)

IS_DEBT_INTEREST_ROWS: dict[str, tuple[str, str]] = {
    "legacy_debt": (
        "is_interest_existing_debt",
        'debt_sweep_schedule["debt_legacy_debt_book_interest", @col]',
    ),
    "revolver": (
        "is_interest_revolver",
        'debt_sweep_schedule["debt_revolver_total_interest", @col]',
    ),
    "term_loan_a": (
        "is_interest_term_loan_a",
        'debt_sweep_schedule["debt_term_loan_a_book_interest", @col]',
    ),
    "term_loan_b": (
        "is_interest_term_loan_b",
        'debt_sweep_schedule["debt_term_loan_b_book_interest", @col]',
    ),
    "senior_note": (
        "is_interest_senior_note",
        'debt_sweep_schedule["debt_senior_note_book_interest", @col]',
    ),
    "subordinated_note": (
        "is_interest_subordinated_note",
        'debt_sweep_schedule["debt_subordinated_note_book_interest", @col]',
    ),
    "mezzanine": (
        "is_interest_mezzanine",
        'debt_sweep_schedule["debt_mezzanine_book_interest", @col]',
    ),
    "seller_note": (
        "is_interest_seller_note",
        'debt_sweep_schedule["debt_seller_note_book_interest", @col]',
    ),
    "convertible_bond": (
        "is_interest_convertible_bond",
        'debt_sweep_schedule["debt_convertible_bond_book_interest", @col]',
    ),
    "debt_8": (
        "is_interest_debt_8",
        'debt_sweep_schedule["debt_debt_8_book_interest", @col]',
    ),
}

CASH_FLOW_ROWS: tuple[tuple[str, str, str, str | None, f8.SemanticStyle | None], ...] = (
    (
        "cf_net_income_common",
        "Net income available to common",
        'income_statement["is_gaap_net_income_common", @col]',
        None,
        None,
    ),
    ("cf_depreciation", "Depreciation", 'income_statement["is_depreciation", @col]', None, None),
    (
        "cf_amortization_intangibles",
        "Amortization of intangibles",
        'income_statement["is_amortization", @col]',
        None,
        None,
    ),
    (
        "cf_amortization_financing_costs",
        "Amortization of capitalized financing costs",
        'income_statement["is_amort_deferred_financing", @col]',
        None,
        None,
    ),
    ("cf_sbc", "Stock-based compensation", 'income_statement["is_sbc", @col]', None, None),
    (
        "cf_equity_income_affiliates",
        "Equity income in affiliates",
        '-income_statement["is_equity_income_affiliates", @col]',
        None,
        None,
    ),
    ("cf_cash_dividends_equity_inv", "Cash dividends from equity investments", "0", None, None),
    (
        "cf_amortization_oid",
        "Amortization of OID",
        'debt_sweep_schedule["debt_total_oid_amort", @col]',
        "0",
        None,
    ),
    (
        "cf_loss_unamortized_oid",
        "Loss on unamortized OID at repayment",
        'income_statement["is_loss_unamortized_oid", @col]',
        None,
        None,
    ),
    (
        "cf_pik_subordinated_note",
        "PIK accrual of Subordinated note",
        'debt_sweep_schedule["debt_subordinated_note_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_mezzanine",
        "PIK accrual of Mezzanine",
        'debt_sweep_schedule["debt_mezzanine_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_seller_note",
        "PIK accrual of Seller note",
        'debt_sweep_schedule["debt_seller_note_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_convertible_bond",
        "PIK accrual of Convertible bond",
        'debt_sweep_schedule["debt_convertible_bond_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_debt_8",
        "PIK accrual of [Debt 8]",
        'debt_sweep_schedule["debt_debt_8_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_preferred_a",
        "PIK accrual of Preferred stock - A",
        'debt_sweep_schedule["debt_preferred_a_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_pik_preferred_b",
        "PIK accrual of Preferred stock - B",
        'debt_sweep_schedule["debt_preferred_b_face_pik", @col]',
        "0",
        None,
    ),
    (
        "cf_is_adjustments",
        "Income statement adjustments",
        'SUM(cash_flow_statement["cf_depreciation".."cf_pik_preferred_b", @col])',
        None,
        "subtotal",
    ),
    (
        "cf_change_in_wc",
        "(Increase) / decrease in working capital",
        'working_capital_schedule["wc_net_working_capital", col.prev] - working_capital_schedule["wc_net_working_capital", @col]',
        None,
        None,
    ),
    (
        "cf_change_in_net_dtl",
        "Increase / (decrease) in net DTL",
        'balance_sheet["bs_net_dtl", @col] - balance_sheet["bs_net_dtl", col.prev]',
        None,
        None,
    ),
    (
        "cf_change_in_other_assets",
        "(Increase) / decrease in other assets",
        'balance_sheet["bs_other_lt_assets", col.prev] - balance_sheet["bs_other_lt_assets", @col]',
        None,
        None,
    ),
    (
        "cf_change_in_other_liabilities",
        "Increase / (decrease) in other liabilities",
        'balance_sheet["bs_other_lt_liabilities", @col] - balance_sheet["bs_other_lt_liabilities", col.prev]',
        None,
        None,
    ),
    (
        "cf_bs_adjustments",
        "Balance sheet adjustments",
        'SUM(cash_flow_statement["cf_change_in_wc".."cf_change_in_other_liabilities", @col])',
        None,
        "subtotal",
    ),
    (
        "cf_cfo",
        "Cash flow from operating activities",
        'cash_flow_statement["cf_net_income_common", @col] + cash_flow_statement["cf_is_adjustments", @col] + cash_flow_statement["cf_bs_adjustments", @col]',
        None,
        "subtotal",
    ),
    ("cf_capex", "Capital expenditures", '-income_statement["is_capex", @col]', None, None),
    ("cf_asset_sale_proceeds", "Proceeds from the sale of assets", "0", None, None),
    (
        "cf_cfi",
        "Cash flow from investing activities",
        'cash_flow_statement["cf_capex", @col] + cash_flow_statement["cf_asset_sale_proceeds", @col]',
        None,
        "subtotal",
    ),
    (
        "cf_revolver",
        "Revolver",
        'debt_sweep_schedule["debt_revolver_draw", @col] + debt_sweep_schedule["debt_revolver_paydown", @col]',
        "0",
        None,
    ),
    (
        "cf_debt_assumed",
        "Debt assumed",
        'debt_sweep_schedule["debt_legacy_debt_face_mandatory", @col] + debt_sweep_schedule["debt_legacy_debt_face_optional", @col]',
        None,
        None,
    ),
    (
        "cf_term_loan_a",
        "Term loan - A",
        'debt_sweep_schedule["debt_term_loan_a_face_mandatory", @col] + debt_sweep_schedule["debt_term_loan_a_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_term_loan_b",
        "Term loan - B",
        'debt_sweep_schedule["debt_term_loan_b_face_mandatory", @col] + debt_sweep_schedule["debt_term_loan_b_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_senior_note",
        "Senior note",
        'debt_sweep_schedule["debt_senior_note_face_mandatory", @col] + debt_sweep_schedule["debt_senior_note_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_subordinated_note",
        "Subordinated note",
        'debt_sweep_schedule["debt_subordinated_note_face_mandatory", @col] + debt_sweep_schedule["debt_subordinated_note_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_mezzanine",
        "Mezzanine",
        'debt_sweep_schedule["debt_mezzanine_face_mandatory", @col] + debt_sweep_schedule["debt_mezzanine_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_seller_note",
        "Seller note",
        'debt_sweep_schedule["debt_seller_note_face_mandatory", @col] + debt_sweep_schedule["debt_seller_note_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_convertible_bond",
        "Convertible bond",
        'debt_sweep_schedule["debt_convertible_bond_face_mandatory", @col] + debt_sweep_schedule["debt_convertible_bond_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_debt_8",
        "[Debt 8]",
        'debt_sweep_schedule["debt_debt_8_face_mandatory", @col] + debt_sweep_schedule["debt_debt_8_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_preferred_a",
        "Preferred stock - A",
        'debt_sweep_schedule["debt_preferred_a_face_mandatory", @col] + debt_sweep_schedule["debt_preferred_a_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_preferred_b",
        "Preferred stock - B",
        'debt_sweep_schedule["debt_preferred_b_face_mandatory", @col] + debt_sweep_schedule["debt_preferred_b_face_optional", @col]',
        "0",
        None,
    ),
    (
        "cf_common_dividend",
        "Common dividend",
        '-income_statement["is_common_dividend_per_share", @col] * valuation_and_fdso["basic_shares_outstanding", "value"]',
        None,
        None,
    ),
    (
        "cf_cff",
        "Cash flow from financing activities",
        'SUM(cash_flow_statement["cf_revolver".."cf_common_dividend", @col])',
        None,
        "subtotal",
    ),
    (
        "cf_cash_available_for_debt_repayment",
        "Cash flow available for debt repayment",
        'cash_flow_statement["cf_cfo", @col] + cash_flow_statement["cf_cfi", @col]',
        None,
        "subtotal",
    ),
    (
        "cf_change_in_cash",
        "Change in cash",
        'cash_flow_statement["cf_cfo", @col] + cash_flow_statement["cf_cfi", @col] + cash_flow_statement["cf_cff", @col]',
        None,
        "total",
    ),
)

BALANCE_SHEET_EXPRS: dict[str, str] = {
    "bs_cash": 'balance_sheet["bs_cash", col.prev] + cash_flow_statement["cf_change_in_cash", @col]',
    "bs_accounts_receivable": 'working_capital_schedule["wc_accounts_receivable", @col]',
    "bs_inventories": 'working_capital_schedule["wc_inventories", @col]',
    "bs_dta_current": 'working_capital_schedule["wc_dta_current", @col]',
    "bs_prepaid_expenses": 'working_capital_schedule["wc_prepaid_expenses", @col]',
    "bs_total_current_assets": 'SUM(balance_sheet["bs_cash".."bs_prepaid_expenses", @col])',
    "bs_ppe_gross": 'balance_sheet["bs_ppe_gross", col.prev] + income_statement["is_capex", @col]',
    "bs_accumulated_depreciation": 'balance_sheet["bs_accumulated_depreciation", col.prev] - income_statement["is_depreciation", @col]',
    "bs_ppe_net": 'balance_sheet["bs_ppe_gross", @col] + balance_sheet["bs_accumulated_depreciation", @col]',
    "bs_equity_investments": 'balance_sheet["bs_equity_investments", col.prev]',
    "bs_capitalized_financing_costs": 'balance_sheet["bs_capitalized_financing_costs", col.prev] - income_statement["is_amort_deferred_financing", @col]',
    "bs_goodwill": 'balance_sheet["bs_goodwill", col.prev]',
    "bs_intangibles_net": 'balance_sheet["bs_intangibles_net", col.prev] - income_statement["is_amortization", @col]',
    "bs_operating_rights": 'balance_sheet["bs_operating_rights", col.prev]',
    "bs_other_lt_assets": 'balance_sheet["bs_other_lt_assets", col.prev]',
    "bs_total_assets": 'balance_sheet["bs_total_current_assets", @col] + balance_sheet["bs_ppe_net", @col] + SUM(balance_sheet["bs_equity_investments".."bs_other_lt_assets", @col])',
    "bs_short_term_debt": 'balance_sheet["bs_short_term_debt", col.prev]',
    "bs_accounts_payable": 'working_capital_schedule["wc_accounts_payable", @col]',
    "bs_accrued_liabilities": 'working_capital_schedule["wc_accrued_liabilities", @col]',
    "bs_client_deposits": 'working_capital_schedule["wc_client_deposits", @col]',
    "bs_other_current_liabilities": 'working_capital_schedule["wc_other_current_liabilities", @col]',
    "bs_total_current_liabilities": 'SUM(balance_sheet["bs_short_term_debt".."bs_other_current_liabilities", @col])',
    "bs_capital_leases": 'balance_sheet["bs_capital_leases", col.prev]',
    "bs_existing_lt_debt": 'debt_sweep_schedule["debt_legacy_debt_book_end", @col]',
    "bs_revolver": 'debt_sweep_schedule["debt_revolver_end", @col]',
    "bs_term_loan_a": 'debt_sweep_schedule["debt_term_loan_a_book_end", @col]',
    "bs_term_loan_b": 'debt_sweep_schedule["debt_term_loan_b_book_end", @col]',
    "bs_senior_note": 'debt_sweep_schedule["debt_senior_note_book_end", @col]',
    "bs_subordinated_note": 'debt_sweep_schedule["debt_subordinated_note_book_end", @col]',
    "bs_mezzanine": 'debt_sweep_schedule["debt_mezzanine_book_end", @col]',
    "bs_seller_note": 'debt_sweep_schedule["debt_seller_note_book_end", @col]',
    "bs_convertible_bond": 'debt_sweep_schedule["debt_convertible_bond_book_end", @col]',
    "bs_debt_8": 'debt_sweep_schedule["debt_debt_8_book_end", @col]',
    "bs_total_debt": 'balance_sheet["bs_short_term_debt", @col] + SUM(balance_sheet["bs_capital_leases".."bs_debt_8", @col])',
    "bs_net_dtl": 'nol_amt_schedule["tax_net_dtl_end", @col]',
    "bs_other_lt_liabilities": 'balance_sheet["bs_other_lt_liabilities", col.prev]',
    "bs_total_liabilities": 'balance_sheet["bs_total_current_liabilities", @col] + SUM(balance_sheet["bs_capital_leases".."bs_debt_8", @col]) + balance_sheet["bs_net_dtl", @col] + balance_sheet["bs_other_lt_liabilities", @col]',
    "bs_noncontrolling_interest": 'balance_sheet["bs_noncontrolling_interest", col.prev]',
    "bs_preferred_a": 'debt_sweep_schedule["debt_preferred_a_book_end", @col]',
    "bs_preferred_b": 'debt_sweep_schedule["debt_preferred_b_book_end", @col]',
    "bs_common_stock_par": 'balance_sheet["bs_common_stock_par", col.prev]',
    "bs_apic": 'balance_sheet["bs_apic", col.prev] + income_statement["is_sbc", @col]',
    "bs_retained_earnings": 'balance_sheet["bs_retained_earnings", col.prev] + income_statement["is_gaap_net_income_common", @col] + cash_flow_statement["cf_common_dividend", @col]',
    "bs_total_equity": 'SUM(balance_sheet["bs_preferred_a".."bs_retained_earnings", @col])',
    "bs_total_liabilities_and_equity": 'balance_sheet["bs_total_liabilities", @col] + balance_sheet["bs_noncontrolling_interest", @col] + balance_sheet["bs_total_equity", @col]',
    "bs_balance_check": 'balance_sheet["bs_total_assets", @col] - balance_sheet["bs_total_liabilities_and_equity", @col]',
}

NEW_TRANCHE_BS_ROWS: tuple[str, ...] = tuple(t.bs_row_id for t in NEW_FINANCING_TRANCHE_SPECS)


def build_income_statement(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the unified 18-column `income_statement` table."""
    base = assumptions.baseline
    op = assumptions.operating
    sub = "Units: $ in millions"
    table = sheet.add_table("income_statement", "Income Statement", subtitle=sub, currency="USD")
    add_timeline_columns(table, "Income Statement Line Item")

    fy_cells: dict[str, f8.CellInputValue] = {
        "label": "Fractional years",
        "standalone_close": None,
        "deal_adjustments": None,
    }
    for col_id, pre_fy in zip(PRE_CLOSE_ALL_COLS, base.pre_close_fractional_years, strict=True):
        fy_cells[col_id] = pre_fy
    for col_id, post_fy in zip(POST_CLOSE_PERIOD_KEYS, op.post_close_fractional_years, strict=True):
        fy_cells[col_id] = post_fy
    table.add_row("is_fractional_years", cells=fy_cells, style="data", format="number", decimals=2)
    table.set_cell(
        "is_fractional_years",
        "pf_close",
        expr='income_statement["is_fractional_years", "mrq_plus_3"]',
    )

    def add_is(
        r_id: str,
        lbl: str,
        expr: str,
        style: f8.SemanticStyle | None = None,
        fmt: f8.FormatPreset = "currency",
        dec: int = 3,
        *,
        pre_vals: tuple[float, ...] | None = None,
        pre_expr: str | None = None,
        mrq_val: float | None = None,
        mrq_expr: str | None = None,
    ) -> None:
        cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_IS_COLS, None)
        cells["label"] = lbl
        if pre_vals is not None:
            for col_id, v in zip(PRE_CLOSE_ALL_COLS, pre_vals, strict=True):
                cells[col_id] = f8.Cell(value=v, style="data", format=fmt, decimals=dec)
        if mrq_val is not None:
            cells["mrq"] = f8.Cell(value=mrq_val, style="data", format=fmt, decimals=dec)
        table.add_row(r_id, cells=cells, expr=expr, style=style, format=fmt, decimals=dec)
        if pre_expr is not None:
            table.set_cells(
                r_id,
                slice("mrq", "mrq_plus_4"),
                expr=pre_expr,
                style=style,
                format=fmt,
                decimals=dec,
            )
        if mrq_expr is not None:
            table.set_cell(r_id, "mrq", expr=mrq_expr, style=style, format=fmt, decimals=dec)

    add_is(
        "is_net_sales",
        "Net Sales",
        '(income_statement["is_net_sales", col.prev] / income_statement["is_fractional_years", col.prev]) * (1 + operating_schedule["active_sales_growth", @col]) * income_statement["is_fractional_years", @col]',
        pre_vals=base.pre_close_sales,
    )
    table.set_cell(
        "is_net_sales",
        STUB_PERIOD_KEY,
        expr='(operating_schedule["analyst_revenue", "pf_close"] / operating_schedule["analyst_fractional_years", "pf_close"]) * (1 + operating_schedule["active_sales_growth", @col]) * income_statement["is_fractional_years", @col]',
    )
    add_is(
        "is_cogs",
        "COGS",
        'income_statement["is_net_sales", @col] * operating_schedule["active_cogs_pct_sales", @col] - operating_schedule["cogs_synergy", @col]',
        pre_vals=base.pre_close_cogs,
    )
    add_is(
        "is_gross_profit",
        "Gross profit",
        'income_statement["is_net_sales", @col] - income_statement["is_cogs", @col]',
        "subtotal",
    )
    add_is(
        "is_sga",
        "SG&A",
        'income_statement["is_net_sales", @col] * operating_schedule["active_sga_pct_sales", @col] - operating_schedule["sga_synergy", @col]',
        pre_vals=base.pre_close_sga,
    )
    add_is(
        "is_ebitda",
        "EBITDA",
        'income_statement["is_gross_profit", @col] - income_statement["is_sga", @col]',
        "subtotal",
    )
    add_is(
        "is_depreciation",
        "Depreciation",
        'da_schedule["da_pf_depreciation", @col]',
        pre_vals=base.pre_close_depreciation,
    )
    add_is(
        "is_ebita",
        "EBITA",
        'income_statement["is_ebitda", @col] - income_statement["is_depreciation", @col]',
        "subtotal",
    )
    add_is(
        "is_amortization",
        "Amortization",
        'da_schedule["da_pf_amortization", @col]',
        pre_vals=base.pre_close_amortization,
    )
    add_is(
        "is_sbc",
        "Stock-based compensation",
        'income_statement["is_net_sales", @col] * operating_schedule["active_sbc_pct_sales", @col]',
        pre_vals=base.pre_close_sbc,
    )
    add_is(
        "is_ebit",
        "EBIT",
        'income_statement["is_ebita", @col] - income_statement["is_amortization", @col] - income_statement["is_sbc", @col]',
        "subtotal",
    )

    add_is(
        "is_interest_cash",
        "Interest expense - Cash",
        '-debt_sweep_schedule["cash_interest_rate", "pf_close"] * balance_sheet["bs_cash", col.prev] * income_statement["is_fractional_years", @col]',
        pre_vals=base.pre_close_interest_income,
    )
    int_labels: dict[str, str] = {
        "is_interest_existing_debt": "Interest expense - Existing debt",
        "is_interest_revolver": "Interest expense - Revolver",
        "is_interest_term_loan_a": "Interest expense - Term loan - A",
        "is_interest_term_loan_b": "Interest expense - Term loan - B",
        "is_interest_senior_note": "Interest expense - Senior note",
        "is_interest_subordinated_note": "Interest expense - Subordinated note",
        "is_interest_mezzanine": "Interest expense - Mezzanine",
        "is_interest_seller_note": "Interest expense - Seller note",
        "is_interest_convertible_bond": "Interest expense - Convertible bond",
        "is_interest_debt_8": "Interest expense - [Debt 8]",
    }
    for tk in DEBT_TRANCHE_KEYS:
        int_r, int_e = IS_DEBT_INTEREST_ROWS[tk]
        if tk == "legacy_debt":
            add_is(int_r, int_labels[int_r], int_e, mrq_val=base.mrq_interest_existing_debt)
        else:
            add_is(int_r, int_labels[int_r], int_e, pre_expr="0")

    add_is(
        "is_interest_expense_net",
        "Interest (income) / expense",
        'SUM(income_statement["is_interest_cash".."is_interest_debt_8", @col])',
        "subtotal",
    )
    add_is(
        "is_amort_deferred_financing",
        "Amortization of capitalized financing costs",
        'da_schedule["da_amort_financing_costs_total", @col]',
        pre_expr="0",
    )
    add_is(
        "is_loss_unamortized_oid",
        "Loss on unamortized OID at repayment",
        'debt_sweep_schedule["debt_total_oid_loss", @col]',
        pre_expr="0",
    )
    add_is(
        "is_equity_income_affiliates",
        "Equity income in affiliates",
        "0",
        pre_vals=base.pre_close_equity_income,
    )
    add_is(
        "is_sponsor_mgmt_fee",
        "Sponsor management fee",
        'dashboard_entry_valuation["sponsor_management_fee", "metric_value"] * sources_uses["lbo_flag", "active_case"] * income_statement["is_fractional_years", @col]',
        pre_expr="0",
    )
    add_is(
        "is_other_income_expense",
        "Other (income) / expense",
        "0",
        pre_vals=base.pre_close_non_operating_income,
    )
    add_is(
        "is_ebt",
        "Income before tax",
        'income_statement["is_ebit", @col] - SUM(income_statement["is_interest_expense_net".."is_other_income_expense", @col])',
        "subtotal",
    )
    add_is(
        "is_tax_provision",
        "Provision for tax",
        'income_statement["is_ebt", @col] * nol_amt_schedule["blended_tax_rate", @col]',
        mrq_val=base.mrq_tax_provision,
    )
    add_is(
        "is_gaap_net_income",
        "GAAP net income",
        'income_statement["is_ebt", @col] - income_statement["is_tax_provision", @col]',
        "subtotal",
    )
    add_is(
        "is_pref_a_dividend",
        "Preferred stock - A dividend",
        'debt_sweep_schedule["debt_preferred_a_book_interest", @col]',
        pre_vals=base.pre_close_preferred_dividend,
    )
    add_is(
        "is_pref_b_dividend",
        "Preferred stock - B dividend",
        'debt_sweep_schedule["debt_preferred_b_book_interest", @col]',
        pre_expr="0",
    )
    add_is(
        "is_noncontrolling_interest",
        "Noncontrolling (minority) interest",
        "0",
        pre_vals=base.pre_close_noncontrolling_interest,
    )
    add_is(
        "is_gaap_net_income_common",
        "GAAP net income available to common",
        'income_statement["is_gaap_net_income", @col] - SUM(income_statement["is_pref_a_dividend".."is_noncontrolling_interest", @col])',
        "total",
    )

    add_is(
        "is_after_tax_amortization",
        "Amortization, after-tax",
        'income_statement["is_amortization", @col] * (1 - income_statement["is_effective_tax_rate", @col])',
    )
    add_is(
        "is_after_tax_sbc",
        "Stock-based comp, after-tax",
        'income_statement["is_sbc", @col] * (1 - income_statement["is_effective_tax_rate", @col])',
    )
    add_is(
        "is_after_tax_deferred_financing",
        "Amortization of capitalized financing costs, after-tax",
        'income_statement["is_amort_deferred_financing", @col] * (1 - income_statement["is_effective_tax_rate", @col])',
    )
    add_is("is_after_tax_one_time", "One-time charges, after-tax", "0")
    add_is(
        "is_cash_net_income_common",
        "Cash net income available to common",
        'SUM(income_statement["is_gaap_net_income_common".."is_after_tax_one_time", @col])',
        "total",
    )

    eps_block_specs: tuple[
        tuple[str, str, str, str, str, str, str, str, str, str, str],
        ...,
    ] = (
        (
            "is_standalone_gaap_eps",
            "Standalone GAAP EPS",
            "is_pf_gaap_eps",
            "Pro forma GAAP EPS",
            "is_gaap_accretion_dollars",
            "GAAP accretion / (dilution) ($)",
            "is_gaap_accretion_pct",
            "GAAP accretion / (dilution) (%)",
            'income_statement["is_gaap_net_income_common", @col] / valuation_and_fdso["fdso_treasury", "value"]',
            'IF(sources_uses["case_number", "active_case"] = 1, income_statement["is_gaap_net_income_common", @col] / convertible_fdso_schedule["fdso", @col], operating_schedule["standalone_gaap_eps_input", @col])',
            'IF(sources_uses["lbo_flag", "active_case"] = 1, "NM", income_statement["is_gaap_net_income_common", @col] / convertible_fdso_schedule["fdso", @col])',
        ),
        (
            "is_standalone_cash_eps",
            "Standalone cash EPS",
            "is_pf_cash_eps",
            "Pro forma cash EPS",
            "is_cash_accretion_dollars",
            "Cash accretion / (dilution) ($)",
            "is_cash_accretion_pct",
            "Cash accretion / (dilution) (%)",
            'income_statement["is_cash_net_income_common", @col] / valuation_and_fdso["fdso_treasury", "value"]',
            'IF(sources_uses["case_number", "active_case"] = 1, income_statement["is_cash_net_income_common", @col] / convertible_fdso_schedule["fdso", @col], operating_schedule["standalone_cash_eps_input", @col])',
            'IF(sources_uses["lbo_flag", "active_case"] = 1, "NM", income_statement["is_cash_net_income_common", @col] / convertible_fdso_schedule["fdso", @col])',
        ),
    )
    for (
        std_r,
        std_lbl,
        pf_r,
        pf_lbl,
        acc_d_r,
        acc_d_lbl,
        acc_p_r,
        acc_p_lbl,
        std_pre_expr,
        std_post_expr,
        pf_post_expr,
    ) in eps_block_specs:
        std_cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_IS_COLS, None)
        std_cells["label"] = std_lbl
        table.add_row(
            std_r,
            cells=std_cells,
            expr=std_pre_expr,
            format="currency",
            decimals=2,
        )
        table.set_cells(std_r, slice(STUB_PERIOD_KEY, FINAL_PERIOD_KEY), expr=std_post_expr)

        pf_cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_IS_COLS, None)
        pf_cells["label"] = pf_lbl
        for col_id in PRE_CLOSE_ALL_COLS:
            pf_cells[col_id] = "NA"
        table.add_row(
            pf_r,
            cells=pf_cells,
            expr=pf_post_expr,
            format="currency",
            decimals=2,
        )

        acc_d_cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_IS_COLS, None)
        acc_d_cells["label"] = acc_d_lbl
        acc_p_cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_IS_COLS, None)
        acc_p_cells["label"] = acc_p_lbl
        for col_id in PRE_CLOSE_ALL_COLS:
            acc_d_cells[col_id] = "NA"
            acc_p_cells[col_id] = "NA"
        table.add_row(acc_d_r, cells=acc_d_cells, format="currency", decimals=2)
        table.add_row(acc_p_r, cells=acc_p_cells, format="percentage", decimals=2)
        table.set_cells(
            acc_d_r,
            slice(CONCURRENT_PROJECTION_KEYS[0], CONCURRENT_PROJECTION_KEYS[-1]),
            expr='IF(sources_uses["lbo_flag", "active_case"] = 1, "NM", income_statement[row.prev, @col] - income_statement[row.prev(2), @col])',
        )
        table.set_cells(
            acc_p_r,
            slice(CONCURRENT_PROJECTION_KEYS[0], CONCURRENT_PROJECTION_KEYS[-1]),
            expr='IF(sources_uses["lbo_flag", "active_case"] = 1, "NM", (income_statement[row.prev(2), @col] - income_statement[row.prev(3), @col]) / income_statement[row.prev(3), @col])',
        )
        table.set_cells(
            (acc_d_r, acc_p_r),
            slice(POST_CLOSE_PERIOD_KEYS[5], FINAL_PERIOD_KEY),
            value="NA",
        )

    add_is(
        "is_capex",
        "Capital expenditures",
        'income_statement["is_net_sales", @col] * operating_schedule["active_capex_pct_sales", @col]',
        pre_vals=base.pre_close_capex,
    )
    add_is(
        "is_common_dividend_per_share",
        "Common stock dividend per share",
        'income_statement["is_common_dividend_per_share", "mrq_plus_3"] * (1 - sources_uses["lbo_flag", "active_case"])',
        dec=2,
        pre_vals=base.pre_close_common_dividend_per_share,
    )

    add_is(
        "is_sales_growth",
        "Sales growth",
        'operating_schedule["active_sales_growth", @col]',
        fmt="percentage",
        dec=2,
        pre_expr='((income_statement["is_net_sales", @col] / income_statement["is_net_sales", col.prev]) - 1) / income_statement["is_fractional_years", @col]',
        mrq_expr='((income_statement["is_net_sales", "mrq"] / operating_schedule["prior_quarter_sales", "mrq"]) - 1) / income_statement["is_fractional_years", "mrq"]',
    )
    for eg_id, eg_lbl, eg_expr in (
        (
            "is_gaap_earnings_growth",
            "GAAP earnings growth",
            '(((income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]) / (income_statement["is_gaap_net_income_common", col.prev] / income_statement["is_fractional_years", col.prev])) - 1) / income_statement["is_fractional_years", @col]',
        ),
        (
            "is_cash_earnings_growth",
            "Cash earnings growth",
            '(((income_statement["is_cash_net_income_common", @col] / income_statement["is_fractional_years", @col]) / (income_statement["is_cash_net_income_common", col.prev] / income_statement["is_fractional_years", col.prev])) - 1) / income_statement["is_fractional_years", @col]',
        ),
    ):
        eg_cells: dict[str, f8.CellInputValue] = dict.fromkeys(
            ("mrq", *INACTIVE_IS_COLS, STUB_PERIOD_KEY), None
        )
        eg_cells["label"] = eg_lbl
        table.add_row(
            eg_id,
            cells=eg_cells,
            expr=eg_expr,
            format="percentage",
            decimals=2,
        )

    post_ratio_rows: tuple[tuple[str, str, str, str | None, str | None], ...] = (
        (
            "is_cogs_pct_sales",
            "COGS / sales",
            'income_statement["is_cogs", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_sga_pct_sales",
            "SG&A / sales",
            'income_statement["is_sga", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_depr_pct_sales",
            "Depreciation / sales",
            'income_statement["is_depreciation", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_amort_pct_sales",
            "Amortization / sales",
            'income_statement["is_amortization", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_sbc_pct_sales",
            "Stock-based compensation / sales",
            'income_statement["is_sbc", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_capex_pct_sales",
            "Capex / sales",
            'income_statement["is_capex", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_cogs_savings_phase_in",
            "COGS cost savings phase-in",
            'operating_schedule["cogs_savings_phase_in", @col]',
            "0",
            None,
        ),
        (
            "is_sga_savings_phase_in",
            "SG&A cost savings phase-in",
            'operating_schedule["sga_savings_phase_in", @col]',
            "0",
            None,
        ),
        (
            "is_gross_margin",
            "Gross margin",
            'income_statement["is_gross_profit", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_ebitda_margin",
            "EBITDA margin",
            'income_statement["is_ebitda", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_ebita_margin",
            "EBITA margin",
            'income_statement["is_ebita", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_ebit_margin",
            "EBIT margin",
            'income_statement["is_ebit", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_gaap_net_margin",
            "GAAP net margin",
            'income_statement["is_gaap_net_income_common", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_cash_net_margin",
            "Cash net margin",
            'income_statement["is_cash_net_income_common", @col] / income_statement["is_net_sales", @col]',
            None,
            None,
        ),
        (
            "is_roic",
            "ROIC",
            'credit_stats["credit_roic", @col]',
            '((income_statement["is_gaap_net_income", @col] + income_statement["is_interest_expense_net", @col]) / income_statement["is_fractional_years", @col]) / (balance_sheet["bs_total_debt", @col] + balance_sheet["bs_noncontrolling_interest", @col] + balance_sheet["bs_total_equity", @col])',
            None,
        ),
        (
            "is_roe",
            "ROE",
            'credit_stats["credit_roe", @col]',
            '(income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]) / SUM(balance_sheet["bs_common_stock_par".."bs_retained_earnings", @col])',
            None,
        ),
        (
            "is_roa",
            "ROA",
            'credit_stats["credit_roa", @col]',
            '(income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]) / balance_sheet["bs_total_assets", @col]',
            None,
        ),
        (
            "is_effective_tax_rate",
            "Tax rate",
            'nol_amt_schedule["blended_tax_rate", @col]',
            None,
            'income_statement["is_tax_provision", "mrq"] / income_statement["is_ebt", "mrq"]',
        ),
    )
    for r_id, r_lbl, r_expr, pre_r_expr, mrq_r_expr in post_ratio_rows:
        add_is(
            r_id,
            r_lbl,
            r_expr,
            fmt="percentage",
            dec=2,
            pre_expr=pre_r_expr,
            mrq_expr=mrq_r_expr,
        )
    return table


def build_cash_flow_statement(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the unified 18-column `cash_flow_statement` table."""
    del assumptions
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "cash_flow_statement", "Cash Flow Statement", subtitle=sub, currency="USD"
    )
    add_timeline_columns(table, "Cash Flow Line Item")
    for r_id, lbl, expr, pre_expr, style in CASH_FLOW_ROWS:
        cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_CF_COLS, None)
        cells["label"] = lbl
        table.add_row(
            r_id,
            cells=cells,
            expr=expr,
            style=style,
            format="currency",
            decimals=3,
        )
        if pre_expr is not None:
            table.set_cells(r_id, slice("mrq_plus_1", "mrq_plus_4"), expr=pre_expr, style=style)
    return table


def build_balance_sheet(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the unified 18-column `balance_sheet` table."""
    base = assumptions.baseline
    sub = "Units: $ in millions"
    table = sheet.add_table("balance_sheet", "Balance Sheet", subtitle=sub, currency="USD")
    add_timeline_columns(table, "Balance Sheet Line Item")

    non_vertical_bs_rows = tuple(
        acc.bs_row_id for acc in BALANCE_SHEET_ACCOUNTS if not acc.is_vertical_calc
    )
    for acc in BALANCE_SHEET_ACCOUNTS:
        cells: dict[str, f8.CellInputValue] = {"label": acc.label}
        if not acc.is_vertical_calc:
            cells["mrq"] = f8.Cell(
                value=base.get_mrq_bs_balance(acc.tx_row_id),
                style="data",
                format="currency",
                decimals=3,
            )
            cells["pf_close"] = f8.Cell(expr=f'transaction_bs["{acc.tx_row_id}", "pf_close"]')
        table.add_row(
            acc.bs_row_id,
            cells=cells,
            expr=BALANCE_SHEET_EXPRS[acc.bs_row_id],
            style=acc.style,
            format="currency",
            decimals=3,
        )
    table.set_cells(
        NEW_TRANCHE_BS_ROWS,
        slice("mrq_plus_1", "mrq_plus_4"),
        expr="balance_sheet[@row, col.prev]",
    )
    table.set_cells(
        non_vertical_bs_rows,
        "standalone_close",
        expr='balance_sheet[@row, "mrq_plus_3"]',
    )
    table.set_cells(
        non_vertical_bs_rows,
        "deal_adjustments",
        expr='balance_sheet[@row, "pf_close"] - balance_sheet[@row, "standalone_close"]',
    )
    return table
