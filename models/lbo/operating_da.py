"""Post-close operating scenario drivers, synergy phase-in, and D&A / PPA write-up schedules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import f8

from models.lbo.registry import NEW_FINANCING_TRANCHE_SPECS
from models.lbo.timeline import (
    ANNUAL_PROJECTION_KEYS,
    FINAL_PERIOD_KEY,
    POST_CLOSE_PERIOD_KEYS,
    STUB_PERIOD_KEY,
    TIMELINE_COL_KEYS,
    add_timeline_columns,
    inactive_pre_pf_cells,
)

if TYPE_CHECKING:
    from models.lbo.assumptions import LboAssumptions


@dataclass(frozen=True)
class OperatingPctDriverSpec:
    """Specification for an operating percentage-of-sales driver block."""

    flat_row_id: str
    flat_label: str
    flat_expr: str
    mgmt_row_id: str
    mgmt_label: str
    mgmt_values: tuple[float, ...]
    analyst_row_id: str
    analyst_label: str
    analyst_expr: str
    downside_row_id: str
    downside_label: str
    downside_values: tuple[float, ...]
    active_row_id: str
    active_label: str


ANALYST_INPUT_ROWS: tuple[tuple[str, str, str, f8.FormatPreset, int], ...] = (
    ("analyst_fractional_years", "fractional_years", "Consensus fractional years", "number", 2),
    ("analyst_revenue", "revenue", "Consensus revenue", "currency", 3),
    ("analyst_cogs", "cogs", "Consensus COGS", "currency", 3),
    ("analyst_sga", "sga", "Consensus SG&A", "currency", 3),
    ("analyst_depreciation", "depreciation", "Consensus depreciation", "currency", 3),
    ("analyst_amortization", "amortization", "Consensus amortization", "currency", 3),
    ("analyst_sbc", "sbc", "Consensus stock-based compensation", "currency", 3),
    ("analyst_capex", "capex", "Consensus capital expenditures", "currency", 3),
)


def _add_post_close_vec_row(
    table: f8.Table,
    row_id: str,
    label: str,
    values: tuple[float, ...],
    fmt: f8.FormatPreset = "percentage",
    dec: int = 2,
) -> None:
    cells = inactive_pre_pf_cells(label, include_pf_close=True)
    for col_id, val in zip(POST_CLOSE_PERIOD_KEYS, values, strict=True):
        cells[col_id] = val
    table.add_row(row_id, cells=cells, style="data", format=fmt, decimals=dec)


ACTIVE_OPERATING_CHOOSE_EXPR = (
    'CHOOSE(dashboard_entry_valuation["active_operating_case", "metric_value"], '
    "operating_schedule[row.prev(4), @col], "
    "operating_schedule[row.prev(3), @col], "
    "operating_schedule[row.prev(2), @col], "
    "operating_schedule[row.prev, @col])"
)

FC_AMORT_STUB_EXPR = (
    f'da_schedule[@row, "pf_close"] * income_statement["is_fractional_years", "{STUB_PERIOD_KEY}"]'
)

FC_AMORT_ANNUAL_EXPR = (
    'MAX(0, MIN(da_schedule[@row, "pf_close"], '
    f'da_schedule[@row, "standalone_close"] - SUM(da_schedule[@row, "{STUB_PERIOD_KEY}"..col.prev])))'
)

CAPEX_COHORT_ROW_IDS: tuple[str, ...] = (
    "da_capex_cohort_1",
    "da_capex_cohort_2",
    "da_capex_cohort_3",
    "da_capex_cohort_4",
    "da_capex_cohort_5",
    "da_capex_cohort_6",
    "da_capex_cohort_7",
    "da_capex_cohort_8",
    "da_capex_cohort_9",
    "da_capex_cohort_10",
)

CAPEX_COHORT_FIRST_COL_EXPR = 'MIN(da_schedule[@row, "pf_close"] * income_statement["is_fractional_years", @col], da_schedule[@row, "standalone_close"])'

CAPEX_COHORT_SUBSEQUENT_EXPR = (
    'MIN(da_schedule[@row, "pf_close"] * income_statement["is_fractional_years", @col], '
    f'da_schedule[@row, "standalone_close"] - SUM(da_schedule[@row, "{STUB_PERIOD_KEY}"..col.prev]))'
)

WRITEUP_SCHEDULE_STUB_EXPR = f'income_statement["is_fractional_years", "{STUB_PERIOD_KEY}"] / da_schedule[row.prev, "pf_close"]'

WRITEUP_SCHEDULE_ANNUAL_EXPR = (
    'MIN(income_statement["is_fractional_years", @col] / da_schedule[row.prev, "pf_close"], '
    f'1 - SUM(da_schedule[@row, "{STUB_PERIOD_KEY}"..col.prev]))'
)


def build_operating_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `operating_schedule` 4-case operating driver selector and synergy schedule."""
    base = assumptions.baseline
    op = assumptions.operating
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "operating_schedule",
        "Post-Close Operating Scenarios & Synergy Schedule",
        subtitle=sub,
        currency="USD",
    )
    add_timeline_columns(table, "Operating Driver / Scenario Line Item")

    prior_q_cells: dict[str, f8.CellInputValue] = dict.fromkeys(TIMELINE_COL_KEYS, None)
    prior_q_cells["label"] = "Prior quarter baseline sales ($M)"
    prior_q_cells["mrq"] = base.pre_close_prior_quarter_sales[0]
    table.add_row(
        "prior_quarter_sales",
        cells=prior_q_cells,
        style="data",
        format="currency",
        decimals=3,
    )
    _add_post_close_vec_row(
        table,
        "standalone_gaap_eps_input",
        "Standalone consensus GAAP EPS ($/sh)",
        base.standalone_post_close_gaap_eps,
        fmt="currency",
        dec=2,
    )
    _add_post_close_vec_row(
        table,
        "standalone_cash_eps_input",
        "Standalone consensus Cash EPS ($/sh)",
        base.standalone_post_close_cash_eps,
        fmt="currency",
        dec=2,
    )

    returns_cols = ("pf_close", *POST_CLOSE_PERIOD_KEYS)
    yr_cells = inactive_pre_pf_cells("Returns schedule calendar year", include_pf_close=False)
    mo_cells = inactive_pre_pf_cells("Returns schedule calendar month", include_pf_close=False)
    dy_cells = inactive_pre_pf_cells("Returns schedule calendar day", include_pf_close=False)
    for col_id, (yr_val, mo_val, dy_val) in zip(
        returns_cols, assumptions.timeline.returns_schedule_dates, strict=True
    ):
        yr_cells[col_id] = float(yr_val)
        mo_cells[col_id] = float(mo_val)
        dy_cells[col_id] = float(dy_val)
    table.add_row("returns_date_year", cells=yr_cells, style="data", format="integer")
    table.add_row("returns_date_month", cells=mo_cells, style="data", format="integer")
    table.add_row("returns_date_day", cells=dy_cells, style="data", format="integer")

    consensus_cols = (STUB_PERIOD_KEY, ANNUAL_PROJECTION_KEYS[0], ANNUAL_PROJECTION_KEYS[1])
    for r_id, _src_r, lbl, fmt, dec in ANALYST_INPUT_ROWS:
        vec: tuple[float, ...] = getattr(base, r_id)
        vec_map: dict[str, float] = dict(zip(("pf_close", *consensus_cols), vec, strict=True))
        cells = inactive_pre_pf_cells(lbl, include_pf_close=False)
        cells["pf_close"] = vec_map["pf_close"]
        for c_id in POST_CLOSE_PERIOD_KEYS:
            cells[c_id] = vec_map.get(c_id)
        table.add_row(r_id, cells=cells, style="data", format=fmt, decimals=dec)

    table.add_row(
        "flat_sales_growth",
        cells=inactive_pre_pf_cells("Flat Case - Annual sales growth"),
        expr='income_statement["is_sales_growth", "mrq"]',
        format="percentage",
        decimals=2,
    )
    _add_post_close_vec_row(
        table,
        "mgmt_sales_growth",
        "Management Case - Annual sales growth",
        op.management_sales_growth,
    )
    table.add_row(
        "analyst_sales_growth",
        cells=inactive_pre_pf_cells("Analyst Case - Annual sales growth"),
        expr='operating_schedule["analyst_sales_growth", col.prev]',
        format="percentage",
        decimals=2,
    )
    growth_expr = '((operating_schedule["analyst_revenue", @col] / operating_schedule["analyst_fractional_years", @col]) / (operating_schedule["analyst_revenue", col.prev] / operating_schedule["analyst_fractional_years", col.prev])) - 1'
    table.set_cells(
        "analyst_sales_growth",
        slice(STUB_PERIOD_KEY, ANNUAL_PROJECTION_KEYS[1]),
        expr=growth_expr,
    )
    _add_post_close_vec_row(
        table,
        "downside_sales_growth",
        "Downside Case - Annual sales growth",
        op.downside_sales_growth,
    )
    table.add_row(
        "active_sales_growth",
        cells=inactive_pre_pf_cells("Active Case - Annual sales growth"),
        expr=ACTIVE_OPERATING_CHOOSE_EXPR,
        style="subtotal",
        format="percentage",
        decimals=2,
    )

    pct_specs: tuple[OperatingPctDriverSpec, ...] = (
        OperatingPctDriverSpec(
            flat_row_id="flat_cogs_pct_sales",
            flat_label="Flat Case - COGS / sales",
            flat_expr='income_statement["is_cogs", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_cogs_pct_sales",
            mgmt_label="Management Case - COGS / sales",
            mgmt_values=op.management_cogs_pct_sales,
            analyst_row_id="analyst_cogs_pct_sales",
            analyst_label="Analyst Case - COGS / sales",
            analyst_expr='operating_schedule["analyst_cogs", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_cogs_pct_sales",
            downside_label="Downside Case - COGS / sales",
            downside_values=op.downside_cogs_pct_sales,
            active_row_id="active_cogs_pct_sales",
            active_label="Active Case - COGS / sales",
        ),
        OperatingPctDriverSpec(
            flat_row_id="flat_sga_pct_sales",
            flat_label="Flat Case - SG&A / sales",
            flat_expr='income_statement["is_sga", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_sga_pct_sales",
            mgmt_label="Management Case - SG&A / sales",
            mgmt_values=op.management_sga_pct_sales,
            analyst_row_id="analyst_sga_pct_sales",
            analyst_label="Analyst Case - SG&A / sales",
            analyst_expr='operating_schedule["analyst_sga", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_sga_pct_sales",
            downside_label="Downside Case - SG&A / sales",
            downside_values=op.downside_sga_pct_sales,
            active_row_id="active_sga_pct_sales",
            active_label="Active Case - SG&A / sales",
        ),
        OperatingPctDriverSpec(
            flat_row_id="flat_depr_pct_sales",
            flat_label="Flat Case - Depreciation / sales",
            flat_expr='income_statement["is_depreciation", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_depr_pct_sales",
            mgmt_label="Management Case - Depreciation / sales",
            mgmt_values=op.management_depr_pct_sales,
            analyst_row_id="analyst_depr_pct_sales",
            analyst_label="Analyst Case - Depreciation / sales",
            analyst_expr='operating_schedule["analyst_depreciation", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_depr_pct_sales",
            downside_label="Downside Case - Depreciation / sales",
            downside_values=op.downside_depr_pct_sales,
            active_row_id="active_depr_pct_sales",
            active_label="Active Case - Depreciation / sales",
        ),
        OperatingPctDriverSpec(
            flat_row_id="flat_amort_pct_sales",
            flat_label="Flat Case - Amortization / sales",
            flat_expr='income_statement["is_amortization", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_amort_pct_sales",
            mgmt_label="Management Case - Amortization / sales",
            mgmt_values=op.management_amort_pct_sales,
            analyst_row_id="analyst_amort_pct_sales",
            analyst_label="Analyst Case - Amortization / sales",
            analyst_expr='operating_schedule["analyst_amortization", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_amort_pct_sales",
            downside_label="Downside Case - Amortization / sales",
            downside_values=op.downside_amort_pct_sales,
            active_row_id="active_amort_pct_sales",
            active_label="Active Case - Amortization / sales",
        ),
        OperatingPctDriverSpec(
            flat_row_id="flat_sbc_pct_sales",
            flat_label="Flat Case - SBC / sales",
            flat_expr='income_statement["is_sbc", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_sbc_pct_sales",
            mgmt_label="Management Case - SBC / sales",
            mgmt_values=op.management_sbc_pct_sales,
            analyst_row_id="analyst_sbc_pct_sales",
            analyst_label="Analyst Case - SBC / sales",
            analyst_expr='operating_schedule["analyst_sbc", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_sbc_pct_sales",
            downside_label="Downside Case - SBC / sales",
            downside_values=op.downside_sbc_pct_sales,
            active_row_id="active_sbc_pct_sales",
            active_label="Active Case - SBC / sales",
        ),
        OperatingPctDriverSpec(
            flat_row_id="flat_capex_pct_sales",
            flat_label="Flat Case - Capex / sales",
            flat_expr='income_statement["is_capex", "mrq"] / income_statement["is_net_sales", "mrq"]',
            mgmt_row_id="mgmt_capex_pct_sales",
            mgmt_label="Management Case - Capex / sales",
            mgmt_values=op.management_capex_pct_sales,
            analyst_row_id="analyst_capex_pct_sales",
            analyst_label="Analyst Case - Capex / sales",
            analyst_expr='operating_schedule["analyst_capex", @col] / operating_schedule["analyst_revenue", @col]',
            downside_row_id="downside_capex_pct_sales",
            downside_label="Downside Case - Capex / sales",
            downside_values=op.downside_capex_pct_sales,
            active_row_id="active_capex_pct_sales",
            active_label="Active Case - Capex / sales",
        ),
    )
    for spec in pct_specs:
        table.add_row(
            spec.flat_row_id,
            cells=inactive_pre_pf_cells(spec.flat_label),
            expr=spec.flat_expr,
            format="percentage",
            decimals=2,
        )
        _add_post_close_vec_row(table, spec.mgmt_row_id, spec.mgmt_label, spec.mgmt_values)
        table.add_row(
            spec.analyst_row_id,
            cells=inactive_pre_pf_cells(spec.analyst_label),
            expr="operating_schedule[@row, col.prev]",
            format="percentage",
            decimals=2,
        )
        table.set_cells(
            spec.analyst_row_id,
            slice(STUB_PERIOD_KEY, ANNUAL_PROJECTION_KEYS[1]),
            expr=spec.analyst_expr,
        )
        _add_post_close_vec_row(
            table, spec.downside_row_id, spec.downside_label, spec.downside_values
        )
        table.add_row(
            spec.active_row_id,
            cells=inactive_pre_pf_cells(spec.active_label),
            expr=ACTIVE_OPERATING_CHOOSE_EXPR,
            style="subtotal",
            format="percentage",
            decimals=2,
        )

    _add_post_close_vec_row(
        table, "cogs_savings_phase_in", "COGS synergy phase-in", op.cogs_savings_phase_in
    )
    _add_post_close_vec_row(
        table, "sga_savings_phase_in", "SG&A synergy phase-in", op.sga_savings_phase_in
    )
    table.add_row(
        "cogs_synergy",
        cells=inactive_pre_pf_cells("Realized COGS synergy ($M)"),
        expr='dashboard_entry_valuation["annual_cogs_savings", "metric_value"] * operating_schedule["cogs_savings_phase_in", @col] * sources_uses["lbo_flag", "active_case"] * income_statement["is_fractional_years", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "sga_synergy",
        cells=inactive_pre_pf_cells("Realized SG&A synergy ($M)"),
        expr='dashboard_entry_valuation["annual_sga_savings", "metric_value"] * operating_schedule["sga_savings_phase_in", @col] * sources_uses["lbo_flag", "active_case"] * income_statement["is_fractional_years", @col]',
        format="currency",
        decimals=3,
    )
    return table


