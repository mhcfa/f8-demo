"""Unified 18-column Working Capital Schedule builder."""

from __future__ import annotations

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.timeline import add_timeline_columns

INACTIVE_CF_COLS: tuple[str, ...] = (
    "mrq",
    "standalone_close",
    "deal_adjustments",
    "pf_close",
)


def build_working_capital_schedule(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the unified 18-column `working_capital_schedule` table."""
    del assumptions
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "working_capital_schedule", "Working Capital Schedule", subtitle=sub, currency="USD"
    )
    add_timeline_columns(table, "Working Capital Line Item")

    ca_items: tuple[tuple[str, str, str, str], ...] = (
        (
            "wc_accounts_receivable",
            "Accounts receivable",
            '(working_capital_schedule["wc_ar_pct_sales", @col] * working_capital_schedule["wc_sales", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_accounts_receivable", "mrq"]',
        ),
        (
            "wc_inventories",
            "Inventories",
            '(working_capital_schedule["wc_inv_pct_cogs", @col] * working_capital_schedule["wc_cogs", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_inventories", "mrq"]',
        ),
        (
            "wc_dta_current",
            "Deferred tax asset, current",
            '(working_capital_schedule["wc_dta_pct_sales", @col] * working_capital_schedule["wc_sales", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_dta_current", "mrq"]',
        ),
        (
            "wc_prepaid_expenses",
            "Prepaid expenses & other",
            '(working_capital_schedule["wc_prepaid_pct_cogs", @col] * working_capital_schedule["wc_cogs", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_prepaid_expenses", "mrq"]',
        ),
    )
    cl_items: tuple[tuple[str, str, str, str], ...] = (
        (
            "wc_accounts_payable",
            "Accounts payable",
            '(working_capital_schedule["wc_ap_pct_cogs", @col] * working_capital_schedule["wc_cogs", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_accounts_payable", "mrq"]',
        ),
        (
            "wc_accrued_liabilities",
            "Accrued liabilities",
            '(working_capital_schedule["wc_accrued_pct_cogs", @col] * working_capital_schedule["wc_cogs", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_accrued_liabilities", "mrq"]',
        ),
        (
            "wc_client_deposits",
            "Client deposits",
            '(working_capital_schedule["wc_deposits_pct_sales", @col] * working_capital_schedule["wc_sales", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_client_deposits", "mrq"]',
        ),
        (
            "wc_other_current_liabilities",
            "Other current liabilities",
            '(working_capital_schedule["wc_other_cl_pct_cogs", @col] * working_capital_schedule["wc_cogs", @col]) / income_statement["is_fractional_years", @col]',
            'balance_sheet["bs_other_current_liabilities", "mrq"]',
        ),
    )

    for wc_r, wc_lbl, wc_expr, mrq_expr in ca_items:
        table.add_row(
            wc_r,
            cells={"label": wc_lbl, "mrq": f8.Cell(expr=mrq_expr)},
            expr=wc_expr,
            format="currency",
            decimals=3,
        )

    table.add_row(
        "wc_non_cash_current_assets",
        cells={"label": "Non-cash current assets"},
        expr='SUM(working_capital_schedule["wc_accounts_receivable".."wc_prepaid_expenses", @col])',
        style="subtotal",
        format="currency",
        decimals=3,
    )

    for wc_r, wc_lbl, wc_expr, mrq_expr in cl_items:
        table.add_row(
            wc_r,
            cells={"label": wc_lbl, "mrq": f8.Cell(expr=mrq_expr)},
            expr=wc_expr,
            format="currency",
            decimals=3,
        )

    wc_balance_rows = (
        *(wc_r for wc_r, _, _, _ in ca_items),
        *(wc_r for wc_r, _, _, _ in cl_items),
    )
    table.set_cells(
        wc_balance_rows,
        "standalone_close",
        expr='working_capital_schedule[@row, "mrq_plus_3"]',
    )
    table.set_cells(
        wc_balance_rows,
        "deal_adjustments",
        expr='working_capital_schedule[@row, "pf_close"] - working_capital_schedule[@row, "standalone_close"]',
    )
    table.set_cells(
        wc_balance_rows,
        "pf_close",
        expr='working_capital_schedule[@row, "standalone_close"]',
    )

    table.add_row(
        "wc_non_debt_current_liabilities",
        cells={"label": "Non-debt current liabilities"},
        expr='SUM(working_capital_schedule["wc_accounts_payable".."wc_other_current_liabilities", @col])',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.add_row(
        "wc_net_working_capital",
        cells={"label": "Net working capital"},
        expr='working_capital_schedule["wc_non_cash_current_assets", @col] - working_capital_schedule["wc_non_debt_current_liabilities", @col]',
        style="total",
        format="currency",
        decimals=3,
    )

    table.add_row(
        "wc_sales",
        cells={"label": "Sales", "deal_adjustments": None},
        expr='income_statement["is_net_sales", @col]',
        format="currency",
        decimals=3,
    )

    table.add_row(
        "wc_cogs",
        cells={"label": "COGS", "deal_adjustments": None},
        expr='income_statement["is_cogs", @col]',
        format="currency",
        decimals=3,
    )

    table.add_row(
        "wc_purchases",
        cells={"label": "Purchases", "mrq": None, "deal_adjustments": None},
        expr='working_capital_schedule["wc_cogs", @col] + working_capital_schedule["wc_inventories", @col] - working_capital_schedule["wc_inventories", col.prev]',
        format="currency",
        decimals=3,
    )

    ratio_specs: tuple[tuple[str, str, str], ...] = (
        (
            "wc_ar_pct_sales",
            "Accounts receivable / sales",
            '(working_capital_schedule["wc_accounts_receivable", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_sales", "mrq"]',
        ),
        (
            "wc_inv_pct_cogs",
            "Inventories / COGS",
            '(working_capital_schedule["wc_inventories", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_cogs", "mrq"]',
        ),
        (
            "wc_dta_pct_sales",
            "Deferred tax asset, current / sales",
            '(working_capital_schedule["wc_dta_current", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_sales", "mrq"]',
        ),
        (
            "wc_prepaid_pct_cogs",
            "Prepaid expenses & other / COGS",
            '(working_capital_schedule["wc_prepaid_expenses", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_cogs", "mrq"]',
        ),
        (
            "wc_ap_pct_cogs",
            "Accounts payable / COGS",
            '(working_capital_schedule["wc_accounts_payable", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_cogs", "mrq"]',
        ),
        (
            "wc_accrued_pct_cogs",
            "Accrued liabilities / COGS",
            '(working_capital_schedule["wc_accrued_liabilities", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_cogs", "mrq"]',
        ),
        (
            "wc_deposits_pct_sales",
            "Client deposits / sales",
            '(working_capital_schedule["wc_client_deposits", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_sales", "mrq"]',
        ),
        (
            "wc_other_cl_pct_cogs",
            "Other current liabilities / COGS",
            '(working_capital_schedule["wc_other_current_liabilities", "mrq"] * income_statement["is_fractional_years", "mrq"]) / working_capital_schedule["wc_cogs", "mrq"]',
        ),
    )
    for ratio_id, ratio_lbl, mrq_expr in ratio_specs:
        table.add_row(
            ratio_id,
            cells={
                "label": ratio_lbl,
                "mrq": f8.Cell(expr=mrq_expr),
                "deal_adjustments": None,
            },
            expr="working_capital_schedule[@row, col.prev]",
            format="percentage",
            decimals=2,
        )
    table.set_cells(
        slice("wc_sales", "wc_other_cl_pct_cogs"),
        "standalone_close",
        expr='working_capital_schedule[@row, "mrq_plus_3"]',
    )
    table.set_cells(
        slice("wc_sales", "wc_other_cl_pct_cogs"),
        "pf_close",
        expr='working_capital_schedule[@row, "standalone_close"]',
    )

    for day_id, day_lbl, day_expr in (
        (
            "wc_ar_days",
            "Accounts receivable days",
            '((working_capital_schedule["wc_accounts_receivable", col.prev] + working_capital_schedule["wc_accounts_receivable", @col]) / 2) / (working_capital_schedule["wc_sales", @col] / income_statement["is_fractional_years", @col]) * 365',
        ),
        (
            "wc_ap_days",
            "Accounts payable days",
            '((working_capital_schedule["wc_accounts_payable", col.prev] + working_capital_schedule["wc_accounts_payable", @col]) / 2) / (working_capital_schedule["wc_purchases", @col] / income_statement["is_fractional_years", @col]) * 365',
        ),
        (
            "wc_inv_days",
            "Inventory days",
            '((working_capital_schedule["wc_inventories", col.prev] + working_capital_schedule["wc_inventories", @col]) / 2) / (working_capital_schedule["wc_cogs", @col] / income_statement["is_fractional_years", @col]) * 365',
        ),
    ):
        day_cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_CF_COLS, None)
        day_cells["label"] = day_lbl
        table.add_row(
            day_id,
            cells=day_cells,
            expr=day_expr,
            format="number",
            decimals=1,
        )
    return table
