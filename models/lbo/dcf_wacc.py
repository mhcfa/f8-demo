"""Pre-Deal CAPM Relevering, Pro Forma WACC, 10-Year UFCF & 5-Year XNPV DCF Valuation, and 8x3x3 Sensitivity Schedules."""

from __future__ import annotations

from dataclasses import dataclass

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.registry import TRANCHE_SPECS
from models.lbo.timeline import (
    DCF_PROJECTION_KEYS,
    EXIT_PERIOD_KEY,
    POST_CLOSE_PERIOD_KEYS,
    STUB_PERIOD_KEY,
    add_post_close_columns,
)

DCF_HORIZON_COLS: tuple[str, ...] = DCF_PROJECTION_KEYS
DCF_CF_COLS: tuple[str, ...] = ("pf_close", *DCF_HORIZON_COLS)
DCF_SCHEDULE_COL_KEYS: tuple[str, ...] = ("pf_close", *POST_CLOSE_PERIOD_KEYS)
SENS_VALUE_COLS: tuple[str, ...] = ("sens_col_1", "sens_col_2", "sens_col_3")
DCF_SENSITIVITY_COL_KEYS: tuple[str, ...] = ("discount_rate", *SENS_VALUE_COLS)
PRE_DEAL_CAPM_COL_KEYS: tuple[str, ...] = ("metric_value",)
WACC_COL_KEYS: tuple[str, ...] = (
    "wacc_amount",
    "wacc_taxability",
    "wacc_rate",
)

DEBT_TAXABILITY_EXPR = '1 - ppa_schedule["statutory_tax_rate", "active_case"]'

WACC_CAP_TRANCHES: tuple[tuple[str, str, str, str, str], ...] = tuple(
    (
        "wacc_cap_liquidation_of_options" if t.key == "legacy_debt" else f"wacc_cap_{t.key}",
        "WACC Capital Structure – Liquidation of options"
        if t.key == "legacy_debt"
        else f"WACC Capital Structure – {t.name}",
        f'balance_sheet["{t.bs_row_id}", "pf_close"]',
        "1" if t.is_preferred else DEBT_TAXABILITY_EXPR,
        f'debt_sweep_schedule["debt_rate_{t.key}", "{STUB_PERIOD_KEY}"]',
    )
    for t in TRANCHE_SPECS
)


@dataclass(frozen=True)
class SensitivityMatrixSpec:
    """Specification for an 8x3x3 DCF sensitivity matrix block."""

    row_ids: tuple[str, str, str]
    section_title: str
    cell_expr: str
    format: f8.FormatPreset
    decimals: int


def _add_pre_deal_capm_row(
    table: f8.Table,
    row_id: str,
    label: str,
    *,
    value: float | int | None = None,
    expr: str | None = None,
    style: f8.SemanticStyle | None = None,
    fmt: f8.FormatPreset = "currency",
    dec: int | None = 3,
) -> None:
    """Add a scalar metric row to `pre_deal_capm_schedule` populated in `metric_value`."""
    metric_cell = (
        f8.Cell(value=value, style=style or "data", format=fmt, decimals=dec)
        if value is not None
        else f8.Cell(expr=expr, style=style, format=fmt, decimals=dec)
    )
    table.add_row(
        row_id,
        cells={
            "label": label,
            "metric_value": metric_cell,
        },
        style=style,
        format=fmt,
        decimals=dec,
    )


