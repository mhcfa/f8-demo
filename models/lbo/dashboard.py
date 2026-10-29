"""Executive Dashboard summary tables: Institutional PE Investment Committee command center."""

from __future__ import annotations

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.timeline import (
    ANNUAL_PROJECTION_KEYS,
    EXIT_PERIOD_KEY,
    FINAL_PERIOD_KEY,
    STUB_PERIOD_KEY,
)

DASHBOARD_SOURCES_ROWS: tuple[tuple[str, str, str], ...] = (
    ("excess_cash", "Excess cash", 'sources_uses["excess_cash", "active_case"]'),
    (
        "option_proceeds",
        "Proceeds from liquidation of options",
        'sources_uses["option_liquidation_proceeds", "active_case"]',
    ),
    ("revolver", "Revolver", 'sources_uses["revolver_draw", "active_case"]'),
    ("term_loan_a", "Term loan - A", 'sources_uses["term_loan_a", "active_case"]'),
    ("term_loan_b", "Term loan - B", 'sources_uses["term_loan_b", "active_case"]'),
    ("senior_note", "Senior note", 'sources_uses["senior_note", "active_case"]'),
    (
        "subordinated_note",
        "Subordinated note",
        'sources_uses["subordinated_note", "active_case"]',
    ),
    ("mezzanine", "Mezzanine", 'sources_uses["mezzanine", "active_case"]'),
    ("seller_note", "Seller note", 'sources_uses["seller_note", "active_case"]'),
    (
        "convertible_bond",
        "Convertible bond",
        'sources_uses["convertible_bond", "active_case"]',
    ),
    ("debt_8", "[Debt 8]", 'sources_uses["debt_8", "active_case"]'),
    ("preferred_a", "Preferred stock - A", 'sources_uses["preferred_a", "active_case"]'),
    ("preferred_b", "Preferred stock - B", 'sources_uses["preferred_b", "active_case"]'),
    ("sponsor_equity", "Sponsor equity", 'sources_uses["sponsor_equity", "active_case"]'),
    (
        "management_equity",
        "Management equity",
        'sources_uses["management_equity", "active_case"]',
    ),
    ("tax_refund", "Tax refund", 'sources_uses["tax_refund", "active_case"]'),
)

DASHBOARD_USES_ROWS: tuple[tuple[str, str, str], ...] = (
    (
        "use_equity_purchase_price",
        "Purchase target equity",
        'sources_uses["equity_purchase_price", "active_case"]',
    ),
    (
        "use_refinance_debt",
        "Refinance existing debt",
        'sources_uses["legacy_debt_refinanced", "active_case"]',
    ),
    (
        "use_fund_cash_balance",
        "Fund cash balance",
        'sources_uses["fund_cash_balance", "active_case"]',
    ),
    ("use_oid", "Original issue discount (OID)", 'sources_uses["oid", "active_case"]'),
    (
        "use_prepayment_penalties",
        "Prepayment penalties",
        'sources_uses["prepayment_penalties", "active_case"]',
    ),
    (
        "use_financing_fees",
        "Financing fees",
        'sources_uses["financing_fees", "active_case"]',
    ),
    (
        "use_transaction_costs",
        "Transaction costs",
        'sources_uses["transaction_costs", "active_case"]',
    ),
)


