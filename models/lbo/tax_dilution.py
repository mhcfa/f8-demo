"""Full-horizon Section 382 NOL, Corporate AMT, and Convertible Securities / FDSO schedules."""

from __future__ import annotations

from dataclasses import dataclass

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.registry import SCHED_SWEEP_TRANCHE_SPECS
from models.lbo.timeline import (
    POST_CLOSE_PERIOD_KEYS,
    PRE_CLOSE_ROLL_COLS,
    add_timeline_columns,
)

INACTIVE_TAX_COLS: tuple[str, ...] = (
    "mrq",
    "standalone_close",
    "deal_adjustments",
    "pf_close",
)
ACTIVE_TAX_COLS: tuple[str, ...] = (*PRE_CLOSE_ROLL_COLS, *POST_CLOSE_PERIOD_KEYS)

CONV_PRE_EPS_NON_LEGACY_EXPR = (
    'IFERROR(income_statement["is_gaap_net_income_common", @col] / '
    '(convertible_fdso_schedule["bso", @col] + convertible_fdso_schedule[row.prev(11), @col]), 0)'
)


@dataclass(frozen=True)
class EpsAccretionBlockSpec:
    """Specification for a convertible security tranche in the FDSO schedule."""

    tranche_key: str
    face_row_id: str
    face_label: str
    face_expr: str
    shares_row_id: str
    shares_label: str
    shares_expr: str
    eps_row_id: str
    eps_label: str
    eps_post_expr: str
    eps_pre_expr: str
    dilutive_row_id: str
    dilutive_label: str


CONV_TRANCHE_SPECS: tuple[EpsAccretionBlockSpec, ...] = (
    EpsAccretionBlockSpec(
        tranche_key="legacy_debt",
        face_row_id="conv_face_legacy_debt",
        face_label="Convertible Face Value – Liquidation of options",
        face_expr='debt_sweep_schedule["debt_legacy_debt_face_end", @col]',
        shares_row_id="conv_shares_legacy_debt",
        shares_label="Shares if Converted – Liquidation of options",
        shares_expr='IFERROR(convertible_fdso_schedule[row.prev(11), @col] / tranche_fees_oid["legacy_debt", "conversion_price"], 0)',
        eps_row_id="eps_if_converted_legacy_debt",
        eps_label="EPS if Converted – Liquidation of options",
        eps_post_expr='IFERROR((income_statement["is_gaap_net_income_common", @col] + debt_sweep_schedule["debt_legacy_debt_book_interest", @col] * (1 - nol_amt_schedule["blended_tax_rate", @col] * (1 - tranche_fees_oid["legacy_debt", "is_preferred"]))) / (convertible_fdso_schedule["bso", @col] + convertible_fdso_schedule[row.prev(11), @col]), 0)',
        eps_pre_expr='IFERROR((income_statement["is_gaap_net_income_common", @col] + income_statement["is_interest_existing_debt", @col] * (1 - nol_amt_schedule["blended_tax_rate", @col] * (1 - tranche_fees_oid["legacy_debt", "is_preferred"]))) / (convertible_fdso_schedule["bso", @col] + convertible_fdso_schedule[row.prev(11), @col]), 0)',
        dilutive_row_id="is_conversion_dilutive_legacy_debt",
        dilutive_label="Is Conversion Dilutive? – Liquidation of options",
    ),
    *(
        EpsAccretionBlockSpec(
            tranche_key=t.key,
            face_row_id=f"conv_face_{t.key}",
            face_label=f"Convertible Face Value – {t.name}",
            face_expr=f'debt_sweep_schedule["debt_{t.key}_face_end", @col]',
            shares_row_id=f"conv_shares_{t.key}",
            shares_label=f"Shares if Converted – {t.name}",
            shares_expr=f'IFERROR(convertible_fdso_schedule[row.prev(11), @col] / tranche_fees_oid["{t.key}", "conversion_price"], 0)',
            eps_row_id=f"eps_if_converted_{t.key}",
            eps_label=f"EPS if Converted – {t.name}",
            eps_post_expr=f'IFERROR((income_statement["is_gaap_net_income_common", @col] + debt_sweep_schedule["debt_{t.key}_book_interest", @col] * (1 - nol_amt_schedule["blended_tax_rate", @col] * (1 - tranche_fees_oid["{t.key}", "is_preferred"]))) / (convertible_fdso_schedule["bso", @col] + convertible_fdso_schedule[row.prev(11), @col]), 0)',
            eps_pre_expr=CONV_PRE_EPS_NON_LEGACY_EXPR,
            dilutive_row_id=f"is_conversion_dilutive_{t.key}",
            dilutive_label=f"Is Conversion Dilutive? – {t.name}",
        )
        for t in SCHED_SWEEP_TRANCHE_SPECS
    ),
)