def build_pre_deal_capm_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 17-row x 1-column `pre_deal_capm_schedule` Pre-Deal Dilution & CAPM Beta Relevering table."""
    deal = assumptions.deal
    fin = assumptions.financing
    sub = "Units: $ in millions / $ per share"
    table = sheet.add_table(
        "pre_deal_capm_schedule",
        "Pre-Deal Market Capitalization & CAPM Beta Relevering Schedule",
        subtitle=sub,
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="WACC / CAPM Line Item")
    table.add_column(
        "metric_value",
        headers=["WACC / CAPM", "Metric Value"],
    )

    # 1. Pre-Transaction Dilution & Market Capitalization (11 rows)
    table.add_section_header("Pre-Transaction Dilution & Market Capitalization")
    _add_pre_deal_capm_row(
        table,
        "wacc_current_stock_price",
        "Current stock price ($/sh)",
        expr='valuation_and_fdso["current_share_price", "value"]',
        fmt="currency",
        dec=2,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_conv_face_value",
        "Convertible debt – face value ($M)",
        expr='balance_sheet["bs_existing_lt_debt", "mrq"]',
        fmt="currency",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_conv_conversion_price",
        "Convertible debt – conversion price ($/sh)",
        value=fin.legacy_debt.conversion_price,
        fmt="currency",
        dec=2,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_conv_shares",
        "Convertible debt – shares if converted (M)",
        expr='IFERROR(pre_deal_capm_schedule["wacc_conv_face_value", "metric_value"] / pre_deal_capm_schedule["wacc_conv_conversion_price", "metric_value"], 0)',
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_bso",
        "Basic shares outstanding (BSO) (M)",
        expr='convertible_fdso_schedule["bso", "standalone_close"]',
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_treasury_method_shares",
        "Treasury method option shares (M)",
        expr='option_tranches["options_total", "treasury_method_shares"]',
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_itm_convertible_shares",
        "In-the-money convertible debt shares (M)",
        expr='IF(pre_deal_capm_schedule["wacc_conv_conversion_price", "metric_value"] > pre_deal_capm_schedule["wacc_current_stock_price", "metric_value"], 0, pre_deal_capm_schedule["wacc_conv_shares", "metric_value"])',
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_fdso",
        "Fully diluted shares outstanding (FDSO) (M)",
        expr='SUM(pre_deal_capm_schedule["wacc_bso".."wacc_itm_convertible_shares", "metric_value"])',
        style="subtotal",
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_pre_tx_mv_common_equity",
        "Pre-transaction MV of common equity ($M)",
        expr='pre_deal_capm_schedule["wacc_current_stock_price", "metric_value"] * pre_deal_capm_schedule["wacc_fdso", "metric_value"]',
        fmt="currency",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_pre_tx_mv_debt",
        "Pre-transaction MV of total debt ($M)",
        expr='balance_sheet["bs_short_term_debt", "standalone_close"] + IF(pre_deal_capm_schedule["wacc_conv_conversion_price", "metric_value"] > pre_deal_capm_schedule["wacc_current_stock_price", "metric_value"], pre_deal_capm_schedule["wacc_conv_face_value", "metric_value"], 0)',
        fmt="currency",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_pre_tx_mv_preferred",
        "Pre-transaction MV of preferred stock ($M)",
        expr="0",
        fmt="currency",
        dec=3,
    )

    # 2. CAPM Beta Relevering & Cost of Common Equity (6 rows)
    table.add_row_gutter()
    table.add_section_header("CAPM Beta Relevering & Cost of Common Equity")
    _add_pre_deal_capm_row(
        table,
        "wacc_pre_tx_levered_beta",
        "Pre-transaction levered beta",
        value=deal.pre_tx_levered_beta,
        fmt="number",
        dec=2,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_unlevered_beta",
        "Unlevered beta (asset beta)",
        expr='IFERROR(pre_deal_capm_schedule["wacc_pre_tx_levered_beta", "metric_value"] / (1 + (pre_deal_capm_schedule["wacc_pre_tx_mv_debt", "metric_value"] / pre_deal_capm_schedule["wacc_pre_tx_mv_common_equity", "metric_value"]) * (1 - ppa_schedule["statutory_tax_rate", "active_case"]) + (pre_deal_capm_schedule["wacc_pre_tx_mv_preferred", "metric_value"] / pre_deal_capm_schedule["wacc_pre_tx_mv_common_equity", "metric_value"])), 0)',
        style="subtotal",
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_risk_free_rate",
        "Risk-free rate (10-year Treasury)",
        value=deal.risk_free_rate,
        fmt="percentage",
        dec=2,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_market_risk_premium",
        "Equity market risk premium",
        value=deal.market_risk_premium,
        fmt="percentage",
        dec=2,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_relevered_beta",
        "Relevered beta (pro forma capital structure)",
        expr='IFERROR(pre_deal_capm_schedule["wacc_unlevered_beta", "metric_value"] * (1 + (SUM(wacc_schedule["wacc_cap_liquidation_of_options".."wacc_cap_debt_8", "wacc_amount"]) / wacc_schedule["wacc_cap_common_equity", "wacc_amount"]) * (1 - ppa_schedule["statutory_tax_rate", "active_case"]) + (SUM(wacc_schedule["wacc_cap_preferred_a".."wacc_cap_preferred_b", "wacc_amount"]) / wacc_schedule["wacc_cap_common_equity", "wacc_amount"])), 0)',
        style="subtotal",
        fmt="number",
        dec=3,
    )
    _add_pre_deal_capm_row(
        table,
        "wacc_capm_cost_of_equity",
        "CAPM cost of common equity",
        expr='pre_deal_capm_schedule["wacc_risk_free_rate", "metric_value"] + pre_deal_capm_schedule["wacc_market_risk_premium", "metric_value"] * pre_deal_capm_schedule["wacc_relevered_beta", "metric_value"]',
        style="subtotal",
        fmt="percentage",
        dec=2,
    )

    return table


def build_wacc_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 17-row x 3-column `wacc_schedule` Pro Forma Capital Structure & WACC table."""
    deal = assumptions.deal
    sub = "Units: $ in millions / $ per share"
    table = sheet.add_table(
        "wacc_schedule",
        "Pro Forma Capital Structure & Weighted Average Cost of Capital (WACC) Schedule",
        subtitle=sub,
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="WACC / Capital Structure Line Item")
    table.add_column(
        "wacc_amount",
        group="Pro Forma Capital Structure",
        headers=["Capital", "Amount ($M)"],
    )
    table.add_column(
        "wacc_taxability",
        group="Pro Forma Capital Structure",
        headers=["After-Tax", "Multiplier"],
    )
    table.add_column(
        "wacc_rate",
        group="Pro Forma Capital Structure",
        headers=["Pre-Tax", "Cost (%)"],
    )

    # 1. Pro Forma Capital Structure & Weighted Average Cost of Capital (14 rows)
    table.add_section_header("Pro Forma Capital Structure & Weighted Average Cost of Capital")
    for cap_r_id, cap_lbl, amount_expr, tax_expr, rate_expr in WACC_CAP_TRANCHES:
        table.add_row(
            cap_r_id,
            cells={
                "label": cap_lbl,
                "wacc_amount": f8.Cell(expr=amount_expr, format="currency", decimals=3),
                "wacc_taxability": f8.Cell(expr=tax_expr, format="number", decimals=2),
                "wacc_rate": f8.Cell(expr=rate_expr, format="percentage", decimals=2),
            },
            format="currency",
            decimals=3,
        )

    table.add_row(
        "wacc_cap_common_equity",
        cells={
            "label": "WACC Capital Structure – Common equity",
            "wacc_amount": f8.Cell(
                expr='SUM(balance_sheet["bs_common_stock_par".."bs_retained_earnings", "pf_close"])',
                format="currency",
                decimals=3,
            ),
            "wacc_taxability": f8.Cell(expr="1", format="number", decimals=2),
            "wacc_rate": f8.Cell(
                expr='pre_deal_capm_schedule["wacc_capm_cost_of_equity", "metric_value"]',
                format="percentage",
                decimals=2,
            ),
        },
        format="currency",
        decimals=3,
    )

    table.add_row(
        "wacc",
        cells={
            "label": "Weighted average cost of capital (WACC)",
            "wacc_amount": f8.Cell(
                expr='SUM(wacc_schedule["wacc_cap_liquidation_of_options".."wacc_cap_common_equity", "wacc_amount"])',
                style="total",
                format="currency",
                decimals=3,
            ),
            "wacc_taxability": None,
            "wacc_rate": f8.Cell(
                expr=(
                    "IFERROR("
                    'SUMPRODUCT(wacc_schedule["wacc_cap_liquidation_of_options".."wacc_cap_common_equity", "wacc_amount"], '
                    'wacc_schedule["wacc_cap_liquidation_of_options".."wacc_cap_common_equity", "wacc_taxability"], '
                    'wacc_schedule["wacc_cap_liquidation_of_options".."wacc_cap_common_equity", "wacc_rate"]) / '
                    'wacc_schedule["wacc", "wacc_amount"], '
                    "0)"
                ),
                style="total",
                format="percentage",
                decimals=2,
            ),
        },
        style="total",
    )

    # 2. Active Discount Rate Selection (3 rows)
    table.add_row_gutter()
    table.add_section_header("Active Discount Rate Selection")
    table.add_row(
        "manual_wacc",
        cells={
            "label": "Manual discount rate (WACC) input",
            "wacc_amount": None,
            "wacc_taxability": None,
            "wacc_rate": f8.Cell(
                value=deal.manual_wacc, style="data", format="percentage", decimals=2
            ),
        },
        style="data",
        format="percentage",
        decimals=2,
    )
    table.add_row(
        "wacc_selector",
        cells={
            "label": "Active WACC selector (1 = Manual, 2 = Calculated)",
            "wacc_amount": None,
            "wacc_taxability": None,
            "wacc_rate": f8.Cell(
                value=deal.wacc_selector, style="data", format="integer", decimals=None
            ),
        },
        style="data",
        format="integer",
        decimals=None,
    )
    table.add_row(
        "active_wacc",
        cells={
            "label": "Active discount rate (WACC)",
            "wacc_amount": None,
            "wacc_taxability": None,
            "wacc_rate": f8.Cell(
                expr='CHOOSE(wacc_schedule["wacc_selector", "wacc_rate"], wacc_schedule["manual_wacc", "wacc_rate"], wacc_schedule["wacc", "wacc_rate"])',
                style="total",
                format="percentage",
                decimals=2,
            ),
        },
        style="total",
        format="percentage",
        decimals=2,
    )

    return table