def build_dashboard_sources_uses(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `dashboard_sources_uses` Summary Sources & Uses of Funds table."""
    del assumptions
    table = sheet.add_table(
        "dashboard_sources_uses",
        "Summary Sources & Uses of Funds",
        subtitle="Units: $ in millions",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Sources & Uses Line Item")
    table.add_column("balance", header="Amount ($M)", format="currency", decimals=3)
    table.add_column("pct_of_total", header="% of Total", format="percentage", decimals=2)
    table.add_column("mult_ltm_ebitda", headers=["x LTM", "EBITDA"], format="multiple", decimals=2)

    table.add_section_header("Sources of Funds")
    for row_id, label, balance_expr in DASHBOARD_SOURCES_ROWS:
        table.add_row(
            row_id,
            cells={"label": label, "balance": f8.Cell(expr=balance_expr)},
        )
    table.set_cells(
        slice("excess_cash", "tax_refund"),
        "pct_of_total",
        expr='IFERROR(dashboard_sources_uses[@row, "balance"] / dashboard_sources_uses["total_sources", "balance"], 0)',
    )
    table.set_cells(
        slice("excess_cash", "tax_refund"),
        "mult_ltm_ebitda",
        expr='IFERROR(dashboard_sources_uses[@row, "balance"] / credit_stats["credit_ebitda_annualized", "pf_close"], 0)',
    )

    table.add_row(
        "total_sources",
        cells={"label": "Total sources"},
        expr='SUM(dashboard_sources_uses["excess_cash".."tax_refund", @col])',
        style="total",
    )

    table.add_row_gutter()
    table.add_section_header("Uses of Funds")
    for row_id, label, balance_expr in DASHBOARD_USES_ROWS:
        table.add_row(
            row_id,
            cells={"label": label, "balance": f8.Cell(expr=balance_expr)},
        )
    table.set_cells(
        slice("use_equity_purchase_price", "use_transaction_costs"),
        "pct_of_total",
        expr='IFERROR(dashboard_sources_uses[@row, "balance"] / dashboard_sources_uses["total_uses", "balance"], 0)',
    )
    table.set_cells(
        slice("use_equity_purchase_price", "use_transaction_costs"),
        "mult_ltm_ebitda",
        expr='IFERROR(dashboard_sources_uses[@row, "balance"] / credit_stats["credit_ebitda_annualized", "pf_close"], 0)',
    )

    table.add_row(
        "total_uses",
        cells={"label": "Total uses"},
        expr='SUM(dashboard_sources_uses["use_equity_purchase_price".."use_transaction_costs", @col])',
        style="total",
    )
    return table


def build_dashboard_entry_valuation(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `dashboard_entry_valuation` Scenario Selectors & Entry Valuation Bridge table."""
    deal = assumptions.deal
    fin = assumptions.financing
    op = assumptions.operating

    table = sheet.add_table(
        "dashboard_entry_valuation",
        "Scenario Selectors & Entry Valuation Bridge",
        subtitle="Units: $ in millions, except per share",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Valuation / Scenario Line Item")
    table.add_column("metric_value", headers=["Value /", "Amount"])

    def add_metric(
        row_id: str,
        label: str,
        expr: str | None = None,
        style: f8.SemanticStyle | None = None,
        fmt: f8.FormatPreset = "currency",
        dec: int | None = 3,
        *,
        value: float | int | None = None,
    ) -> None:
        row_style: f8.SemanticStyle | None = (
            "data" if value is not None and style is None else style
        )
        if value is not None:
            table.add_row(
                row_id,
                cells={"label": label, "metric_value": float(value)},
                style=row_style,
                format=fmt,
                decimals=dec,
            )
        else:
            table.add_row(
                row_id,
                cells={"label": label},
                expr=expr,
                style=style,
                format=fmt,
                decimals=dec,
            )

    table.add_section_header("Scenario Selectors & Operating Switches")
    add_metric(
        "active_financing_case",
        "Active financing scenario",
        'sources_uses["case_number", "active_case"]',
        fmt="integer",
        dec=None,
    )
    add_metric(
        "active_operating_case",
        "Active operating scenario",
        value=deal.active_operating_case,
        fmt="integer",
        dec=None,
    )
    add_metric(
        "annual_cogs_savings",
        "Annual COGS cost savings ($M)",
        value=op.annual_cogs_savings,
    )
    add_metric(
        "annual_sga_savings",
        "Annual SG&A cost savings ($M)",
        value=op.annual_sga_savings,
    )
    add_metric(
        "total_run_rate_cost_savings",
        "Total run-rate annual cost savings ($M)",
        'dashboard_entry_valuation["annual_cogs_savings", "metric_value"] + dashboard_entry_valuation["annual_sga_savings", "metric_value"]',
        style="subtotal",
    )
    add_metric(
        "minimum_cash_balance",
        "Minimum cash balance ($M)",
        value=deal.minimum_cash_balance,
    )
    add_metric(
        "sponsor_management_fee",
        "Annual sponsor management fee ($M)",
        value=op.sponsor_management_fee_annual,
    )
    add_metric(
        "average_interest_flag",
        "Average debt balance interest switch",
        value=fin.average_interest_flag,
        fmt="integer",
        dec=None,
    )

    table.add_row_gutter()
    table.add_section_header("Entry Valuation Bridge")
    add_metric(
        "current_stock_price",
        "Current stock price ($/sh)",
        'valuation_and_fdso["current_share_price", "value"]',
        fmt="currency",
        dec=2,
    )
    add_metric(
        "offer_premium",
        "Offer premium (%)",
        'valuation_and_fdso["offer_premium", "value"]',
        fmt="percentage",
        dec=2,
    )
    add_metric(
        "offer_price_per_share",
        "Offer price per share ($/sh)",
        'valuation_and_fdso["offer_price_per_share", "value"]',
        style="subtotal",
        fmt="currency",
        dec=2,
    )
    add_metric(
        "bso",
        "Basic shares outstanding (M)",
        'valuation_and_fdso["basic_shares_outstanding", "value"]',
        fmt="number",
        dec=3,
    )
    add_metric(
        "itm_options_liquidated",
        "In-the-money options liquidated (M)",
        'option_tranches["options_total", "itm_options"]',
        fmt="number",
        dec=3,
    )
    add_metric(
        "itm_convertible_shares",
        "In-the-money convertible debt shares (M)",
        'IF(valuation_and_fdso["legacy_conversion_price", "value"] < valuation_and_fdso["offer_price_per_share", "value"], valuation_and_fdso["legacy_convertible_shares", "value"], 0)',
        fmt="number",
        dec=3,
    )
    add_metric(
        "fdso",
        "Fully diluted shares outstanding (M)",
        'SUM(dashboard_entry_valuation["bso".."itm_convertible_shares", "metric_value"])',
        style="subtotal",
        fmt="number",
        dec=3,
    )
    add_metric(
        "equity_purchase_price",
        "Equity purchase price ($M)",
        'dashboard_entry_valuation["offer_price_per_share", "metric_value"] * dashboard_entry_valuation["fdso", "metric_value"]',
        style="subtotal",
    )
    add_metric(
        "less_option_proceeds",
        "( – ) Option liquidation proceeds ($M)",
        '-option_tranches["options_total", "liquidation_proceeds"]',
    )
    add_metric(
        "purchase_price",
        "Purchase price (net of option proceeds) ($M)",
        'dashboard_entry_valuation["equity_purchase_price", "metric_value"] + dashboard_entry_valuation["less_option_proceeds", "metric_value"]',
        style="subtotal",
    )
    add_metric(
        "non_convertible_debt",
        "Non-convertible debt ($M)",
        'balance_sheet["bs_short_term_debt", "standalone_close"] + balance_sheet["bs_capital_leases", "standalone_close"]',
    )
    add_metric(
        "convertible_debt",
        "Convertible debt ($M)",
        'IF(valuation_and_fdso["legacy_conversion_price", "value"] > dashboard_entry_valuation["offer_price_per_share", "metric_value"], balance_sheet["bs_existing_lt_debt", "standalone_close"], 0)',
    )
    add_metric(
        "minority_interest",
        "Noncontrolling (minority) interest ($M)",
        'balance_sheet["bs_noncontrolling_interest", "standalone_close"]',
    )
    add_metric(
        "total_debt_and_mi",
        "Total debt & minority interest ($M)",
        'SUM(dashboard_entry_valuation["non_convertible_debt".."minority_interest", "metric_value"])',
        style="subtotal",
    )
    add_metric(
        "less_cash",
        "( – ) Cash & equivalents ($M)",
        '-balance_sheet["bs_cash", "standalone_close"]',
    )
    add_metric(
        "net_debt",
        "Net debt ($M)",
        'dashboard_entry_valuation["total_debt_and_mi", "metric_value"] + dashboard_entry_valuation["less_cash", "metric_value"]',
        style="subtotal",
    )
    add_metric(
        "pf_enterprise_value",
        "Pro forma enterprise value ($M)",
        'dashboard_entry_valuation["equity_purchase_price", "metric_value"] + dashboard_entry_valuation["net_debt", "metric_value"]',
        style="total",
    )
    return table


def build_dashboard_implied_multiples(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `dashboard_implied_multiples` Implied Entry Valuation Multiples table."""
    table = sheet.add_table(
        "dashboard_implied_multiples",
        "Implied Entry Valuation Multiples",
        subtitle="Units: $ in millions, except multiples",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Valuation Metric")
    table.add_column("metric_value", headers=["Amount", "($M)"], format="currency", decimals=3)
    table.add_column(
        "implied_multiple", headers=["Implied", "EV Multiple"], format="multiple", decimals=2
    )

    timeline = assumptions.timeline
    stub_year = timeline.close_year + 1
    annual_year = timeline.close_year + 2
    mult_specs: tuple[tuple[str, str, str], ...] = (
        ("ltm_sales", "LTM Sales", 'SUM(income_statement["is_net_sales", "mrq".."mrq_plus_3"])'),
        (
            "fy12_pf_sales",
            f"FY{stub_year} Stub (3Q) Sales",
            f'income_statement["is_net_sales", "{STUB_PERIOD_KEY}"]',
        ),
        (
            "fy13_pf_sales",
            f"FY{annual_year} Sales",
            f'income_statement["is_net_sales", "{ANNUAL_PROJECTION_KEYS[0]}"]',
        ),
        ("ltm_ebitda", "LTM EBITDA", 'SUM(income_statement["is_ebitda", "mrq".."mrq_plus_3"])'),
        (
            "fy12_pf_ebitda",
            f"FY{stub_year} Stub (3Q) EBITDA",
            f'income_statement["is_ebitda", "{STUB_PERIOD_KEY}"]',
        ),
        (
            "fy13_pf_ebitda",
            f"FY{annual_year} EBITDA",
            f'income_statement["is_ebitda", "{ANNUAL_PROJECTION_KEYS[0]}"]',
        ),
    )
    for row_id, label, val_expr in mult_specs:
        table.add_row(
            row_id,
            cells={
                "label": label,
                "metric_value": f8.Cell(expr=val_expr, format="currency", decimals=3),
            },
        )
    table.set_cells(
        slice("ltm_sales", "fy13_pf_ebitda"),
        "implied_multiple",
        expr='dashboard_entry_valuation["pf_enterprise_value", "metric_value"] / dashboard_implied_multiples[@row, "metric_value"]',
        format="multiple",
        decimals=2,
    )
    return table


def build_dashboard_returns_summary(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `dashboard_returns_summary` Sponsor and Management Return Metrics summary table."""
    del assumptions
    table = sheet.add_table(
        "dashboard_returns_summary",
        "Investment Returns Summary",
        subtitle="Units: $ in millions, except MoIC",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Return Metric")
    table.add_column("metric_value", headers=["Value /", "Amount"])

    table.add_section_header("Exit Valuation")
    table.add_row(
        "exit_enterprise_value",
        cells={"label": "Exit enterprise value ($M)"},
        expr=f'SUMPRODUCT(exit_valuation["enterprise_value_ebitda", "{STUB_PERIOD_KEY}".."{FINAL_PERIOD_KEY}"], returns_waterfall["returns_exit_flag", "{STUB_PERIOD_KEY}".."{FINAL_PERIOD_KEY}"])',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "exit_equity_value",
        cells={"label": "Exit equity value ($M)"},
        expr=f'SUMPRODUCT(exit_valuation["active_exit_equity_value", "{STUB_PERIOD_KEY}".."{FINAL_PERIOD_KEY}"], returns_waterfall["returns_exit_flag", "{STUB_PERIOD_KEY}".."{FINAL_PERIOD_KEY}"])',
        format="currency",
        decimals=3,
    )

    table.add_row_gutter()
    table.add_section_header("Sponsor & Management Returns")
    table.add_row(
        "sponsor_moic",
        cells={"label": "Sponsor MoIC"},
        expr='returns_waterfall["sponsor_equity_cash_on_cash", "metric_value"]',
        style="data",
        format="multiple",
        decimals=2,
    )
    table.add_row(
        "sponsor_irr",
        cells={"label": "Sponsor IRR"},
        expr='returns_waterfall["sponsor_equity_irr", "metric_value"]',
        format="percentage",
        decimals=2,
    )
    table.add_row(
        "management_moic",
        cells={"label": "Management MoIC"},
        expr='returns_waterfall["management_equity_cash_on_cash", "metric_value"]',
        style="data",
        format="multiple",
        decimals=2,
    )
    table.add_row(
        "management_irr",
        cells={"label": "Management IRR"},
        expr='returns_waterfall["management_equity_irr", "metric_value"]',
        style="total",
        format="percentage",
        decimals=2,
    )
    return table


def build_dashboard_credit_profile(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `dashboard_credit_profile` Core Credit & De-leveraging Trajectory schedule."""
    table = sheet.add_table(
        "dashboard_credit_profile",
        "Credit & De-leveraging Profile",
        subtitle="Units: $ in millions, except ratios",
        currency="USD",
    )
    timeline = assumptions.timeline
    y2_year = timeline.close_year + 2
    exit_year = timeline.exit_fiscal_year
    fy_end_md = f"{timeline.fiscal_year_end_month:02d}-{timeline.fiscal_year_end_day:02d}"
    table.add_column("label", role="descriptor", header="Credit Metric / Ratio")
    table.add_column("pf_close", headers=["PF Close", timeline.close_date_iso])
    table.add_column(ANNUAL_PROJECTION_KEYS[0], headers=[f"FY{y2_year}", f"{y2_year}-{fy_end_md}"])
    table.add_column(EXIT_PERIOD_KEY, headers=[f"Exit FY{exit_year}", f"{exit_year}-{fy_end_md}"])

    table.add_section_header("Debt & Leverage Trajectory")
    table.add_row(
        "total_debt",
        cells={"label": "Total debt (incl. preferred)"},
        expr='credit_stats["credit_total_debt", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "net_debt",
        cells={"label": "Net debt"},
        expr='credit_stats["credit_net_debt", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "ebitda",
        cells={"label": "EBITDA (annualized)"},
        expr='credit_stats["credit_ebitda_annualized", @col]',
        format="currency",
        decimals=3,
    )

    table.add_row_gutter()
    table.add_section_header("Credit & Coverage Ratios")
    table.add_row(
        "total_debt_to_ebitda",
        cells={"label": "Total debt / EBITDA"},
        expr='credit_stats["credit_total_debt_to_ebitda", @col]',
        format="multiple",
        decimals=2,
    )
    table.add_row(
        "net_debt_to_ebitda",
        cells={"label": "Net debt / EBITDA"},
        expr='credit_stats["credit_net_debt_to_ebitda", @col]',
        format="multiple",
        decimals=2,
    )
    table.add_row(
        "ebitda_to_cash_interest",
        cells={"label": "EBITDA / cash interest coverage", "pf_close": None},
        expr='credit_stats["credit_ebitda_to_cash_interest", @col]',
        style="total",
        format="multiple",
        decimals=2,
    )
    return table


def build_dashboard_integrity_checks(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `dashboard_integrity_checks` Standalone Audit Card table."""
    del assumptions
    table = sheet.add_table(
        "dashboard_integrity_checks",
        "Model Integrity Checks",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Model Integrity Check")
    table.add_column_gutter()
    table.add_column("metric_value", header="Status", format="integer", decimals=None)

    table.add_row(
        "check_sources_uses_balanced",
        cells={"label": "Sources & uses balanced check"},
        expr='IF(AND(sources_uses["sources_uses_check", "active_case"] <= ppa_schedule["balance_check_tolerance", "active_case"], sources_uses["sources_uses_check", "active_case"] >= -ppa_schedule["balance_check_tolerance", "active_case"]), 1, 0)',
        format="integer",
        decimals=None,
    )
    table.add_row(
        "check_balance_sheet_balanced",
        cells={"label": "Balance sheet balanced check"},
        expr=f'IF(AND(MAX(balance_sheet["bs_balance_check", "mrq".."{FINAL_PERIOD_KEY}"]) <= ppa_schedule["balance_check_tolerance", "active_case"], MIN(balance_sheet["bs_balance_check", "mrq".."{FINAL_PERIOD_KEY}"]) >= -ppa_schedule["balance_check_tolerance", "active_case"]), 1, 0)',
        format="integer",
        decimals=None,
    )
    table.add_row(
        "check_revolver_limit_observed",
        cells={"label": "Revolver commitment limit observed check"},
        expr=f'IF(MAX(balance_sheet["bs_revolver", "pf_close".."{FINAL_PERIOD_KEY}"]) <= sources_uses["revolver_commitment", "active_case"], 1, 0)',
        format="integer",
        decimals=None,
    )
    table.add_row(
        "check_all_passed",
        cells={"label": "All model integrity checks passed"},
        expr='IF(SUM(dashboard_integrity_checks["check_sources_uses_balanced".."check_revolver_limit_observed", "metric_value"]) = 3, 1, 0)',
        style="total",
        format="integer",
        decimals=None,
    )
    return table