def build_da_schedule(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `da_schedule` Financing Fee, Capex Cohort, and PPA Write-Up D&A schedule."""
    deal = assumptions.deal
    capex_life = assumptions.operating.capex_useful_life_years
    capex_salvage = assumptions.operating.capex_salvage_value
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "da_schedule",
        "Depreciation, Amortization & PPA Step-Up Schedule",
        subtitle=sub,
        currency="USD",
    )
    add_timeline_columns(table, "D&A Schedule Line Item")

    life_cells = inactive_pre_pf_cells("Capex useful life (yrs)", include_pf_close=False)
    life_cells["pf_close"] = capex_life
    for c_id in POST_CLOSE_PERIOD_KEYS:
        life_cells[c_id] = None
    table.add_row("capex_useful_life", cells=life_cells, style="data", format="number", decimals=1)

    salvage_cells = inactive_pre_pf_cells("Capex salvage value ($M)", include_pf_close=False)
    salvage_cells["pf_close"] = capex_salvage
    for c_id in POST_CLOSE_PERIOD_KEYS:
        salvage_cells[c_id] = None
    table.add_row(
        "capex_salvage_value", cells=salvage_cells, style="data", format="currency", decimals=3
    )

    for t in NEW_FINANCING_TRANCHE_SPECS:
        fc_cells = inactive_pre_pf_cells(
            f"Amortization of financing costs - {t.name}", include_pf_close=False
        )
        fc_cells["standalone_close"] = f8.Cell(
            expr=f'tranche_fees_oid["{t.key}", "capitalized_financing_fee"]'
        )
        fc_cells["pf_close"] = f8.Cell(
            expr=f'IFERROR(da_schedule[@row, "standalone_close"] / tranche_fees_oid["{t.key}", "fee_amort_years"], 0)'
        )
        table.add_row(
            f"da_amort_fc_{t.key}",
            cells=fc_cells,
            format="currency",
            decimals=3,
        )
    table.set_cells(
        slice("da_amort_fc_revolver", "da_amort_fc_preferred_b"),
        STUB_PERIOD_KEY,
        expr=FC_AMORT_STUB_EXPR,
    )
    table.set_cells(
        slice("da_amort_fc_revolver", "da_amort_fc_preferred_b"),
        slice(ANNUAL_PROJECTION_KEYS[0], FINAL_PERIOD_KEY),
        expr=FC_AMORT_ANNUAL_EXPR,
    )

    table.add_row(
        "da_amort_financing_costs_total",
        cells=inactive_pre_pf_cells("Total annual amortization of financing costs"),
        expr='SUM(da_schedule["da_amort_fc_revolver".."da_amort_fc_preferred_b", @col])',
        style="subtotal",
        format="currency",
        decimals=3,
    )

    for c_idx, (coh_id, yr, col_key) in enumerate(
        zip(
            CAPEX_COHORT_ROW_IDS,
            assumptions.timeline.capex_cohort_years,
            POST_CLOSE_PERIOD_KEYS,
            strict=True,
        )
    ):
        coh_lbl = f"Capex depreciation cohort - {yr}"
        coh_capex_expr = f'income_statement["is_capex", "{col_key}"]'
        coh_cells = inactive_pre_pf_cells(coh_lbl, include_pf_close=False)
        coh_cells["standalone_close"] = f8.Cell(expr=coh_capex_expr)
        coh_cells[col_key] = f8.Cell(expr=CAPEX_COHORT_FIRST_COL_EXPR)
        table.add_row(
            coh_id,
            cells=coh_cells,
            format="currency",
            decimals=3,
        )
        if c_idx > 0:
            table.set_cells(
                coh_id,
                slice(STUB_PERIOD_KEY, POST_CLOSE_PERIOD_KEYS[c_idx - 1]),
                expr="0",
            )
        if c_idx + 1 < len(POST_CLOSE_PERIOD_KEYS):
            table.set_cells(
                coh_id,
                slice(POST_CLOSE_PERIOD_KEYS[c_idx + 1], FINAL_PERIOD_KEY),
                expr=CAPEX_COHORT_SUBSEQUENT_EXPR,
            )
    table.set_cells(
        slice(CAPEX_COHORT_ROW_IDS[0], CAPEX_COHORT_ROW_IDS[-1]),
        "pf_close",
        expr='(da_schedule[@row, "standalone_close"] - da_schedule["capex_salvage_value", "pf_close"]) / da_schedule["capex_useful_life", "pf_close"]',
    )

    table.add_row(
        "da_depreciation_capex",
        cells=inactive_pre_pf_cells("Depreciation of capex"),
        expr=f'SUM(da_schedule["{CAPEX_COHORT_ROW_IDS[0]}".."{CAPEX_COHORT_ROW_IDS[-1]}", @col])',
        style="subtotal",
        format="currency",
        decimals=3,
    )

    ppe_p_cells = inactive_pre_pf_cells("PP&E depreciation period (yrs)", include_pf_close=False)
    ppe_p_cells["pf_close"] = deal.ppe_writeup_depr_period_years
    for c_id in POST_CLOSE_PERIOD_KEYS:
        ppe_p_cells[c_id] = None
    table.add_row("da_ppe_writeup_period", cells=ppe_p_cells, format="number", decimals=1)

    table.add_row(
        "da_ppe_writeup_schedule",
        cells=inactive_pre_pf_cells("PP&E depreciation / accretion schedule"),
        format="percentage",
        decimals=2,
    )

    table.add_row(
        "da_ppe_writeup_beg",
        cells=inactive_pre_pf_cells("PP&E write-up / (down) – beginning"),
        expr='da_schedule["da_ppe_writeup_end", col.prev]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_ppe_writeup_depr",
        cells=inactive_pre_pf_cells("(Depreciation) / accretion of PP&E write-up"),
        expr='-da_schedule["da_ppe_writeup_end", "pf_close"] * da_schedule["da_ppe_writeup_schedule", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_ppe_writeup_end",
        cells=inactive_pre_pf_cells("PP&E write-up / (down) – ending", include_pf_close=False),
        expr='da_schedule["da_ppe_writeup_beg", @col] + da_schedule["da_ppe_writeup_depr", @col]',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.set_cell(
        "da_ppe_writeup_end", "pf_close", expr='ppa_schedule["ppe_fv_mark", "active_case"]'
    )

    table.add_row(
        "da_depr_existing_assets",
        cells=inactive_pre_pf_cells("Depreciation of existing fixed assets"),
        expr='da_schedule["da_standalone_depr", @col] - da_schedule["da_depr_new_assets", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_depr_new_assets",
        cells=inactive_pre_pf_cells("( + ) Depreciation of new fixed assets"),
        expr='da_schedule["da_depreciation_capex", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_standalone_depr",
        cells=inactive_pre_pf_cells("Standalone depreciation expense"),
        expr='income_statement["is_net_sales", @col] * operating_schedule["active_depr_pct_sales", @col]',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_depr_ppe_writeup_add",
        cells=inactive_pre_pf_cells("( + ) Depreciation / (accretion) of PP&E write-up"),
        expr='-da_schedule["da_ppe_writeup_depr", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_pf_depreciation",
        cells=inactive_pre_pf_cells("Pro forma depreciation expense"),
        expr='da_schedule["da_standalone_depr", @col] + da_schedule["da_depr_ppe_writeup_add", @col]',
        style="total",
        format="currency",
        decimals=3,
    )

    int_p_cells = inactive_pre_pf_cells(
        "Identifiable intangibles amortization period (yrs)",
        include_pf_close=False,
    )
    int_p_cells["pf_close"] = deal.intangibles_writeup_amort_period_years
    for c_id in POST_CLOSE_PERIOD_KEYS:
        int_p_cells[c_id] = None
    table.add_row("da_intangibles_writeup_period", cells=int_p_cells, format="number", decimals=1)

    table.add_row(
        "da_intangibles_writeup_schedule",
        cells=inactive_pre_pf_cells("Identifiable intangibles amortization schedule"),
        format="percentage",
        decimals=2,
    )
    writeup_schedule_rows = ("da_ppe_writeup_schedule", "da_intangibles_writeup_schedule")
    table.set_cells(writeup_schedule_rows, STUB_PERIOD_KEY, expr=WRITEUP_SCHEDULE_STUB_EXPR)
    table.set_cells(
        writeup_schedule_rows,
        slice(ANNUAL_PROJECTION_KEYS[0], FINAL_PERIOD_KEY),
        expr=WRITEUP_SCHEDULE_ANNUAL_EXPR,
    )

    table.add_row(
        "da_intangibles_writeup_beg",
        cells=inactive_pre_pf_cells("Identifiable intangible asset write-up – beginning"),
        expr='da_schedule["da_intangibles_writeup_end", col.prev]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_intangibles_writeup_amort",
        cells=inactive_pre_pf_cells("(Amortization) of identifiable intangible write-up"),
        expr='-da_schedule["da_intangibles_writeup_end", "pf_close"] * da_schedule["da_intangibles_writeup_schedule", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_intangibles_writeup_end",
        cells=inactive_pre_pf_cells(
            "Identifiable intangible asset write-up – ending",
            include_pf_close=False,
        ),
        expr='da_schedule["da_intangibles_writeup_beg", @col] + da_schedule["da_intangibles_writeup_amort", @col]',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.set_cell(
        "da_intangibles_writeup_end",
        "pf_close",
        expr='ppa_schedule["intangibles_fv_mark", "active_case"]',
    )

    table.add_row(
        "da_standalone_amort",
        cells=inactive_pre_pf_cells("Standalone amortization expense"),
        expr='income_statement["is_net_sales", @col] * operating_schedule["active_amort_pct_sales", @col]',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_amort_intangibles_writeup_add",
        cells=inactive_pre_pf_cells("( + ) Amortization of identifiable intangible write-up"),
        expr='-da_schedule["da_intangibles_writeup_amort", @col]',
        format="currency",
        decimals=3,
    )
    table.add_row(
        "da_pf_amortization",
        cells=inactive_pre_pf_cells("Pro forma amortization expense"),
        expr='da_schedule["da_standalone_amort", @col] + da_schedule["da_amort_intangibles_writeup_add", @col]',
        style="total",
        format="currency",
        decimals=3,
    )
    return table
