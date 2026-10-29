"""Unified 18-column Credit Statistics & Financial Ratios schedule builder."""

from __future__ import annotations

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.timeline import PRE_PF_COLS, add_timeline_columns


def build_credit_stats(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the 18-column `credit_stats` Summary Credit Statistics and Financial Ratios schedule."""
    del assumptions
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "credit_stats", "Summary Credit Statistics & Financial Ratios", subtitle=sub, currency="USD"
    )
    add_timeline_columns(table, "Credit Metric / Ratio")

    def add_cr(
        r_id: str,
        lbl: str,
        expr: str,
        pf_expr: str | None = None,
        style: f8.SemanticStyle | None = None,
        fmt: f8.FormatPreset = "currency",
        dec: int = 3,
    ) -> None:
        inactive_cols = (*PRE_PF_COLS, "pf_close") if pf_expr is None else PRE_PF_COLS
        cells: dict[str, f8.CellInputValue] = dict.fromkeys(inactive_cols, None)
        cells["label"] = lbl
        table.add_row(r_id, cells=cells, expr=expr, style=style, format=fmt, decimals=dec)
        if pf_expr is not None:
            table.set_cell(r_id, "pf_close", expr=pf_expr, style=style, format=fmt, decimals=dec)

    add_cr(
        "credit_ebitda_annualized",
        "EBITDA (annualized)",
        'income_statement["is_ebitda", @col] / income_statement["is_fractional_years", @col]',
        pf_expr='SUM(income_statement["is_ebitda", "mrq".."mrq_plus_3"])',
    )
    add_cr(
        "credit_capex_annualized",
        "Capex (annualized)",
        'income_statement["is_capex", @col] / income_statement["is_fractional_years", @col]',
        pf_expr='SUM(income_statement["is_capex", "mrq".."mrq_plus_3"])',
    )
    add_cr(
        "credit_change_in_wc",
        "Increase / (decrease) in working capital",
        '-cash_flow_statement["cf_change_in_wc", @col] / income_statement["is_fractional_years", @col]',
    )

    sen_debt_e = (
        'balance_sheet["bs_short_term_debt", @col] + '
        'SUMPRODUCT(balance_sheet["bs_existing_lt_debt".."bs_debt_8", @col], tranche_fees_oid["legacy_debt".."debt_8", "is_senior"]) + '
        'SUMPRODUCT(balance_sheet["bs_preferred_a".."bs_preferred_b", @col], tranche_fees_oid["preferred_a".."preferred_b", "is_senior"])'
    )
    sub_debt_e = (
        'SUM(balance_sheet["bs_existing_lt_debt".."bs_debt_8", @col]) - '
        'SUMPRODUCT(balance_sheet["bs_existing_lt_debt".."bs_debt_8", @col], tranche_fees_oid["legacy_debt".."debt_8", "is_senior"])'
    )
    pref_e = 'balance_sheet["bs_preferred_a", @col] + balance_sheet["bs_preferred_b", @col]'
    nci_e = 'balance_sheet["bs_noncontrolling_interest", @col]'
    leases_e = 'balance_sheet["bs_capital_leases", @col]'
    tot_debt_e = 'SUM(credit_stats["credit_senior_debt".."credit_capital_leases", @col])'
    cash_e = 'balance_sheet["bs_cash", @col]'
    net_debt_e = 'credit_stats["credit_total_debt", @col] - credit_stats["credit_less_cash", @col]'

    add_cr("credit_senior_debt", "Senior debt", sen_debt_e, pf_expr=sen_debt_e)
    add_cr("credit_subordinated_debt", "Subordinated debt", sub_debt_e, pf_expr=sub_debt_e)
    add_cr("credit_preferred_stock", "Preferred stock", pref_e, pf_expr=pref_e)
    add_cr(
        "credit_noncontrolling_interest",
        "Noncontrolling (minority) interest",
        nci_e,
        pf_expr=nci_e,
    )
    add_cr("credit_capital_leases", "Capital leases", leases_e, pf_expr=leases_e)
    add_cr(
        "credit_total_debt",
        "Total debt (incl. preferred)",
        tot_debt_e,
        pf_expr=tot_debt_e,
        style="subtotal",
    )
    add_cr("credit_less_cash", "( – ) Cash", cash_e, pf_expr=cash_e)
    add_cr("credit_net_debt", "Net debt", net_debt_e, pf_expr=net_debt_e, style="total")

    add_cr(
        "credit_senior_interest",
        "Senior interest expense",
        'SUMPRODUCT(income_statement["is_interest_existing_debt".."is_interest_debt_8", @col], tranche_fees_oid["legacy_debt".."debt_8", "is_senior"]) / income_statement["is_fractional_years", @col]',
    )
    add_cr(
        "credit_subordinated_interest",
        "Subordinated interest expense",
        '(SUM(income_statement["is_interest_existing_debt".."is_interest_debt_8", @col]) - SUMPRODUCT(income_statement["is_interest_existing_debt".."is_interest_debt_8", @col], tranche_fees_oid["legacy_debt".."debt_8", "is_senior"])) / income_statement["is_fractional_years", @col]',
    )
    add_cr(
        "credit_preferred_dividends",
        "Preferred dividends",
        '(income_statement["is_pref_a_dividend", @col] + income_statement["is_pref_b_dividend", @col]) / income_statement["is_fractional_years", @col]',
    )
    add_cr(
        "credit_total_fixed_charges",
        "Total fixed charges",
        'SUM(credit_stats["credit_senior_interest".."credit_preferred_dividends", @col])',
        style="subtotal",
    )
    add_cr(
        "credit_cash_interest",
        "Cash interest expense",
        'credit_stats["credit_senior_interest", @col] + credit_stats["credit_subordinated_interest", @col] - (SUM(cash_flow_statement["cf_pik_subordinated_note".."cf_pik_debt_8", @col]) / income_statement["is_fractional_years", @col])',
    )

    td_ebitda = 'IFERROR(credit_stats["credit_total_debt", @col] / credit_stats["credit_ebitda_annualized", @col], 0)'
    sd_ebitda = 'IFERROR(credit_stats["credit_senior_debt", @col] / credit_stats["credit_ebitda_annualized", @col], 0)'
    nd_ebitda = 'IFERROR(credit_stats["credit_net_debt", @col] / credit_stats["credit_ebitda_annualized", @col], 0)'
    td_eb_cx = 'IFERROR(credit_stats["credit_total_debt", @col] / (credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col]), 0)'
    add_cr(
        "credit_total_debt_to_ebitda",
        "Total debt / EBITDA",
        td_ebitda,
        pf_expr=td_ebitda,
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_senior_debt_to_ebitda",
        "Senior debt / EBITDA",
        sd_ebitda,
        pf_expr=sd_ebitda,
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_net_debt_to_ebitda",
        "Net debt / EBITDA",
        nd_ebitda,
        pf_expr=nd_ebitda,
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_total_debt_to_ebitda_less_capex",
        "Total debt / EBITDA – capex",
        td_eb_cx,
        pf_expr=td_eb_cx,
        fmt="number",
        dec=2,
    )

    coverage_rows: tuple[tuple[str, str, str], ...] = (
        (
            "credit_ebitda_to_senior_interest",
            "EBITDA / senior interest",
            'IFERROR(credit_stats["credit_ebitda_annualized", @col] / credit_stats["credit_senior_interest", @col], 0)',
        ),
        (
            "credit_ebitda_to_total_interest",
            "EBITDA / total interest",
            'IFERROR(credit_stats["credit_ebitda_annualized", @col] / credit_stats["credit_total_fixed_charges", @col], 0)',
        ),
        (
            "credit_ebitda_to_cash_interest",
            "EBITDA / cash interest",
            'IFERROR(credit_stats["credit_ebitda_annualized", @col] / credit_stats["credit_cash_interest", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_to_senior_int",
            "EBITDA – capex / senior interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col]) / credit_stats["credit_senior_interest", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_to_total_int",
            "EBITDA – capex / total interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col]) / credit_stats["credit_total_fixed_charges", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_to_cash_int",
            "EBITDA – capex / cash interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col]) / credit_stats["credit_cash_interest", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_wc_to_senior_int",
            "EBITDA – capex – Δ WC / senior interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col] - credit_stats["credit_change_in_wc", @col]) / credit_stats["credit_senior_interest", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_wc_to_total_int",
            "EBITDA – capex – Δ WC / total interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col] - credit_stats["credit_change_in_wc", @col]) / credit_stats["credit_total_fixed_charges", @col], 0)',
        ),
        (
            "credit_ebitda_less_capex_wc_to_cash_int",
            "EBITDA – capex – Δ WC / cash interest",
            'IFERROR((credit_stats["credit_ebitda_annualized", @col] - credit_stats["credit_capex_annualized", @col] - credit_stats["credit_change_in_wc", @col]) / credit_stats["credit_cash_interest", @col], 0)',
        ),
    )
    for r_id, lbl, cov_expr in coverage_rows:
        add_cr(r_id, lbl, cov_expr, fmt="number", dec=2)

    add_cr(
        "credit_cum_senior_debt_paydown",
        "Cumulative senior debt paydown",
        'IFERROR((credit_stats["credit_senior_debt", "pf_close"] - credit_stats["credit_senior_debt", @col]) / credit_stats["credit_senior_debt", "pf_close"], 0)',
        fmt="percentage",
        dec=2,
    )
    add_cr(
        "credit_cum_total_debt_paydown",
        "Cumulative debt paydown (excl. preferred)",
        'IFERROR((balance_sheet["bs_total_debt", "pf_close"] - balance_sheet["bs_total_debt", @col]) / balance_sheet["bs_total_debt", "pf_close"], 0)',
        fmt="percentage",
        dec=2,
    )
    add_cr(
        "credit_roic",
        "ROIC",
        '((income_statement["is_gaap_net_income", @col] + income_statement["is_interest_expense_net", @col]) / income_statement["is_fractional_years", @col]) / (balance_sheet["bs_total_debt", @col] + balance_sheet["bs_noncontrolling_interest", @col] + balance_sheet["bs_total_equity", @col])',
        fmt="percentage",
        dec=2,
    )
    add_cr(
        "credit_roe",
        "ROE",
        '(income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]) / SUM(balance_sheet["bs_common_stock_par".."bs_retained_earnings", @col])',
        fmt="percentage",
        dec=2,
    )
    add_cr(
        "credit_roa",
        "ROA",
        '(income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]) / balance_sheet["bs_total_assets", @col]',
        fmt="percentage",
        dec=2,
    )

    cr_e = 'balance_sheet["bs_total_current_assets", @col] / balance_sheet["bs_total_current_liabilities", @col]'
    qr_e = '(balance_sheet["bs_cash", @col] + balance_sheet["bs_accounts_receivable", @col]) / balance_sheet["bs_total_current_liabilities", @col]'
    add_cr("credit_current_ratio", "Current ratio", cr_e, pf_expr=cr_e, fmt="number", dec=2)
    add_cr(
        "credit_quick_ratio", "Quick ('Acid Test') ratio", qr_e, pf_expr=qr_e, fmt="number", dec=2
    )

    add_cr(
        "credit_total_asset_turnover",
        "Total asset turnover",
        '(income_statement["is_net_sales", @col] / income_statement["is_fractional_years", @col]) / ((balance_sheet["bs_total_assets", col.prev] + balance_sheet["bs_total_assets", @col]) / 2)',
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_fixed_asset_turnover",
        "Fixed asset turnover",
        '(income_statement["is_net_sales", @col] / income_statement["is_fractional_years", @col]) / ((balance_sheet["bs_ppe_net", col.prev] + balance_sheet["bs_ppe_net", @col]) / 2)',
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_ar_turnover",
        "Accounts receivable turnover",
        '(income_statement["is_net_sales", @col] / income_statement["is_fractional_years", @col]) / ((balance_sheet["bs_accounts_receivable", col.prev] + balance_sheet["bs_accounts_receivable", @col]) / 2)',
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_ap_turnover",
        "Accounts payable turnover",
        '(working_capital_schedule["wc_purchases", @col] / income_statement["is_fractional_years", @col]) / ((balance_sheet["bs_accounts_payable", col.prev] + balance_sheet["bs_accounts_payable", @col]) / 2)',
        fmt="number",
        dec=2,
    )
    add_cr(
        "credit_days_receivable",
        "Days receivable",
        '365 / credit_stats["credit_ar_turnover", @col]',
        fmt="number",
        dec=1,
    )
    add_cr(
        "credit_days_payable",
        "Days payable",
        '365 / credit_stats["credit_ap_turnover", @col]',
        fmt="number",
        dec=1,
    )
    return table