def _add_active_tax_row(
    table: f8.Table,
    row_id: str,
    label: str,
    post_expr: str,
    pre_expr: str | None = None,
    style: f8.SemanticStyle | None = None,
    fmt: f8.FormatPreset = "currency",
    dec: int = 3,
) -> None:
    """Add a row active across the 14 operating tax columns and None across static snapshot columns."""
    cells: dict[str, f8.CellInputValue] = {"label": label}
    for col_id in INACTIVE_TAX_COLS:
        cells[col_id] = None
    table.add_row(row_id, cells=cells, expr=post_expr, style=style, format=fmt, decimals=dec)
    if pre_expr is not None:
        table.set_cells(row_id, slice("mrq_plus_1", "mrq_plus_4"), expr=pre_expr)


def _add_active_tax_input_row(
    table: f8.Table,
    row_id: str,
    label: str,
    val: float,
    fmt: f8.FormatPreset = "percentage",
    dec: int = 2,
) -> None:
    """Add a driver input row populated across the 14 active tax columns."""
    cells: dict[str, f8.CellInputValue] = {"label": label}
    for col_id in INACTIVE_TAX_COLS:
        cells[col_id] = None
    for col_id in ACTIVE_TAX_COLS:
        cells[col_id] = val
    table.add_row(row_id, cells=cells, style="data", format=fmt, decimals=dec)


