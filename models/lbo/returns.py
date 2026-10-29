"""Exit valuation, three-tier equity dilution, prepayment premium, and contributor returns waterfall builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import f8

from models.lbo.registry import SCHED_SWEEP_TRANCHE_SPECS
from models.lbo.timeline import (
    FINAL_PERIOD_KEY,
    POST_CLOSE_PERIOD_COLS,
    POST_CLOSE_PERIOD_KEYS,
    STUB_PERIOD_KEY,
    add_post_close_columns,
)

if TYPE_CHECKING:
    from models.lbo.assumptions import LboAssumptions

WATERFALL_DEBT_TRANCHES: tuple[str, ...] = ("subordinated_note", "mezzanine")
WATERFALL_PREF_TRANCHES: tuple[str, ...] = ("preferred_a", "preferred_b")
WATERFALL_CONTRIBUTOR_KEYS: tuple[str, ...] = (
    *WATERFALL_DEBT_TRANCHES,
    *WATERFALL_PREF_TRANCHES,
    "sponsor_equity",
    "management_equity",
)

EQUITY_DILUTION_TRANCHE_SPECS: tuple[tuple[str, str, str], ...] = tuple(
    (
        f"alloc_{t.key}",
        f"Equity Allocation - {t.name}",
        f'tranche_fees_oid["{t.key}", "equity_kicker_pct"] * sources_uses["lbo_flag", "active_case"]',
    )
    for t in SCHED_SWEEP_TRANCHE_SPECS
)

PREPAY_RATE_ROW_SPECS: tuple[tuple[str, str, str], ...] = tuple(
    (
        t.key,
        f"prepay_rate_{t.key}",
        f"Prepayment premium rate - {t.name}",
    )
    for t in SCHED_SWEEP_TRANCHE_SPECS
)


@dataclass(frozen=True)
class CashFlowRowSpec:
    """Specification for an intermediate cash flow row in a contributor waterfall."""

    row_id: str
    label: str
    expr: str


@dataclass(frozen=True)
class ContributorWaterfallSpec:
    """Specification for a contributor return waterfall block."""

    initial_row_id: str
    initial_label: str
    initial_expr: str
    periodic_rows: tuple[CashFlowRowSpec, ...]
    total_row_id: str
    total_label: str
    total_expr: str
    irr_row_id: str
    irr_label: str
    coc_row_id: str
    coc_label: str


def build_equity_dilution(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `equity_dilution` three-tier ownership and dilution schedule."""
    _ = assumptions
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "equity_dilution",
        "Equity Dilution & Ownership Allocation",
        subtitle=sub,
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Capital Structure Contributor")
    table.add_column(
        "initial_investment",
        headers=["Initial", "Investment", assumptions.timeline.close_date_iso],
        format="currency",
        decimals=3,
    )
    table.add_column(
        "undiluted",
        group="Ownership Allocation",
        headers=["Undiluted", "Ownership"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "partial_dilution",
        group="Ownership Allocation",
        headers=["Partial", "Dilution", "Ownership"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "full_dilution",
        group="Ownership Allocation",
        headers=["Full", "Dilution", "Ownership"],
        format="percentage",
        decimals=2,
    )

    undil_expr = 'IFERROR(equity_dilution[@row, "initial_investment"] / equity_dilution["alloc_total", "initial_investment"], 0)'
    common_partial_expr = 'equity_dilution[@row, "undiluted"] * (1 - SUM(equity_dilution["alloc_term_loan_a".."alloc_preferred_b", "partial_dilution"]))'
    diluted_full_expr = 'equity_dilution[@row, "partial_dilution"] * (1 - equity_dilution["alloc_mgmt_performance_equity", "full_dilution"])'

    table.add_row(
        "alloc_sponsor_equity",
        cells={
            "label": "Equity Allocation - Sponsor equity",
            "initial_investment": f8.Cell(expr='sources_uses["sponsor_equity", "active_case"]'),
        },
    )
    table.add_row(
        "alloc_management_equity",
        cells={
            "label": "Equity Allocation - Management equity",
            "initial_investment": f8.Cell(expr='sources_uses["management_equity", "active_case"]'),
        },
    )
    for r_id, r_lbl, part_expr in EQUITY_DILUTION_TRANCHE_SPECS:
        table.add_row(
            r_id,
            cells={
                "label": r_lbl,
                "partial_dilution": f8.Cell(expr=part_expr),
            },
        )
    table.add_row(
        "alloc_mgmt_performance_equity",
        cells={
            "label": "Equity Allocation - Management performance equity",
            "partial_dilution": f8.Cell(expr="0"),
            "full_dilution": f8.Cell(
                expr='ppa_schedule["mgmt_performance_equity_pct", "active_case"] * sources_uses["lbo_flag", "active_case"]'
            ),
        },
    )
    table.set_cells(
        slice("alloc_term_loan_a", "alloc_mgmt_performance_equity"),
        "initial_investment",
        expr="0",
    )
    table.set_cells(
        slice("alloc_sponsor_equity", "alloc_mgmt_performance_equity"),
        "undiluted",
        expr=undil_expr,
    )
    table.set_cells(
        ("alloc_sponsor_equity", "alloc_management_equity"),
        "partial_dilution",
        expr=common_partial_expr,
    )
    table.set_cells(
        slice("alloc_sponsor_equity", "alloc_preferred_b"),
        "full_dilution",
        expr=diluted_full_expr,
    )

    table.add_row(
        "alloc_total",
        cells={"label": "Equity Allocation - Total"},
        expr='SUM(equity_dilution["alloc_sponsor_equity".."alloc_mgmt_performance_equity", @col])',
        style="total",
    )
    return table


def build_exit_valuation(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `exit_valuation` multi-method exit equity valuation and prepayment rate schedule."""
    deal = assumptions.deal
    fin = assumptions.financing
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "exit_valuation",
        "Exit Valuation & Prepayment Premium Schedule",
        subtitle=sub,
        currency="USD",
    )
    add_post_close_columns(table, "Exit Valuation / Prepayment Line Item")

    val_rows: tuple[
        tuple[
            str,
            str,
            str | None,
            float | None,
            f8.SemanticStyle | None,
            f8.FormatPreset,
            int,
        ],
        ...,
    ] = (
        (
            "ebitda_annualized",
            "EBITDA – annualized",
            'income_statement["is_ebitda", @col] / income_statement["is_fractional_years", @col]',
            None,
            None,
            "currency",
            3,
        ),
        (
            "forward_ebitda_multiple",
            "( x ) Forward EBITDA multiple",
            None,
            deal.exit_ebitda_multiple,
            "data",
            "multiple",
            1,
        ),
        (
            "enterprise_value_ebitda",
            "Enterprise value (EBITDA multiple method)",
            'exit_valuation["ebitda_annualized", @col] * exit_valuation["forward_ebitda_multiple", @col]',
            None,
            "subtotal",
            "currency",
            3,
        ),
        (
            "less_net_debt",
            "( – ) Net debt",
            '-credit_stats["credit_net_debt", @col]',
            None,
            None,
            "currency",
            3,
        ),
        (
            "total_equity_value_ebitda",
            "Total equity value (EBITDA multiple method)",
            'exit_valuation["enterprise_value_ebitda", @col] + exit_valuation["less_net_debt", @col]',
            None,
            "subtotal",
            "currency",
            3,
        ),
        (
            "gaap_ni_annualized",
            "GAAP net income – annualized",
            'income_statement["is_gaap_net_income_common", @col] / income_statement["is_fractional_years", @col]',
            None,
            None,
            "currency",
            3,
        ),
        (
            "forward_gaap_pe_multiple",
            "( x ) Forward GAAP P/E multiple",
            None,
            deal.exit_pe_multiple,
            "data",
            "multiple",
            1,
        ),
        (
            "total_equity_value_gaap_pe",
            "Total equity value (GAAP P/E method)",
            'exit_valuation["gaap_ni_annualized", @col] * exit_valuation["forward_gaap_pe_multiple", @col]',
            None,
            "subtotal",
            "currency",
            3,
        ),
        (
            "cash_ni_annualized",
            "Cash net income – annualized",
            'income_statement["is_cash_net_income_common", @col] / income_statement["is_fractional_years", @col]',
            None,
            None,
            "currency",
            3,
        ),
        (
            "forward_cash_pe_multiple",
            "( x ) Forward Cash P/E multiple",
            None,
            deal.exit_pe_multiple,
            "data",
            "multiple",
            1,
        ),
        (
            "total_equity_value_cash_pe",
            "Total equity value (Cash P/E method)",
            'exit_valuation["cash_ni_annualized", @col] * exit_valuation["forward_cash_pe_multiple", @col]',
            None,
            "subtotal",
            "currency",
            3,
        ),
        (
            "active_exit_equity_value",
            "Equity value used in calculating exit participations",
            'CHOOSE(ppa_schedule["exit_valuation_method", "active_case"], exit_valuation["total_equity_value_ebitda", @col], exit_valuation["total_equity_value_gaap_pe", @col], exit_valuation["total_equity_value_cash_pe", @col])',
            None,
            "total",
            "currency",
            3,
        ),
    )
    for r_id, r_lbl, r_expr, r_val, r_style, r_fmt, r_dec in val_rows:
        row_cells: dict[str, f8.CellInputValue] = {"label": r_lbl, "pf_close": None}
        if r_val is not None:
            for col_id in POST_CLOSE_PERIOD_KEYS:
                row_cells[col_id] = r_val
        table.add_row(
            r_id,
            cells=row_cells,
            expr=r_expr,
            style=r_style,
            format=r_fmt,
            decimals=r_dec,
        )

    for tk, row_id, row_lbl in PREPAY_RATE_ROW_SPECS:
        p_cells: dict[str, f8.CellInputValue] = {
            "label": row_lbl,
            "pf_close": None,
        }
        for col_id, p_val in zip(
            POST_CLOSE_PERIOD_KEYS,
            fin.get_tranche(tk).prepayment_premium_schedule,
            strict=True,
        ):
            p_cells[col_id] = p_val
        table.add_row(
            row_id,
            cells=p_cells,
            style="data",
            format="percentage",
            decimals=2,
        )
    return table


def _add_contributor_return_rows(
    table: f8.Table,
    spec: ContributorWaterfallSpec,
) -> None:
    init_cells: dict[str, f8.CellInputValue] = {
        "label": spec.initial_label,
        "initial_investment": f8.Cell(expr=spec.initial_expr, format="currency", decimals=3),
    }
    for col_id in (*POST_CLOSE_PERIOD_KEYS, "metric_value"):
        init_cells[col_id] = None
    table.add_row(spec.initial_row_id, cells=init_cells, format="currency", decimals=3)

    for prow in spec.periodic_rows:
        table.add_row(
            prow.row_id,
            cells={
                "label": prow.label,
                "initial_investment": None,
                "metric_value": None,
            },
            expr=prow.expr,
            format="currency",
            decimals=3,
        )

    table.add_row(
        spec.total_row_id,
        cells={"label": spec.total_label, "metric_value": None},
        expr=spec.total_expr,
        style="subtotal",
        format="currency",
        decimals=3,
    )

    cf_cols = ("initial_investment", *POST_CLOSE_PERIOD_KEYS)
    irr_cells: dict[str, f8.CellInputValue] = {"label": spec.irr_label}
    coc_cells: dict[str, f8.CellInputValue] = {"label": spec.coc_label}
    for col_id in cf_cols:
        irr_cells[col_id] = None
        coc_cells[col_id] = None

    table.add_row(spec.irr_row_id, cells=irr_cells, style="total", format="percentage", decimals=2)
    table.add_row(spec.coc_row_id, cells=coc_cells, style="total", format="multiple", decimals=2)


def build_returns_waterfall(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `returns_waterfall` date-scheduled contributor cash flow waterfalls, XIRR, and MoIC table."""
    deal = assumptions.deal
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "returns_waterfall",
        "Contributor Cash Flow Waterfalls & Returns Summary",
        subtitle=sub,
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Contributor Cash Flow / Return Line Item")
    table.add_column(
        "initial_investment",
        headers=["Initial", "Investment", assumptions.timeline.close_date_iso],
    )
    for col_id, (col_group, col_headers) in POST_CLOSE_PERIOD_COLS.items():
        table.add_column(col_id, group=col_group, headers=col_headers)
    table.add_column("metric_value", headers=["Return", "Metric Value"])

    table.add_row(
        "returns_dates",
        cells={"label": "Cash flow schedule date", "metric_value": None},
        expr='DATE(operating_schedule["returns_date_year", @col], operating_schedule["returns_date_month", @col], operating_schedule["returns_date_day", @col])',
        format="date",
    )
    table.set_cell(
        "returns_dates",
        "initial_investment",
        expr='DATE(operating_schedule["returns_date_year", "pf_close"], operating_schedule["returns_date_month", "pf_close"], operating_schedule["returns_date_day", "pf_close"])',
        format="date",
    )

    table.add_row(
        "returns_exit_flag",
        cells={
            "label": "Active exit period flag",
            "initial_investment": None,
            "metric_value": float(deal.exit_year),
        },
        expr='IF(debt_sweep_schedule["debt_period_number", @col] = returns_waterfall["returns_exit_flag", "metric_value"], 1, 0)',
        format="integer",
    )
    table.add_row(
        "returns_active_period_flag",
        cells={
            "label": "Active holding period cash flow flag",
            "initial_investment": None,
            "metric_value": None,
        },
        expr='IF(AND(debt_sweep_schedule["debt_period_number", @col] > 1, debt_sweep_schedule["debt_period_number", @col] <= returns_waterfall["returns_exit_flag", "metric_value"]), 1, 0)',
        format="integer",
    )

    contributor_blocks: tuple[ContributorWaterfallSpec, ...] = (
        ContributorWaterfallSpec(
            initial_row_id="subordinated_note_initial_investment",
            initial_label="Subordinated note - Initial investment",
            initial_expr='-sources_uses["subordinated_note", "active_case"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "subordinated_note_cash_interest",
                    "Subordinated note - Cash interest payments",
                    '(debt_sweep_schedule["debt_subordinated_note_cash_interest", @col] - debt_sweep_schedule["debt_subordinated_note_face_pik", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "subordinated_note_periodic_amortization",
                    "Subordinated note - Periodic amortization",
                    '-(debt_sweep_schedule["debt_subordinated_note_face_mandatory", @col] + debt_sweep_schedule["debt_subordinated_note_face_optional", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "subordinated_note_principal_repayment",
                    "Subordinated note - Principal repayment",
                    'debt_sweep_schedule["debt_subordinated_note_face_end", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "subordinated_note_prepayment_premium",
                    "Subordinated note - Prepayment premium",
                    'returns_waterfall[row.prev, @col] * exit_valuation["prepay_rate_subordinated_note", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "subordinated_note_equity_participation",
                    "Subordinated note - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * equity_dilution["alloc_subordinated_note", "full_dilution"] * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="subordinated_note_total_cash_flows",
            total_label="Subordinated note - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(6)..row.prev, @col])",
            irr_row_id="subordinated_note_irr",
            irr_label="Subordinated note - IRR",
            coc_row_id="subordinated_note_cash_on_cash",
            coc_label="Subordinated note - Cash-on-cash",
        ),
        ContributorWaterfallSpec(
            initial_row_id="mezzanine_initial_investment",
            initial_label="Mezzanine - Initial investment",
            initial_expr='-sources_uses["mezzanine", "active_case"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "mezzanine_cash_interest",
                    "Mezzanine - Cash interest payments",
                    '(debt_sweep_schedule["debt_mezzanine_cash_interest", @col] - debt_sweep_schedule["debt_mezzanine_face_pik", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "mezzanine_periodic_amortization",
                    "Mezzanine - Periodic amortization",
                    '-(debt_sweep_schedule["debt_mezzanine_face_mandatory", @col] + debt_sweep_schedule["debt_mezzanine_face_optional", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "mezzanine_principal_repayment",
                    "Mezzanine - Principal repayment",
                    'debt_sweep_schedule["debt_mezzanine_face_end", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "mezzanine_prepayment_premium",
                    "Mezzanine - Prepayment premium",
                    'returns_waterfall[row.prev, @col] * exit_valuation["prepay_rate_mezzanine", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "mezzanine_equity_participation",
                    "Mezzanine - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * equity_dilution["alloc_mezzanine", "full_dilution"] * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="mezzanine_total_cash_flows",
            total_label="Mezzanine - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(6)..row.prev, @col])",
            irr_row_id="mezzanine_irr",
            irr_label="Mezzanine - IRR",
            coc_row_id="mezzanine_cash_on_cash",
            coc_label="Mezzanine - Cash-on-cash",
        ),
        ContributorWaterfallSpec(
            initial_row_id="preferred_a_initial_investment",
            initial_label="Preferred stock - A - Initial investment",
            initial_expr='-sources_uses["preferred_a", "active_case"] + debt_sweep_schedule["debt_preferred_a_oid_end", "pf_close"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "preferred_a_cash_dividends",
                    "Preferred stock - A - Cash dividends",
                    '(debt_sweep_schedule["debt_preferred_a_cash_interest", @col] - debt_sweep_schedule["debt_preferred_a_face_pik", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_a_principal_repayment",
                    "Preferred stock - A - Principal repayment",
                    'debt_sweep_schedule["debt_preferred_a_face_end", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_a_prepayment_premium",
                    "Preferred stock - A - Prepayment premium",
                    'returns_waterfall[row.prev, @col] * exit_valuation["prepay_rate_preferred_a", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_a_equity_participation",
                    "Preferred stock - A - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * equity_dilution["alloc_preferred_a", "full_dilution"] * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="preferred_a_total_cash_flows",
            total_label="Preferred stock - A - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(5)..row.prev, @col])",
            irr_row_id="preferred_a_irr",
            irr_label="Preferred stock - A - IRR",
            coc_row_id="preferred_a_cash_on_cash",
            coc_label="Preferred stock - A - Cash-on-cash",
        ),
        ContributorWaterfallSpec(
            initial_row_id="preferred_b_initial_investment",
            initial_label="Preferred stock - B - Initial investment",
            initial_expr='-sources_uses["preferred_b", "active_case"] + debt_sweep_schedule["debt_preferred_b_oid_end", "pf_close"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "preferred_b_cash_dividends",
                    "Preferred stock - B - Cash dividends",
                    '(debt_sweep_schedule["debt_preferred_b_cash_interest", @col] - debt_sweep_schedule["debt_preferred_b_face_pik", @col]) * returns_waterfall["returns_active_period_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_b_principal_repayment",
                    "Preferred stock - B - Principal repayment",
                    'debt_sweep_schedule["debt_preferred_b_face_end", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_b_prepayment_premium",
                    "Preferred stock - B - Prepayment premium",
                    'returns_waterfall[row.prev, @col] * exit_valuation["prepay_rate_preferred_b", @col] * returns_waterfall["returns_exit_flag", @col]',
                ),
                CashFlowRowSpec(
                    "preferred_b_equity_participation",
                    "Preferred stock - B - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * equity_dilution["alloc_preferred_b", "full_dilution"] * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="preferred_b_total_cash_flows",
            total_label="Preferred stock - B - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(5)..row.prev, @col])",
            irr_row_id="preferred_b_irr",
            irr_label="Preferred stock - B - IRR",
            coc_row_id="preferred_b_cash_on_cash",
            coc_label="Preferred stock - B - Cash-on-cash",
        ),
        ContributorWaterfallSpec(
            initial_row_id="sponsor_equity_initial_investment",
            initial_label="Sponsor equity - Initial investment",
            initial_expr='-sources_uses["sponsor_equity", "active_case"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "sponsor_equity_equity_participation",
                    "Sponsor equity - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * equity_dilution["alloc_sponsor_equity", "full_dilution"] * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="sponsor_equity_total_cash_flows",
            total_label="Sponsor equity - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(2)..row.prev, @col])",
            irr_row_id="sponsor_equity_irr",
            irr_label="Sponsor equity - IRR",
            coc_row_id="sponsor_equity_cash_on_cash",
            coc_label="Sponsor equity - Cash-on-cash",
        ),
        ContributorWaterfallSpec(
            initial_row_id="management_equity_initial_investment",
            initial_label="Management equity - Initial investment",
            initial_expr='-sources_uses["management_equity", "active_case"]',
            periodic_rows=(
                CashFlowRowSpec(
                    "management_equity_equity_participation",
                    "Management equity - Equity participation at exit",
                    'exit_valuation["active_exit_equity_value", @col] * (equity_dilution["alloc_management_equity", "full_dilution"] + equity_dilution["alloc_mgmt_performance_equity", "full_dilution"]) * returns_waterfall["returns_exit_flag", @col]',
                ),
            ),
            total_row_id="management_equity_total_cash_flows",
            total_label="Management equity - Total cash flows",
            total_expr="SUM(returns_waterfall[row.prev(2)..row.prev, @col])",
            irr_row_id="management_equity_irr",
            irr_label="Management equity - IRR",
            coc_row_id="management_equity_cash_on_cash",
            coc_label="Management equity - Cash-on-cash",
        ),
    )

    for spec in contributor_blocks:
        _add_contributor_return_rows(table, spec)
    irr_rows = tuple(spec.irr_row_id for spec in contributor_blocks)
    coc_rows = tuple(spec.coc_row_id for spec in contributor_blocks)
    table.set_cells(
        irr_rows,
        "metric_value",
        expr=f'IFERROR(XIRR(returns_waterfall[row.prev, "initial_investment".."{FINAL_PERIOD_KEY}"], returns_waterfall["returns_dates", "initial_investment".."{FINAL_PERIOD_KEY}"]), 0)',
        style="total",
        format="percentage",
        decimals=2,
    )
    table.set_cells(
        coc_rows,
        "metric_value",
        expr=f'IFERROR(-SUM(returns_waterfall[row.prev(2), "{STUB_PERIOD_KEY}".."{FINAL_PERIOD_KEY}"]) / returns_waterfall[row.prev(2), "initial_investment"], "NA")',
        style="total",
        format="multiple",
        decimals=2,
    )
    return table