def _add_empty_dcf_schedule_row(
    table: f8.Table,
    row_id: str,
    label: str,
    style: f8.SemanticStyle | None = None,
    fmt: f8.FormatPreset = "currency",
    dec: int = 3,
) -> None:
    """Add a row to `dcf_schedule` initialized with None across all 11 timeline columns."""
    cells: dict[str, f8.CellInputValue] = {"label": label}
    for col_id in DCF_SCHEDULE_COL_KEYS:
        cells[col_id] = None
    table.add_row(row_id, cells=cells, style=style, format=fmt, decimals=dec)


def build_dcf_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 18-row x 11-column `dcf_schedule` 10-Year UFCF & 5-Year XNPV DCF Valuation table."""
    del assumptions
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "dcf_schedule",
        "10-Year Unlevered Free Cash Flow (UFCF) & 5-Year XNPV DCF Valuation",
        subtitle=sub,
        currency="USD",
    )
    add_post_close_columns(table, "UFCF / DCF Valuation Line Item")

    # 1. Unlevered Free Cash Flow (UFCF) Schedule (10 rows)
    table.add_section_header("Unlevered Free Cash Flow (UFCF) Schedule")
    table.add_row(
        "cumulative_fractional_years",
        cells={
            "label": "Cumulative fractional years",
            "pf_close": None,
            STUB_PERIOD_KEY: f8.Cell(
                expr=f'income_statement["is_fractional_years", "{STUB_PERIOD_KEY}"]'
            ),
        },
        expr='dcf_schedule["cumulative_fractional_years", col.prev] + income_statement["is_fractional_years", @col]',
        format="number",
        decimals=2,
    )
    table.add_row(
        "ufcf_ebitda",
        cells={"label": "EBITDA", "pf_close": None},
        expr='income_statement["is_ebitda", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_ebita",
        cells={"label": "EBITA", "pf_close": None},
        expr='income_statement["is_ebita", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_taxes",
        cells={"label": "( – ) Taxes on EBITA", "pf_close": None},
        expr='-dcf_schedule["ufcf_ebita", @col] * nol_amt_schedule["blended_tax_rate", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_unlevered_net_income",
        cells={"label": "Unlevered net income (EBIAT)", "pf_close": None},
        expr='dcf_schedule["ufcf_ebita", @col] + dcf_schedule["ufcf_taxes", @col]',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_depreciation",
        cells={"label": "( + ) Depreciation", "pf_close": None},
        expr='income_statement["is_depreciation", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_capex",
        cells={"label": "( – ) Capital expenditures", "pf_close": None},
        expr='cash_flow_statement["cf_capex", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_change_in_wc",
        cells={"label": "( – ) Increase / ( + ) decrease in working capital", "pf_close": None},
        expr='cash_flow_statement["cf_change_in_wc", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ufcf_change_in_deferred_taxes",
        cells={"label": "( + ) Increase / ( – ) decrease in deferred taxes", "pf_close": None},
        expr='cash_flow_statement["cf_change_in_net_dtl", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "unlevered_free_cash_flow",
        cells={"label": "Unlevered free cash flow (UFCF)", "pf_close": f8.Cell(expr="0")},
        expr='SUM(dcf_schedule["ufcf_unlevered_net_income".."ufcf_change_in_deferred_taxes", @col])',
        style="total",
        format="currency",
        decimals=3,
    )

    # 2. 5-Year DCF Valuation – EBITDA Multiple Method (4 rows)
    table.add_row_gutter()
    table.add_section_header("5-Year DCF Valuation – EBITDA Multiple Method")
    _add_empty_dcf_schedule_row(
        table,
        "terminal_cf_ebitda_multiple",
        "Terminal cash flow (EBITDA multiple method)",
    )
    table.set_cell(
        "terminal_cf_ebitda_multiple",
        EXIT_PERIOD_KEY,
        expr=f'dcf_schedule["ufcf_ebitda", "{EXIT_PERIOD_KEY}"] * dcf_sensitivity["sens_mult_terminal_multiples", "sens_col_2"]',
    )

    _add_empty_dcf_schedule_row(
        table,
        "total_cf_ebitda_multiple",
        "Total cash flows (EBITDA multiple method)",
        style="subtotal",
    )
    table.set_cells(
        "total_cf_ebitda_multiple",
        slice("pf_close", DCF_PROJECTION_KEYS[-2]),
        expr='dcf_schedule["unlevered_free_cash_flow", @col]',
    )
    table.set_cell(
        "total_cf_ebitda_multiple",
        EXIT_PERIOD_KEY,
        expr=f'dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"] + dcf_schedule["terminal_cf_ebitda_multiple", "{EXIT_PERIOD_KEY}"]',
    )

    _add_empty_dcf_schedule_row(
        table,
        "dcf_xnpv_ebitda_multiple",
        "DCF enterprise value via XNPV (EBITDA multiple method)",
        style="total",
    )
    table.set_cell(
        "dcf_xnpv_ebitda_multiple",
        "pf_close",
        expr=f'XNPV(wacc_schedule["active_wacc", "wacc_rate"], dcf_schedule["total_cf_ebitda_multiple", "pf_close".."{EXIT_PERIOD_KEY}"], returns_waterfall["returns_dates", "initial_investment".."{EXIT_PERIOD_KEY}"]) - dcf_schedule["total_cf_ebitda_multiple", "pf_close"]',
    )

    _add_empty_dcf_schedule_row(
        table,
        "dcf_xnpv_ebitda_multiple_check",
        "DCF XNPV vs. discounting check (EBITDA multiple method)",
        fmt="number",
        dec=0,
    )
    table.set_cell(
        "dcf_xnpv_ebitda_multiple_check",
        "pf_close",
        expr='ROUND(dcf_schedule["dcf_xnpv_ebitda_multiple", "pf_close"] - dcf_sensitivity["sens_mult_ev_wacc_12", "sens_col_2"], 0)',
    )

    # 3. 5-Year DCF Valuation – Perpetuity Growth Method (4 rows)
    table.add_row_gutter()
    table.add_section_header("5-Year DCF Valuation – Perpetuity Growth Method")
    _add_empty_dcf_schedule_row(
        table,
        "terminal_cf_perpetuity_growth",
        "Terminal cash flow (Perpetuity growth method)",
    )
    table.set_cell(
        "terminal_cf_perpetuity_growth",
        EXIT_PERIOD_KEY,
        expr=f'IFERROR(dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"] * (1 + dcf_sensitivity["sens_perp_terminal_growth_rates", "sens_col_2"]) / (wacc_schedule["active_wacc", "wacc_rate"] - dcf_sensitivity["sens_perp_terminal_growth_rates", "sens_col_2"]), 0)',
    )

    _add_empty_dcf_schedule_row(
        table,
        "total_cf_perpetuity_growth",
        "Total cash flows (Perpetuity growth method)",
        style="subtotal",
    )
    table.set_cells(
        "total_cf_perpetuity_growth",
        slice("pf_close", DCF_PROJECTION_KEYS[-2]),
        expr='dcf_schedule["unlevered_free_cash_flow", @col]',
    )
    table.set_cell(
        "total_cf_perpetuity_growth",
        EXIT_PERIOD_KEY,
        expr=f'dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"] + dcf_schedule["terminal_cf_perpetuity_growth", "{EXIT_PERIOD_KEY}"]',
    )

    _add_empty_dcf_schedule_row(
        table,
        "dcf_xnpv_perpetuity_growth",
        "DCF enterprise value via XNPV (Perpetuity growth method)",
        style="total",
    )
    table.set_cell(
        "dcf_xnpv_perpetuity_growth",
        "pf_close",
        expr=f'XNPV(wacc_schedule["active_wacc", "wacc_rate"], dcf_schedule["total_cf_perpetuity_growth", "pf_close".."{EXIT_PERIOD_KEY}"], returns_waterfall["returns_dates", "initial_investment".."{EXIT_PERIOD_KEY}"]) - dcf_schedule["total_cf_perpetuity_growth", "pf_close"]',
    )

    _add_empty_dcf_schedule_row(
        table,
        "dcf_xnpv_perpetuity_growth_check",
        "DCF XNPV vs. discounting check (Perpetuity growth method)",
        fmt="number",
        dec=0,
    )
    table.set_cell(
        "dcf_xnpv_perpetuity_growth_check",
        "pf_close",
        expr='ROUND(dcf_schedule["dcf_xnpv_perpetuity_growth", "pf_close"] - dcf_sensitivity["sens_perp_ev_wacc_12", "sens_col_2"], 0)',
    )

    return table


def build_dcf_sensitivity(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 27-row x 4-column `dcf_sensitivity` 8x3x3 DCF Sensitivity Matrices table."""
    deal = assumptions.deal
    sub = "Units: $ in millions / $ per share"
    table = sheet.add_table(
        "dcf_sensitivity",
        "DCF Valuation Sensitivity Matrices (EBITDA Multiple & Perpetuity Growth Methods)",
        subtitle=sub,
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Sensitivity Parameter / Valuation Metric")
    table.add_column(
        "discount_rate",
        group="Discount Rate",
        headers=["Active WACC", "Tier"],
    )
    table.add_column(
        "sens_col_1",
        group="Terminal Multiple / Perpetuity Growth Case",
        headers=["Low Case", "4.5x / 0.0%"],
    )
    table.add_column(
        "sens_col_2",
        group="Terminal Multiple / Perpetuity Growth Case",
        headers=["Base Case", "5.0x / 0.5%"],
    )
    table.add_column(
        "sens_col_3",
        group="Terminal Multiple / Perpetuity Growth Case",
        headers=["High Case", "5.5x / 1.0%"],
    )

    # 1. Sensitivity Parameter Vectors (3 rows)
    table.add_section_header("Sensitivity Parameter Vectors")
    table.add_row(
        "wacc_step",
        cells={
            "label": "Sensitivity WACC step size",
            "discount_rate": f8.Cell(value=deal.dcf_wacc_step, style="data"),
            "sens_col_1": None,
            "sens_col_2": None,
            "sens_col_3": None,
        },
        style="data",
        format="percentage",
        decimals=2,
    )

    mult_cells: dict[str, f8.CellInputValue] = {
        "label": "EBITDA Multiple Method – Terminal EBITDA multiples",
        "discount_rate": None,
    }
    for col_id, mult_val in zip(SENS_VALUE_COLS, deal.dcf_terminal_ebitda_multiples, strict=True):
        mult_cells[col_id] = f8.Cell(value=mult_val, style="data")
    table.add_row(
        "sens_mult_terminal_multiples",
        cells=mult_cells,
        style="data",
        format="multiple",
        decimals=1,
    )

    perp_cells: dict[str, f8.CellInputValue] = {
        "label": "Perpetuity Growth Method – Terminal growth rates",
        "discount_rate": None,
    }
    for col_id, gr_val in zip(SENS_VALUE_COLS, deal.dcf_terminal_growth_rates, strict=True):
        perp_cells[col_id] = f8.Cell(value=gr_val, style="data")
    table.add_row(
        "sens_perp_terminal_growth_rates",
        cells=perp_cells,
        style="data",
        format="percentage",
        decimals=2,
    )

    # 2. Eight 3x3 Sensitivity Matrices (24 rows across 8 sections)
    pv_ufcf_expr = " + ".join(
        f'dcf_schedule["unlevered_free_cash_flow", "{col}"] / ((1 + dcf_sensitivity[@row, "discount_rate"]) ^ dcf_schedule["cumulative_fractional_years", "{col}"])'
        for col in DCF_PROJECTION_KEYS
    )
    pre_deal_net_debt_expr = (
        'IF(pre_deal_capm_schedule["wacc_conv_conversion_price", "metric_value"] > valuation_and_fdso["offer_price_per_share", "value"], '
        'balance_sheet["bs_existing_lt_debt", "mrq"], 0) + '
        'balance_sheet["bs_noncontrolling_interest", "standalone_close"] - '
        'balance_sheet["bs_cash", "standalone_close"]'
    )

    def _discount_rate_expr(r_id: str) -> str:
        if r_id == "sens_mult_ev_wacc_12":
            return 'wacc_schedule["active_wacc", "wacc_rate"]'
        if r_id == "sens_mult_ev_wacc_11":
            return 'dcf_sensitivity["sens_mult_ev_wacc_12", "discount_rate"] - dcf_sensitivity["wacc_step", "discount_rate"]'
        if r_id == "sens_mult_ev_wacc_13":
            return 'dcf_sensitivity["sens_mult_ev_wacc_12", "discount_rate"] + dcf_sensitivity["wacc_step", "discount_rate"]'
        return 'dcf_sensitivity[row.prev(3), "discount_rate"]'

    wacc_tier_labels: tuple[str, str, str] = (
        "WACC - 1.0% (11.0%)",
        "Base WACC (12.0%)",
        "WACC + 1.0% (13.0%)",
    )
    mult_ev_expr = (
        pv_ufcf_expr
        + f' + (dcf_sensitivity["sens_mult_terminal_multiples", @col] * dcf_schedule["ufcf_ebitda", "{EXIT_PERIOD_KEY}"]) / ((1 + dcf_sensitivity[@row, "discount_rate"]) ^ dcf_schedule["cumulative_fractional_years", "{EXIT_PERIOD_KEY}"])'
    )
    eq_from_ev_expr = "dcf_sensitivity[row.prev(3), @col] - (" + pre_deal_net_debt_expr + ")"
    mult_implied_g_expr = f'IFERROR((dcf_sensitivity["sens_mult_terminal_multiples", @col] * dcf_schedule["ufcf_ebitda", "{EXIT_PERIOD_KEY}"] * dcf_sensitivity[@row, "discount_rate"] - dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"]) / (dcf_sensitivity["sens_mult_terminal_multiples", @col] * dcf_schedule["ufcf_ebitda", "{EXIT_PERIOD_KEY}"] + dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"]), 0)'
    vps_from_eq_expr = 'IFERROR(dcf_sensitivity[row.prev(6), @col] / valuation_and_fdso["fdso_liquidation", "value"], 0)'
    perp_ev_expr = (
        pv_ufcf_expr
        + f' + IFERROR((dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"] * (1 + dcf_sensitivity["sens_perp_terminal_growth_rates", @col]) / (dcf_sensitivity[@row, "discount_rate"] - dcf_sensitivity["sens_perp_terminal_growth_rates", @col])) / ((1 + dcf_sensitivity[@row, "discount_rate"]) ^ dcf_schedule["cumulative_fractional_years", "{EXIT_PERIOD_KEY}"]), 0)'
    )
    perp_implied_mult_expr = f'IFERROR((dcf_schedule["unlevered_free_cash_flow", "{EXIT_PERIOD_KEY}"] * (1 + dcf_sensitivity["sens_perp_terminal_growth_rates", @col]) / (dcf_sensitivity[@row, "discount_rate"] - dcf_sensitivity["sens_perp_terminal_growth_rates", @col])) / dcf_schedule["ufcf_ebitda", "{EXIT_PERIOD_KEY}"], 0)'

    sens_block_specs: tuple[SensitivityMatrixSpec, ...] = (
        SensitivityMatrixSpec(
            ("sens_mult_ev_wacc_11", "sens_mult_ev_wacc_12", "sens_mult_ev_wacc_13"),
            "EBITDA Multiple Sensitivity – Enterprise Value ($M)",
            mult_ev_expr,
            "currency",
            3,
        ),
        SensitivityMatrixSpec(
            ("sens_mult_eq_wacc_11", "sens_mult_eq_wacc_12", "sens_mult_eq_wacc_13"),
            "EBITDA Multiple Sensitivity – Implied Equity Value ($M)",
            eq_from_ev_expr,
            "currency",
            3,
        ),
        SensitivityMatrixSpec(
            (
                "sens_mult_implied_g_wacc_11",
                "sens_mult_implied_g_wacc_12",
                "sens_mult_implied_g_wacc_13",
            ),
            "EBITDA Multiple Sensitivity – Implied Perpetuity Growth Rate",
            mult_implied_g_expr,
            "percentage",
            2,
        ),
        SensitivityMatrixSpec(
            ("sens_mult_vps_wacc_11", "sens_mult_vps_wacc_12", "sens_mult_vps_wacc_13"),
            "EBITDA Multiple Sensitivity – Implied Value per Share ($/sh)",
            vps_from_eq_expr,
            "currency",
            2,
        ),
        SensitivityMatrixSpec(
            ("sens_perp_ev_wacc_11", "sens_perp_ev_wacc_12", "sens_perp_ev_wacc_13"),
            "Perpetuity Growth Sensitivity – Enterprise Value ($M)",
            perp_ev_expr,
            "currency",
            3,
        ),
        SensitivityMatrixSpec(
            ("sens_perp_eq_wacc_11", "sens_perp_eq_wacc_12", "sens_perp_eq_wacc_13"),
            "Perpetuity Growth Sensitivity – Implied Equity Value ($M)",
            eq_from_ev_expr,
            "currency",
            3,
        ),
        SensitivityMatrixSpec(
            (
                "sens_perp_implied_mult_wacc_11",
                "sens_perp_implied_mult_wacc_12",
                "sens_perp_implied_mult_wacc_13",
            ),
            "Perpetuity Growth Sensitivity – Implied Exit EBITDA Multiple",
            perp_implied_mult_expr,
            "multiple",
            1,
        ),
        SensitivityMatrixSpec(
            ("sens_perp_vps_wacc_11", "sens_perp_vps_wacc_12", "sens_perp_vps_wacc_13"),
            "Perpetuity Growth Sensitivity – Implied Value per Share ($/sh)",
            vps_from_eq_expr,
            "currency",
            2,
        ),
    )

    for spec in sens_block_specs:
        table.add_row_gutter()
        table.add_section_header(spec.section_title)
        for r_id, w_lbl in zip(spec.row_ids, wacc_tier_labels, strict=True):
            disc_expr = _discount_rate_expr(r_id)
            table.add_row(
                r_id,
                cells={
                    "label": w_lbl,
                    "discount_rate": f8.Cell(expr=disc_expr, format="percentage", decimals=2),
                },
                expr=spec.cell_expr,
                format=spec.format,
                decimals=spec.decimals,
            )

    return table