def build_nol_amt_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 55-row x 18-column `nol_amt_schedule` Section 382 NOL & Corporate AMT schedule."""
    deal = assumptions.deal
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "nol_amt_schedule",
        "Section 382 NOL Carryforward, Limitation & Corporate AMT Schedule",
        subtitle=sub,
        currency="USD",
    )
    add_timeline_columns(table, "Tax / NOL / AMT Schedule Line Item")

    # 1. Tax Rates (Rows 1-3)
    _add_active_tax_input_row(table, "federal_tax_rate", "Federal tax rate", deal.federal_tax_rate)
    _add_active_tax_input_row(
        table, "state_local_tax_rate", "State and local tax rate", deal.state_local_tax_rate
    )
    _add_active_tax_row(
        table,
        "blended_tax_rate",
        "Blended tax rate",
        post_expr='nol_amt_schedule["federal_tax_rate", @col] * (1 - nol_amt_schedule["state_local_tax_rate", @col]) + nol_amt_schedule["state_local_tax_rate", @col]',
        style="subtotal",
        fmt="percentage",
        dec=2,
    )
    table.set_cell(
        "blended_tax_rate", "mrq", expr='income_statement["is_effective_tax_rate", "mrq"]'
    )

    # 2. Taxable Income & Net DTL Roll-Forward (Rows 4-24)
    _add_active_tax_row(
        table,
        "tax_ebitda",
        "EBITDA",
        post_expr='income_statement["is_ebitda", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_depreciation",
        "( – ) Tax depreciation",
        post_expr='-income_statement["is_depreciation", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_amortization",
        "( – ) Tax amortization of intangible assets",
        post_expr='-income_statement["is_amortization", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_sbc",
        "( – ) Stock-based compensation",
        post_expr='-income_statement["is_sbc", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_interest_net",
        "( + ) Interest income / (expense)",
        post_expr='-income_statement["is_interest_expense_net", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_distributed_equity_income",
        "( + ) Distributed equity income in affiliates",
        post_expr="0",
    )
    _add_active_tax_row(
        table,
        "tax_other_income_expense",
        "( + ) Other income / (expense)",
        post_expr='-income_statement["is_other_income_expense", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_loss_unamortized_oid",
        "( – ) Loss on unamortized OID at repayment",
        post_expr='-income_statement["is_loss_unamortized_oid", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_total_taxable_income",
        "Total taxable income",
        post_expr='SUM(nol_amt_schedule["tax_ebitda".."tax_loss_unamortized_oid", @col])',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "tax_nol_used",
        "( – ) NOL used",
        post_expr='nol_amt_schedule["encumbered_nol_used", @col] + nol_amt_schedule["unencumbered_nol_used", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_state_local_taxable_income",
        "State and local taxable income",
        post_expr='nol_amt_schedule["tax_total_taxable_income", @col] + nol_amt_schedule["tax_nol_used", @col]',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "tax_state_local_cash_taxes_ded",
        "( – ) State and local cash taxes",
        post_expr='-MAX(0, nol_amt_schedule["tax_state_local_taxable_income", @col] * nol_amt_schedule["state_local_tax_rate", @col])',
    )
    _add_active_tax_row(
        table,
        "tax_federal_taxable_income",
        "Federal taxable income",
        post_expr='nol_amt_schedule["tax_state_local_taxable_income", @col] + nol_amt_schedule["tax_state_local_cash_taxes_ded", @col]',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "tax_federal_cash_taxes",
        "Federal cash taxes",
        post_expr='nol_amt_schedule["amt_federal_cash_taxes", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_state_local_cash_taxes",
        "( + ) State and local cash taxes",
        post_expr='-nol_amt_schedule["tax_state_local_cash_taxes_ded", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_total_cash_taxes",
        "Total cash taxes payable",
        post_expr='nol_amt_schedule["tax_federal_cash_taxes", @col] + nol_amt_schedule["tax_state_local_cash_taxes", @col]',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "tax_deferred_tax_expense",
        "( + ) Deferred tax expense / (benefit)",
        post_expr='nol_amt_schedule["tax_book_tax_expense", @col] - nol_amt_schedule["tax_total_cash_taxes", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_book_tax_expense",
        "Book tax expense",
        post_expr='income_statement["is_tax_provision", @col]',
        style="total",
    )
    _add_active_tax_row(
        table,
        "tax_net_dtl_beg",
        "Net DTL – beginning balance",
        post_expr='nol_amt_schedule["tax_net_dtl_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "tax_net_dtl_change",
        "Increase / (decrease) in net DTL",
        post_expr='nol_amt_schedule["tax_deferred_tax_expense", @col]',
    )
    _add_active_tax_row(
        table,
        "tax_net_dtl_end",
        "Net DTL – ending balance",
        post_expr='nol_amt_schedule["tax_net_dtl_beg", @col] + nol_amt_schedule["tax_net_dtl_change", @col]',
        style="subtotal",
    )
    table.set_cell("tax_net_dtl_end", "mrq", expr='balance_sheet["bs_net_dtl", "mrq"]')
    table.set_cell("tax_net_dtl_end", "pf_close", expr='transaction_bs["net_dtl", "pf_close"]')

    # 3. Section 382 Limit, Remaining NOL Life, Encumbered & Unencumbered NOLs, DTA (Rows 25-42)
    _add_active_tax_row(
        table,
        "sec382_annual_deduction_limit",
        "Annual Section 382 NOL deduction limit",
        post_expr='ppa_schedule["purchase_price", "active_case"] * ppa_schedule["sec382_irs_rate", "active_case"] * income_statement["is_fractional_years", @col]',
        pre_expr="0",
    )
    table.set_cell("sec382_annual_deduction_limit", "mrq", expr="0")

    _add_active_tax_row(
        table,
        "nol_remaining_life_years",
        "Remaining NOL life (yrs)",
        post_expr='MAX(0, nol_amt_schedule["nol_remaining_life_years", col.prev] - income_statement["is_fractional_years", @col])',
        fmt="number",
        dec=2,
    )
    table.set_cell(
        "nol_remaining_life_years", "mrq", value=deal.nol_remaining_life_years, style="data"
    )
    table.set_cell(
        "nol_remaining_life_years",
        "pf_close",
        expr='nol_amt_schedule["nol_remaining_life_years", "standalone_close"]',
    )

    _add_active_tax_row(
        table,
        "encumbered_nol_beg",
        "Encumbered NOL subject to Sec. 382 – Beginning balance",
        post_expr='nol_amt_schedule["encumbered_nol_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "encumbered_nol_used",
        "Encumbered NOL subject to Sec. 382 – ( – ) NOL used",
        post_expr='IF(nol_amt_schedule["tax_total_taxable_income", @col] > 0, -MIN(nol_amt_schedule["tax_total_taxable_income", @col], nol_amt_schedule["encumbered_nol_beg", @col], nol_amt_schedule["sec382_annual_deduction_limit", @col] + nol_amt_schedule["unused_limit_cf_beg", @col]), 0)',
    )
    _add_active_tax_row(
        table,
        "encumbered_nol_expired",
        "Encumbered NOL subject to Sec. 382 – ( – ) NOL expired",
        post_expr='IF(nol_amt_schedule["nol_remaining_life_years", @col] > 0, 0, -(nol_amt_schedule["encumbered_nol_beg", @col] + nol_amt_schedule["encumbered_nol_used", @col]))',
    )
    _add_active_tax_row(
        table,
        "encumbered_nol_end",
        "Encumbered NOL subject to Sec. 382 – Ending balance",
        post_expr='SUM(nol_amt_schedule["encumbered_nol_beg".."encumbered_nol_expired", @col])',
        style="subtotal",
    )
    table.set_cell("encumbered_nol_end", "mrq", expr="0")
    table.set_cell(
        "encumbered_nol_end",
        "pf_close",
        expr='IF(sources_uses["lbo_flag", "active_case"] = 1, nol_amt_schedule["unencumbered_nol_end", "standalone_close"], 0)',
    )

    _add_active_tax_row(
        table,
        "unused_limit_cf_beg",
        "Unused limitation carryforward – Beginning balance",
        post_expr='nol_amt_schedule["unused_limit_cf_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "unused_limit_cf_created",
        "Unused limitation carryforward – ( + ) Carryforward created",
        post_expr='IF(nol_amt_schedule["encumbered_nol_end", @col] > 0, MAX(0, nol_amt_schedule["sec382_annual_deduction_limit", @col] + nol_amt_schedule["encumbered_nol_used", @col]), 0)',
    )
    _add_active_tax_row(
        table,
        "unused_limit_cf_used",
        "Unused limitation carryforward – ( – ) Carryforward used",
        post_expr='-MAX(0, -nol_amt_schedule["encumbered_nol_used", @col] - nol_amt_schedule["sec382_annual_deduction_limit", @col])',
    )
    _add_active_tax_row(
        table,
        "unused_limit_cf_end",
        "Unused limitation carryforward – Ending balance",
        post_expr='SUM(nol_amt_schedule["unused_limit_cf_beg".."unused_limit_cf_used", @col])',
        style="subtotal",
    )
    table.set_cells("unused_limit_cf_end", ("mrq", "pf_close"), expr="0")

    _add_active_tax_row(
        table,
        "unencumbered_nol_beg",
        "Unencumbered NOL – Beginning balance",
        post_expr='nol_amt_schedule["unencumbered_nol_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "unencumbered_nol_created",
        "Unencumbered NOL – ( + ) NOL created",
        post_expr='MAX(0, -nol_amt_schedule["tax_total_taxable_income", @col])',
    )
    _add_active_tax_row(
        table,
        "unencumbered_nol_used",
        "Unencumbered NOL – ( – ) NOL used",
        post_expr='IF(nol_amt_schedule["tax_total_taxable_income", @col] + nol_amt_schedule["encumbered_nol_used", @col] > 0, -MIN(nol_amt_schedule["unencumbered_nol_beg", @col] + nol_amt_schedule["unencumbered_nol_created", @col], nol_amt_schedule["tax_total_taxable_income", @col] + nol_amt_schedule["encumbered_nol_used", @col]), 0)',
    )
    _add_active_tax_row(
        table,
        "unencumbered_nol_expired",
        "Unencumbered NOL – ( – ) NOL expired",
        post_expr="0",
    )
    _add_active_tax_row(
        table,
        "unencumbered_nol_end",
        "Unencumbered NOL – Ending balance",
        post_expr='SUM(nol_amt_schedule["unencumbered_nol_beg".."unencumbered_nol_expired", @col])',
        style="subtotal",
    )
    table.set_cell("unencumbered_nol_end", "mrq", value=deal.existing_nol, style="data")
    table.set_cell(
        "unencumbered_nol_end",
        "pf_close",
        expr='IF(sources_uses["lbo_flag", "active_case"] = 1, 0, nol_amt_schedule["unencumbered_nol_end", "standalone_close"])',
    )

    _add_active_tax_row(
        table,
        "dta_nol_beg",
        "DTA attributable to NOL – Beginning balance",
        post_expr='nol_amt_schedule["dta_nol_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "dta_nol_change",
        "Increase / (decrease) in DTA attributable to NOL",
        post_expr='(nol_amt_schedule["encumbered_nol_used", @col] + nol_amt_schedule["encumbered_nol_expired", @col] + SUM(nol_amt_schedule["unencumbered_nol_created".."unencumbered_nol_expired", @col])) * nol_amt_schedule["blended_tax_rate", @col]',
    )
    _add_active_tax_row(
        table,
        "dta_nol_end",
        "DTA attributable to NOL – Ending balance",
        post_expr='nol_amt_schedule["dta_nol_beg", @col] + nol_amt_schedule["dta_nol_change", @col]',
        style="subtotal",
    )
    table.set_cell(
        "dta_nol_end",
        "mrq",
        expr='(nol_amt_schedule["encumbered_nol_end", "mrq"] + nol_amt_schedule["unencumbered_nol_end", "mrq"]) * nol_amt_schedule["blended_tax_rate", "mrq_plus_1"]',
    )
    table.set_cell(
        "dta_nol_end",
        "pf_close",
        expr='MIN(ppa_schedule["purchase_price", "active_case"] * ppa_schedule["sec382_irs_rate", "active_case"] * ppa_schedule["statutory_tax_rate", "active_case"] * nol_amt_schedule["nol_remaining_life_years", "pf_close"], nol_amt_schedule["dta_nol_end", "standalone_close"])',
    )

    # 4. Alternative Minimum Tax & AMT Credit Carryforward (Rows 43-55)
    _add_active_tax_input_row(
        table, "amt_corporate_tax_rate", "Corporate AMT tax rate", deal.amt_tax_rate
    )
    _add_active_tax_input_row(
        table, "amt_max_taxable_income_offset", "Maximum taxable income offset", deal.amt_max_offset
    )
    _add_active_tax_row(
        table,
        "amt_effective_tax_rate",
        "Effective AMT tax rate",
        post_expr='nol_amt_schedule["amt_corporate_tax_rate", @col] * (1 - nol_amt_schedule["amt_max_taxable_income_offset", @col])',
        style="subtotal",
        fmt="percentage",
        dec=2,
    )
    _add_active_tax_row(
        table,
        "amt_federal_tax_statutory_post_nol",
        "Federal tax at statutory rate (post-NOL)",
        post_expr='MAX(0, nol_amt_schedule["tax_federal_taxable_income", @col] * nol_amt_schedule["federal_tax_rate", @col])',
    )
    _add_active_tax_row(
        table,
        "amt_before_credits",
        "Alternative minimum tax (before credits)",
        post_expr='MAX(0, (nol_amt_schedule["tax_total_taxable_income", @col] + nol_amt_schedule["tax_state_local_cash_taxes_ded", @col]) * nol_amt_schedule["amt_effective_tax_rate", @col])',
    )
    _add_active_tax_row(
        table,
        "amt_tax_payable_before_credit",
        "Tax payable before AMT credit used",
        post_expr='MAX(nol_amt_schedule["amt_federal_tax_statutory_post_nol", @col], nol_amt_schedule["amt_before_credits", @col])',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "amt_credit_used",
        "( – ) AMT tax credit used",
        post_expr='nol_amt_schedule["amt_credit_cf_used", @col]',
    )
    _add_active_tax_row(
        table,
        "amt_federal_cash_taxes",
        "Federal cash taxes (post-AMT)",
        post_expr='nol_amt_schedule["amt_tax_payable_before_credit", @col] + nol_amt_schedule["amt_credit_used", @col]',
        style="subtotal",
    )
    _add_active_tax_row(
        table,
        "amt_effective_federal_cash_tax_rate",
        "Effective federal cash tax rate",
        post_expr='IFERROR(nol_amt_schedule["amt_federal_cash_taxes", @col] / (nol_amt_schedule["tax_total_taxable_income", @col] + nol_amt_schedule["tax_state_local_cash_taxes_ded", @col]), 0)',
        fmt="percentage",
        dec=2,
    )
    _add_active_tax_row(
        table,
        "amt_credit_cf_beg",
        "AMT tax credit – beginning balance",
        post_expr='nol_amt_schedule["amt_credit_cf_end", col.prev]',
    )
    _add_active_tax_row(
        table,
        "amt_credit_cf_generated",
        "( + ) AMT tax credit generated",
        post_expr='IF(nol_amt_schedule["amt_before_credits", @col] > nol_amt_schedule["amt_federal_tax_statutory_post_nol", @col], nol_amt_schedule["amt_federal_cash_taxes", @col], 0)',
    )
    _add_active_tax_row(
        table,
        "amt_credit_cf_used",
        "( – ) AMT tax credit used (carryforward)",
        post_expr='IF(nol_amt_schedule["amt_federal_tax_statutory_post_nol", @col] > nol_amt_schedule["amt_before_credits", @col], -MIN(nol_amt_schedule["amt_credit_cf_beg", @col], nol_amt_schedule["amt_tax_payable_before_credit", @col] - nol_amt_schedule["amt_before_credits", @col]), 0)',
    )
    _add_active_tax_row(
        table,
        "amt_credit_cf_end",
        "AMT tax credit – ending balance",
        post_expr='SUM(nol_amt_schedule["amt_credit_cf_beg".."amt_credit_cf_used", @col])',
        style="subtotal",
    )
    table.set_cell("amt_credit_cf_end", "mrq", value=deal.amt_credit_carryforward, style="data")
    table.set_cell(
        "amt_credit_cf_end",
        "pf_close",
        expr='nol_amt_schedule["amt_credit_cf_end", "standalone_close"]',
    )
    table.set_cells(
        (
            "nol_remaining_life_years",
            "unencumbered_nol_end",
            "dta_nol_end",
            "amt_credit_cf_end",
        ),
        "standalone_close",
        expr='nol_amt_schedule[@row, "mrq_plus_3"]',
    )

    return table


def build_convertible_fdso_schedule(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the 49-row x 18-column `convertible_fdso_schedule` If-Converted & FDSO schedule."""
    del assumptions
    sub = "Units: $ in millions / shares in millions"
    table = sheet.add_table(
        "convertible_fdso_schedule",
        "Convertible Securities If-Converted Dilution & FDSO Schedule",
        subtitle=sub,
        currency="USD",
    )
    add_timeline_columns(table, "Convertible Dilution / FDSO Line Item")

    # 1. Ending Face Value by Tranche (11 rows)
    for spec in CONV_TRANCHE_SPECS:
        cells: dict[str, f8.CellInputValue] = {
            "label": spec.face_label,
            "standalone_close": None,
            "deal_adjustments": None,
        }
        table.add_row(
            spec.face_row_id,
            cells=cells,
            expr=spec.face_expr,
            format="currency",
            decimals=3,
        )
    table.set_cell(
        "conv_face_legacy_debt", "mrq", expr='balance_sheet["bs_existing_lt_debt", "mrq"]'
    )
    table.set_cells(
        slice("conv_face_term_loan_a", "conv_face_preferred_b"),
        "mrq",
        expr="0",
    )
    table.set_cells(
        slice("conv_face_legacy_debt", "conv_face_preferred_b"),
        slice("mrq_plus_1", "mrq_plus_4"),
        expr="convertible_fdso_schedule[@row, col.prev]",
    )

    # 2. Shares If Converted by Tranche (11 rows)
    for spec in CONV_TRANCHE_SPECS:
        cells = {
            "label": spec.shares_label,
            "standalone_close": None,
            "deal_adjustments": None,
        }
        table.add_row(
            spec.shares_row_id, cells=cells, expr=spec.shares_expr, format="number", decimals=3
        )

    # 3. EPS If Converted by Tranche (11 rows) + Basic EPS (1 row)
    for spec in CONV_TRANCHE_SPECS:
        cells = {
            "label": spec.eps_label,
            "standalone_close": None,
            "deal_adjustments": None,
        }
        table.add_row(
            spec.eps_row_id, cells=cells, expr=spec.eps_post_expr, format="currency", decimals=3
        )
    table.set_cells(
        "eps_if_converted_legacy_debt",
        slice("mrq", "mrq_plus_4"),
        expr=CONV_TRANCHE_SPECS[0].eps_pre_expr,
    )
    table.set_cells(
        slice("eps_if_converted_term_loan_a", "eps_if_converted_preferred_b"),
        slice("mrq", "mrq_plus_4"),
        expr=CONV_PRE_EPS_NON_LEGACY_EXPR,
    )

    basic_cells: dict[str, f8.CellInputValue] = {
        "label": "Basic EPS",
        "standalone_close": None,
        "deal_adjustments": None,
    }
    table.add_row(
        "basic_eps",
        cells=basic_cells,
        expr='IFERROR(income_statement["is_gaap_net_income_common", @col] / convertible_fdso_schedule["bso", @col], 0)',
        style="subtotal",
        format="currency",
        decimals=3,
    )
    table.set_cells(
        slice("eps_if_converted_legacy_debt", "basic_eps"),
        "pf_close",
        expr='convertible_fdso_schedule[@row, "mrq_plus_4"]',
    )

    # 4. Is Conversion Dilutive? Flags by Tranche (11 rows)
    for spec in CONV_TRANCHE_SPECS:
        cells = {
            "label": spec.dilutive_label,
            "standalone_close": None,
            "deal_adjustments": None,
        }
        table.add_row(
            spec.dilutive_row_id,
            cells=cells,
            expr='IF(convertible_fdso_schedule[row.prev(12), @col] < convertible_fdso_schedule["basic_eps", @col], 1, 0)',
            format="integer",
        )

    # 5. Fully Diluted Shares Outstanding Roll-Up (4 rows)
    table.add_row(
        "bso",
        cells={"label": "Basic shares outstanding (BSO)"},
        expr='convertible_fdso_schedule["bso", col.prev]',
        format="number",
        decimals=3,
    )
    table.set_cell("bso", "mrq", expr='valuation_and_fdso["basic_shares_outstanding", "value"]')
    table.set_cell(
        "bso",
        "deal_adjustments",
        expr='IF(sources_uses["lbo_flag", "active_case"] = 1, -convertible_fdso_schedule["bso", "standalone_close"] + sources_uses["sponsor_equity", "active_case"] / valuation_and_fdso["offer_price_per_share", "value"], 0)',
    )

    table.add_row(
        "treasury_method_option_shares",
        cells={"label": "Treasury method option shares"},
        expr='convertible_fdso_schedule["treasury_method_option_shares", col.prev]',
        format="number",
        decimals=3,
    )
    table.set_cells(
        "treasury_method_option_shares",
        slice("mrq", "mrq_plus_4"),
        expr='option_tranches["options_total", "treasury_method_shares"]',
    )
    table.set_cell(
        "treasury_method_option_shares",
        "deal_adjustments",
        expr='IF(sources_uses["lbo_flag", "active_case"] = 1, -convertible_fdso_schedule["treasury_method_option_shares", "standalone_close"], 0)',
    )

    table.add_row(
        "convertible_securities_shares",
        cells={"label": "Convertible securities dilutive shares", "deal_adjustments": None},
        expr=(
            'SUMPRODUCT(convertible_fdso_schedule["conv_shares_legacy_debt".."conv_shares_preferred_b", @col], '
            'convertible_fdso_schedule["is_conversion_dilutive_legacy_debt".."is_conversion_dilutive_preferred_b", @col])'
        ),
        format="number",
        decimals=3,
    )
    table.set_cells(
        slice("bso", "convertible_securities_shares"),
        "standalone_close",
        expr='convertible_fdso_schedule[@row, "mrq_plus_3"]',
    )
    table.set_cells(
        ("bso", "treasury_method_option_shares"),
        "pf_close",
        expr='convertible_fdso_schedule[@row, "standalone_close"] + convertible_fdso_schedule[@row, "deal_adjustments"]',
    )

    table.add_row(
        "fdso",
        cells={"label": "Fully diluted shares outstanding (FDSO)"},
        expr='SUM(convertible_fdso_schedule["bso".."convertible_securities_shares", @col])',
        style="total",
        format="number",
        decimals=3,
    )
    table.set_cell(
        "fdso",
        "deal_adjustments",
        expr='convertible_fdso_schedule["bso", "deal_adjustments"] + convertible_fdso_schedule["treasury_method_option_shares", "deal_adjustments"]',
    )

    return table
