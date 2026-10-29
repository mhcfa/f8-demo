"""Sources & Uses, Tranche Fees & OID, Purchase Price Allocation, and Transaction Balance Sheet builders."""

from __future__ import annotations

from typing import TYPE_CHECKING

import f8

from models.lbo.assumptions.deal import CASE_KEYS
from models.lbo.assumptions.financing import NEW_FINANCING_TRANCHE_KEYS, TRANCHE_KEYS
from models.lbo.assumptions.timeline import TimelineAssumptions
from models.lbo.registry import (
    BALANCE_SHEET_ACCOUNTS,
    NEW_FINANCING_TRANCHE_SPECS,
    TRANCHE_SPECS,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from models.lbo.assumptions import LboAssumptions

BS_LABELS: dict[str, str] = {s.tx_row_id: s.label for s in BALANCE_SHEET_ACCOUNTS}

CASE_HEADERS: dict[str, tuple[str | None, list[str]]] = {
    "case_1_no_deal": ("Financing Scenarios", ["Case 1", "No Deal"]),
    "case_2_refi_a": ("Financing Scenarios", ["Case 2", "Refi A"]),
    "case_3_refi_b": ("Financing Scenarios", ["Case 3", "Refi B"]),
    "case_4_lbo_a": ("Financing Scenarios", ["Case 4", "LBO A"]),
    "case_5_lbo_b": ("Financing Scenarios", ["Case 5", "LBO B"]),
    "case_6_lbo_c": ("Financing Scenarios", ["Case 6", "LBO C"]),
}

TRANCHE_LABELS: dict[str, str] = {s.key: s.name for s in TRANCHE_SPECS}


def build_tx_bs_columns(
    close_date_iso: str = TimelineAssumptions().close_date_iso,
) -> dict[str, tuple[str | None, list[str]]]:
    """Derive transaction balance sheet column definitions from close date."""
    return {
        "pre_deal_close": (None, ["Pre-Deal", "at Close", close_date_iso]),
        "write_off_intangibles": (
            "Purchase Price Allocation Bridge",
            ["Write-Off", "Intangibles"],
        ),
        "fv_marks_pretax": ("Purchase Price Allocation Bridge", ["FV Marks", "(Pre-Tax)"]),
        "new_net_dtl": ("Purchase Price Allocation Bridge", ["New Net DTL", "FV Marks"]),
        "fv_acquired_bs": ("Purchase Price Allocation Bridge", ["Fair Value", "Acquired BS"]),
        "ppa_adjustments": ("Purchase Price Allocation Bridge", ["PPA", "Adjustments"]),
        "acquired_bs": (None, ["Acquired", "BS at Close", close_date_iso]),
        "deal_charges": ("Transaction Financing Adjustments", ["Transaction", "Charges"]),
        "refinance_debt": ("Transaction Financing Adjustments", ["Refinance", "Legacy Debt"]),
        "new_financing": ("Transaction Financing Adjustments", ["New Funding", "Sources"]),
        "pf_close": (None, ["Pro Forma", "at Close", close_date_iso]),
    }


TX_BS_COLUMNS: dict[str, tuple[str | None, list[str]]] = build_tx_bs_columns()

PPA_LABELS: dict[str, str] = {
    "purchase_price": "Purchase price (net of option proceeds)",
    "book_value_equity": "( - ) Book value of common equity",
    "excess_purchase_price": "Excess purchase price to allocate",
    "ppe_fv_mark": "PP&E fair value mark",
    "ppe_dtl_created": "PP&E deferred tax liability created",
    "intangibles_fv_mark": "Identifiable intangibles fair value mark",
    "intangibles_dtl_created": "Identifiable intangibles deferred tax liability created",
    "total_dtl_created": "Total transaction deferred tax liability created",
    "goodwill_created": "Goodwill created",
}


CHOOSE_ACTIVE_CASE_EXPR = (
    'CHOOSE(sources_uses["case_number", "active_case"], '
    'sources_uses[@row, "case_1_no_deal"], '
    'sources_uses[@row, "case_2_refi_a"], '
    'sources_uses[@row, "case_3_refi_b"], '
    'sources_uses[@row, "case_4_lbo_a"], '
    'sources_uses[@row, "case_5_lbo_b"], '
    'sources_uses[@row, "case_6_lbo_c"])'
)


def _tranche_fee_oid_exprs(tranche_key: str) -> tuple[str, str, str]:
    fee_ref = "revolver_commitment" if tranche_key == "revolver" else tranche_key
    oid_ref = "revolver_draw" if tranche_key == "revolver" else tranche_key
    return (
        f'IF(tranche_fees_oid[@row, "is_preferred"] = 0, sources_uses["{fee_ref}", "active_case"] * tranche_fees_oid[@row, "financing_fee_rate"], 0)',
        f'IF(tranche_fees_oid[@row, "is_preferred"] = 1, sources_uses["{fee_ref}", "active_case"] * tranche_fees_oid[@row, "financing_fee_rate"], 0)',
        f'sources_uses["{oid_ref}", "active_case"] * tranche_fees_oid[@row, "oid_rate"]',
    )


TRANCHE_FEE_OID_EXPRS: dict[str, tuple[str, str, str]] = {
    t.key: _tranche_fee_oid_exprs(t.key) for t in NEW_FINANCING_TRANCHE_SPECS
}

PPA_EXPRS: dict[str, str] = {
    "purchase_price": 'sources_uses["equity_purchase_price", "active_case"] - sources_uses["option_liquidation_proceeds", "active_case"]',
    "book_value_equity": '-balance_sheet["bs_total_equity", "standalone_close"] * sources_uses["lbo_flag", "active_case"]',
    "excess_purchase_price": 'ppa_schedule["purchase_price", "active_case"] + ppa_schedule["book_value_equity", "active_case"]',
    "ppe_fv_mark": 'ppa_schedule["ppe_fv_mark_input", "active_case"] * sources_uses["lbo_flag", "active_case"]',
    "ppe_dtl_created": 'ppa_schedule["ppe_fv_mark", "active_case"] * ppa_schedule["statutory_tax_rate", "active_case"]',
    "intangibles_fv_mark": 'ppa_schedule["excess_purchase_price", "active_case"] * ppa_schedule["intangibles_allocation_pct", "active_case"]',
    "intangibles_dtl_created": 'ppa_schedule["intangibles_fv_mark", "active_case"] * ppa_schedule["statutory_tax_rate", "active_case"]',
    "total_dtl_created": (
        'ppa_schedule["ppe_dtl_created", "active_case"] + '
        'ppa_schedule["intangibles_dtl_created", "active_case"] - '
        'balance_sheet["bs_intangibles_net", "standalone_close"] * '
        'ppa_schedule["existing_intangibles_writeoff_pct", "active_case"] * '
        'sources_uses["lbo_flag", "active_case"] * '
        'ppa_schedule["statutory_tax_rate", "active_case"]'
    ),
    "goodwill_created": (
        'MAX(0, ppa_schedule["excess_purchase_price", "active_case"] + '
        '(balance_sheet["bs_goodwill", "standalone_close"] + '
        'balance_sheet["bs_intangibles_net", "standalone_close"] * '
        'ppa_schedule["existing_intangibles_writeoff_pct", "active_case"]) * '
        'sources_uses["lbo_flag", "active_case"] - '
        '(ppa_schedule["ppe_fv_mark", "active_case"] + ppa_schedule["intangibles_fv_mark", "active_case"]) + '
        'ppa_schedule["total_dtl_created", "active_case"])'
    ),
}

TX_BS_PRE_DEAL_EXPRS: dict[str, str] = {
    s.tx_row_id: s.tx_pre_deal_expr
    for s in BALANCE_SHEET_ACCOUNTS
    if s.tx_pre_deal_expr is not None
}

TX_BS_OVERRIDES: dict[str, dict[str, str]] = {
    "cash": {
        "ppa_adjustments": '-ppa_schedule["purchase_price", "active_case"]',
        "deal_charges": '-(1 - ppa_schedule["statutory_tax_rate", "active_case"]) * sources_uses["transaction_costs", "active_case"]',
        "refinance_debt": '-sources_uses["legacy_debt_refinanced", "active_case"] - (1 - ppa_schedule["statutory_tax_rate", "active_case"]) * sources_uses["prepayment_penalties", "active_case"]',
        "new_financing": 'sources_uses["new_funding", "active_case"] - sources_uses["oid", "active_case"] - (1 - ppa_schedule["statutory_tax_rate", "active_case"]) * sources_uses["financing_fees", "active_case"]',
    },
    "ppe_gross": {"fv_marks_pretax": 'ppa_schedule["ppe_fv_mark", "active_case"]'},
    "capitalized_financing_costs": {
        "new_financing": 'tranche_fees_oid["total", "capitalized_financing_fee"]'
    },
    "goodwill": {
        "write_off_intangibles": '-transaction_bs["goodwill", "pre_deal_close"] * sources_uses["lbo_flag", "active_case"]',
        "ppa_adjustments": 'ppa_schedule["goodwill_created", "active_case"]',
    },
    "intangibles_net": {
        "write_off_intangibles": '-transaction_bs["intangibles_net", "pre_deal_close"] * ppa_schedule["existing_intangibles_writeoff_pct", "active_case"] * sources_uses["lbo_flag", "active_case"]',
        "fv_marks_pretax": 'ppa_schedule["intangibles_fv_mark", "active_case"]',
    },
    "existing_lt_debt": {
        "refinance_debt": '-sources_uses["legacy_debt_refinanced", "active_case"]'
    },
    "revolver": {
        "new_financing": 'sources_uses["revolver_draw", "active_case"] - tranche_fees_oid["revolver", "oid_amount"]'
    },
    "term_loan_a": {
        "new_financing": 'sources_uses["term_loan_a", "active_case"] - tranche_fees_oid["term_loan_a", "oid_amount"]'
    },
    "term_loan_b": {
        "new_financing": 'sources_uses["term_loan_b", "active_case"] - tranche_fees_oid["term_loan_b", "oid_amount"]'
    },
    "senior_note": {
        "new_financing": 'sources_uses["senior_note", "active_case"] - tranche_fees_oid["senior_note", "oid_amount"]'
    },
    "subordinated_note": {
        "new_financing": 'sources_uses["subordinated_note", "active_case"] - tranche_fees_oid["subordinated_note", "oid_amount"]'
    },
    "mezzanine": {
        "new_financing": 'sources_uses["mezzanine", "active_case"] - tranche_fees_oid["mezzanine", "oid_amount"]'
    },
    "seller_note": {
        "new_financing": 'sources_uses["seller_note", "active_case"] - tranche_fees_oid["seller_note", "oid_amount"]'
    },
    "convertible_bond": {
        "new_financing": 'sources_uses["convertible_bond", "active_case"] - tranche_fees_oid["convertible_bond", "oid_amount"]'
    },
    "debt_8": {
        "new_financing": 'sources_uses["debt_8", "active_case"] - tranche_fees_oid["debt_8", "oid_amount"]'
    },
    "preferred_a": {
        "new_financing": 'sources_uses["preferred_a", "active_case"] - tranche_fees_oid["preferred_a", "oid_amount"]'
    },
    "preferred_b": {
        "new_financing": 'sources_uses["preferred_b", "active_case"] - tranche_fees_oid["preferred_b", "oid_amount"]'
    },
    "net_dtl": {
        "new_net_dtl": 'ppa_schedule["total_dtl_created", "active_case"]',
        "new_financing": 'ppa_schedule["statutory_tax_rate", "active_case"] * tranche_fees_oid["total", "capitalized_financing_fee"]',
    },
    "common_stock": {
        "ppa_adjustments": '-transaction_bs["common_stock", "fv_acquired_bs"] * sources_uses["lbo_flag", "active_case"]'
    },
    "apic": {
        "ppa_adjustments": '-transaction_bs["apic", "fv_acquired_bs"] * sources_uses["lbo_flag", "active_case"]',
        "new_financing": 'sources_uses["sponsor_equity", "active_case"] + sources_uses["management_equity", "active_case"] - (1 - ppa_schedule["statutory_tax_rate", "active_case"]) * tranche_fees_oid["total", "fee_netted_proceeds"]',
    },
    "retained_earnings": {
        "ppa_adjustments": (
            '-transaction_bs["retained_earnings", "fv_acquired_bs"] * sources_uses["lbo_flag", "active_case"] + '
            'MAX(0, -(ppa_schedule["excess_purchase_price", "active_case"] + '
            '(balance_sheet["bs_goodwill", "standalone_close"] + '
            'balance_sheet["bs_intangibles_net", "standalone_close"] * '
            'ppa_schedule["existing_intangibles_writeoff_pct", "active_case"]) * '
            'sources_uses["lbo_flag", "active_case"] - '
            '(ppa_schedule["ppe_fv_mark", "active_case"] + ppa_schedule["intangibles_fv_mark", "active_case"]) + '
            'ppa_schedule["total_dtl_created", "active_case"]))'
        ),
        "deal_charges": '-(1 - ppa_schedule["statutory_tax_rate", "active_case"]) * sources_uses["transaction_costs", "active_case"]',
        "refinance_debt": '-(1 - ppa_schedule["statutory_tax_rate", "active_case"]) * sources_uses["prepayment_penalties", "active_case"]',
    },
}


def build_sources_uses(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `sources_uses` 6-case Sources & Uses and Active Case table."""
    deal = assumptions.deal
    fin = assumptions.financing
    table = sheet.add_table(
        "sources_uses",
        "Financing Scenarios & Sources and Uses of Funds",
        subtitle="Units: $ in millions",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Sources & Uses Line Item")
    for col_id, (col_group, col_headers) in CASE_HEADERS.items():
        table.add_column(col_id, group=col_group, headers=col_headers)
    table.add_column("active_case", headers=["Active", "Case"])

    choose_input_rows: list[str] = []

    def add_in(
        row_id: str,
        label: str,
        mapping: Mapping[str, float | int],
        fmt: f8.FormatPreset = "currency",
    ) -> None:
        cells: dict[str, f8.CellInputValue] = {"label": label}
        for ck in CASE_KEYS:
            cells[ck] = float(mapping[ck])
        dec = None if fmt == "integer" else 3
        if row_id == "case_number":
            cells["active_case"] = f8.Cell(
                value=float(deal.active_financing_case),
                style="data",
                format=fmt,
                decimals=dec,
            )
        else:
            choose_input_rows.append(row_id)
        table.add_row(row_id, cells=cells, style="data", format=fmt, decimals=dec)

    def add_calc(row_id: str, label: str, expr: str, style: f8.SemanticStyle | None = None) -> None:
        table.add_row(
            row_id, cells={"label": label}, expr=expr, style=style, format="currency", decimals=3
        )

    add_in("case_number", "Financing scenario case", fin.case_numbers_by_case, fmt="integer")
    add_in("lbo_flag", "LBO transaction flag", fin.lbo_flag_by_case, fmt="integer")
    add_in("revolver_commitment", "New revolver bank commitment", fin.revolver_commitment_by_case)

    table.add_section_header("Sources of Funds")
    add_calc(
        "excess_cash",
        "Excess cash",
        'IF(sources_uses["revolver_commitment", @col] + sources_uses["lbo_flag", @col] > 0, MAX(0, balance_sheet["bs_cash", "standalone_close"] - dashboard_entry_valuation["minimum_cash_balance", "metric_value"]), 0)',
    )
    add_calc(
        "option_liquidation_proceeds",
        "Proceeds from liquidation of options",
        'IF(sources_uses["lbo_flag", @col] = 1, option_tranches["options_total", "liquidation_proceeds"], 0)',
    )

    for tk in NEW_FINANCING_TRANCHE_KEYS:
        su_r = "revolver_draw" if tk == "revolver" else tk
        add_in(
            su_r,
            "Revolver draw-down" if tk == "revolver" else TRANCHE_LABELS[tk],
            fin.get_draws_by_case(tk),
        )

    add_calc(
        "sponsor_equity",
        "Sponsor equity",
        'IF(sources_uses["lbo_flag", @col] = 1, (sources_uses["equity_purchase_price", @col] + sources_uses["legacy_debt_refinanced", @col] + sources_uses["oid", @col] + sources_uses["prepayment_penalties", @col] + sources_uses["financing_fees", @col] + sources_uses["transaction_costs", @col]) - (sources_uses["excess_cash", @col] + sources_uses["option_liquidation_proceeds", @col] + SUM(sources_uses["revolver_draw".."preferred_b", @col]) + sources_uses["management_equity", @col] + sources_uses["tax_refund", @col]), 0)',
    )
    add_in("management_equity", "Management equity", fin.management_equity_by_case)
    add_calc(
        "new_funding",
        "New funding",
        'SUM(sources_uses["revolver_draw".."management_equity", @col])',
        "subtotal",
    )
    add_calc(
        "tax_refund",
        "Tax refund",
        'ppa_schedule["statutory_tax_rate", "active_case"] * (sources_uses["transaction_costs", @col] + sources_uses["prepayment_penalties", @col] + sources_uses["financing_fees", @col])',
    )
    add_calc(
        "total_sources",
        "Total sources",
        'sources_uses["excess_cash", @col] + sources_uses["option_liquidation_proceeds", @col] + sources_uses["new_funding", @col] + sources_uses["tax_refund", @col]',
        "total",
    )

    table.add_section_header("Uses of Funds")
    add_calc(
        "equity_purchase_price",
        "Equity purchase price",
        'IF(sources_uses["lbo_flag", @col] = 1, valuation_and_fdso["fdso_liquidation", "value"] * valuation_and_fdso["offer_price_per_share", "value"], 0)',
    )
    add_calc(
        "legacy_debt_refinanced",
        "Legacy debt refinanced",
        'sources_uses["legacy_debt_refinanced_flag", @col] * balance_sheet["bs_existing_lt_debt", "standalone_close"]',
    )
    add_calc(
        "fund_cash_balance",
        "Fund cash balance",
        'IF(sources_uses["lbo_flag", @col] = 0, MAX(0, (sources_uses["excess_cash", @col] + SUM(sources_uses["revolver_draw".."preferred_b", @col]) + sources_uses["tax_refund", @col]) - (sources_uses["equity_purchase_price", @col] + sources_uses["legacy_debt_refinanced", @col] + sources_uses["oid", @col] + sources_uses["prepayment_penalties", @col] + sources_uses["financing_fees", @col] + sources_uses["transaction_costs", @col])), 0)',
    )

    add_calc(
        "oid",
        "OID",
        'SUMPRODUCT(sources_uses["revolver_draw".."preferred_b", @col], tranche_fees_oid["revolver".."preferred_b", "oid_rate"])',
    )
    add_calc(
        "prepayment_penalties",
        "Prepayment penalties",
        'sources_uses["legacy_debt_refinanced", @col] * ppa_schedule["prepayment_penalty_rate", "active_case"]',
    )
    add_calc(
        "financing_fees",
        "Financing fees",
        'sources_uses["revolver_commitment", @col] * tranche_fees_oid["revolver", "financing_fee_rate"] + SUMPRODUCT(sources_uses["term_loan_a".."preferred_b", @col], tranche_fees_oid["term_loan_a".."preferred_b", "financing_fee_rate"])',
    )
    add_calc(
        "advisory_fee",
        "Advisory fee",
        'sources_uses["equity_purchase_price", @col] * ppa_schedule["advisory_fee_rate", "active_case"]',
    )
    add_calc(
        "sponsor_fee",
        "Sponsor fee",
        'sources_uses["equity_purchase_price", @col] * ppa_schedule["sponsor_fee_rate", "active_case"]',
    )
    add_in("legal_fee", "Legal fee", deal.legal_fee_by_case)
    add_in("accounting_fee", "Accounting fee", deal.accounting_fee_by_case)
    add_in("printing_fee", "Printing fee", deal.printing_fee_by_case)
    add_in("other_fee", "Other fee", deal.other_fee_by_case)
    add_calc(
        "transaction_costs",
        "Transaction costs expensed at close",
        'SUM(sources_uses["advisory_fee".."other_fee", @col])',
        "subtotal",
    )
    add_calc(
        "total_uses",
        "Total uses",
        'SUM(sources_uses["equity_purchase_price".."financing_fees", @col]) + sources_uses["transaction_costs", @col]',
        "total",
    )
    add_calc(
        "sources_uses_check",
        "Sources equal uses check",
        'sources_uses["total_sources", @col] - sources_uses["total_uses", @col]',
    )
    add_in(
        "legacy_debt_refinanced_flag",
        "Legacy debt refinancing trigger",
        deal.legacy_debt_refinanced_by_case,
        fmt="integer",
    )
    table.set_cells(tuple(choose_input_rows), "active_case", expr=CHOOSE_ACTIVE_CASE_EXPR)
    return table


def build_tranche_fees_oid(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `tranche_fees_oid` Financing Triggers, Capitalized Fees, and OID table."""
    fin = assumptions.financing
    table = sheet.add_table(
        "tranche_fees_oid",
        "Financing Triggers, Fees & Original Issue Discount",
        subtitle="Units: $ in millions",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Capital Structure Tranche")
    table.add_column(
        "is_senior", group="Classification", headers=["Senior", "Debt?"], format="integer"
    )
    table.add_column(
        "is_preferred", group="Classification", headers=["Preferred", "Security?"], format="integer"
    )
    table.add_column(
        "financing_fee_rate",
        group="Financing Fees",
        headers=["Financing", "Fee (%)"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "fee_amort_years",
        group="Financing Fees",
        headers=["Fee Amort.", "(yrs)"],
        format="number",
        decimals=1,
    )
    table.add_column(
        "capitalized_financing_fee",
        group="Financing Fees",
        headers=["Capitalized", "Fee ($M)"],
        format="currency",
        decimals=3,
    )
    table.add_column(
        "fee_netted_proceeds",
        group="Financing Fees",
        headers=["Fee Netted", "Proceeds"],
        format="currency",
        decimals=3,
    )
    table.add_column(
        "fixed_coupon_rate",
        group="Coupon & Spread",
        headers=["Fixed", "Coupon (%)"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "libor_spread",
        group="Coupon & Spread",
        headers=["Spread to", "LIBOR (%)"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "oid_rate",
        group="Original Issue Discount (OID)",
        headers=["OID", "Rate (%)"],
        format="percentage",
        decimals=2,
    )
    table.add_column(
        "oid_amort_years",
        group="Original Issue Discount (OID)",
        headers=["OID Amort.", "(yrs)"],
        format="number",
        decimals=1,
    )
    table.add_column(
        "oid_amount",
        group="Original Issue Discount (OID)",
        headers=["OID Amount", "($M)"],
        format="currency",
        decimals=3,
    )
    table.add_column(
        "conversion_price",
        group="Equity Features",
        headers=["Conversion", "Price ($)"],
        format="currency",
        decimals=2,
    )
    table.add_column(
        "equity_kicker_pct",
        group="Equity Features",
        headers=["Equity", "Kicker (%)"],
        format="percentage",
        decimals=2,
    )

    for tk in TRANCHE_KEYS:
        terms = fin.get_tranche(tk)
        cells: dict[str, f8.CellInputValue] = {
            "label": TRANCHE_LABELS[tk],
            "is_senior": float(terms.is_senior),
            "is_preferred": float(terms.is_preferred),
            "financing_fee_rate": terms.financing_fee_rate,
            "fee_amort_years": terms.fee_amort_years,
            "fixed_coupon_rate": terms.fixed_coupon_rate,
            "libor_spread": terms.libor_spread,
            "oid_rate": terms.oid_rate,
            "oid_amort_years": terms.oid_amort_years,
            "conversion_price": terms.conversion_price,
            "equity_kicker_pct": terms.equity_kicker_pct,
        }
        if tk != "legacy_debt":
            cap_e, net_e, oid_e = TRANCHE_FEE_OID_EXPRS[tk]
            cells["capitalized_financing_fee"] = f8.Cell(
                expr=cap_e, style="data", format="currency", decimals=3
            )
            cells["fee_netted_proceeds"] = f8.Cell(
                expr=net_e, style="data", format="currency", decimals=3
            )
            cells["oid_amount"] = f8.Cell(expr=oid_e, style="data", format="currency", decimals=3)
        table.add_row(tk, cells=cells, style="data")
    table.set_cells(
        "legacy_debt",
        ("capitalized_financing_fee", "fee_netted_proceeds", "oid_amount"),
        expr="0",
        format="currency",
        decimals=3,
    )

    tot_cells: dict[str, f8.CellInputValue] = {"label": "Total"}
    for nsc in (
        "is_senior",
        "is_preferred",
        "financing_fee_rate",
        "fee_amort_years",
        "fixed_coupon_rate",
        "libor_spread",
        "oid_rate",
        "oid_amort_years",
        "conversion_price",
        "equity_kicker_pct",
    ):
        tot_cells[nsc] = None
    table.add_row("total", cells=tot_cells, style="total")
    table.set_cells(
        "total",
        ("capitalized_financing_fee", "fee_netted_proceeds", "oid_amount"),
        expr='SUM(tranche_fees_oid["revolver".."preferred_b", @col])',
        style="total",
        format="currency",
        decimals=3,
    )
    return table


def build_ppa_schedule(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `ppa_schedule` Purchase Price Allocation and Goodwill Creation schedule."""
    deal = assumptions.deal
    table = sheet.add_table(
        "ppa_schedule",
        "Purchase Price Allocation Schedule",
        subtitle="Units: $ in millions",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="PPA Component")
    table.add_column("active_case", headers=["Active", "Case ($M)"], format="currency", decimals=3)

    ppa_inputs: tuple[tuple[str, str, float, f8.FormatPreset, int | None], ...] = (
        (
            "ppe_fv_mark_input",
            "PP&E fair value mark assumption",
            deal.ppe_fair_value_mark,
            "currency",
            3,
        ),
        (
            "intangibles_allocation_pct",
            "Excess purchase price allocated to intangibles (%)",
            deal.excess_purchase_price_to_intangibles_pct,
            "percentage",
            2,
        ),
        (
            "existing_intangibles_writeoff_pct",
            "Existing intangibles purchase accounting write-off (%)",
            deal.existing_intangibles_purch_acct_pct,
            "percentage",
            2,
        ),
        (
            "prepayment_penalty_rate",
            "Legacy debt prepayment penalty rate (%)",
            deal.legacy_debt_prepayment_penalty_rate,
            "percentage",
            2,
        ),
        (
            "advisory_fee_rate",
            "Advisory fee rate (% of equity purchase price)",
            deal.advisory_fee_rate,
            "percentage",
            2,
        ),
        (
            "sponsor_fee_rate",
            "Sponsor fee rate (% of equity purchase price)",
            deal.sponsor_fee_rate,
            "percentage",
            2,
        ),
        (
            "mgmt_performance_equity_pct",
            "Management performance equity allocation (%)",
            deal.mgmt_performance_equity_pct,
            "percentage",
            2,
        ),
        (
            "exit_valuation_method",
            "Exit valuation method selector",
            float(deal.exit_valuation_method),
            "integer",
            None,
        ),
        (
            "balance_check_tolerance",
            "Balance check tolerance ($M)",
            deal.balance_check_tolerance,
            "currency",
            6,
        ),
        (
            "statutory_tax_rate",
            "Statutory tax rate",
            deal.statutory_tax_rate,
            "percentage",
            2,
        ),
        (
            "sec382_irs_rate",
            "IRS Section 382 long-term tax-exempt rate",
            deal.irs_section_382_rate,
            "percentage",
            2,
        ),
    )
    for r_id, r_lbl, r_val, r_fmt, r_dec in ppa_inputs:
        table.add_row(
            r_id,
            cells={
                "label": r_lbl,
                "active_case": f8.Cell(
                    value=r_val,
                    style="data",
                    format=r_fmt,
                    decimals=r_dec,
                ),
            },
            style="data",
        )

    for r_id, r_lbl in PPA_LABELS.items():
        r_style: f8.SemanticStyle | None = (
            "total"
            if r_id == "goodwill_created"
            else ("subtotal" if r_id in {"excess_purchase_price", "total_dtl_created"} else None)
        )
        table.add_row(r_id, cells={"label": r_lbl}, expr=PPA_EXPRS[r_id], style=r_style)
    return table


def build_transaction_bs(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `transaction_bs` 11-column Transaction Balance Sheet bridge."""
    table = sheet.add_table(
        "transaction_bs",
        "Transaction Balance Sheet Bridge",
        subtitle="Units: $ in millions",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Balance Sheet Line Item")
    tx_bs_cols = build_tx_bs_columns(assumptions.timeline.close_date_iso)
    for col_id, (col_group, col_headers) in tx_bs_cols.items():
        table.add_column(
            col_id, group=col_group, headers=col_headers, format="currency", decimals=3
        )

    adj_cols = (
        "write_off_intangibles",
        "fv_marks_pretax",
        "new_net_dtl",
        "ppa_adjustments",
        "deal_charges",
        "refinance_debt",
        "new_financing",
    )
    vertical_exprs: dict[str, tuple[str, f8.SemanticStyle | None]] = {
        s.tx_row_id: (s.tx_vertical_expr, s.style)
        for s in BALANCE_SHEET_ACCOUNTS
        if s.is_vertical_calc and s.tx_vertical_expr is not None
    }

    non_vertical_rows = tuple(r_id for r_id in BS_LABELS if r_id not in vertical_exprs)
    for r_id, r_lbl in BS_LABELS.items():
        if r_id in vertical_exprs:
            v_expr, v_style = vertical_exprs[r_id]
            table.add_row(r_id, cells={"label": r_lbl}, expr=v_expr, style=v_style)
        else:
            row_ov = TX_BS_OVERRIDES.get(r_id, {})
            row_cells: dict[str, f8.CellInputValue] = {
                "label": r_lbl,
                "pre_deal_close": f8.Cell(expr=TX_BS_PRE_DEAL_EXPRS[r_id]),
            }
            for ac in adj_cols:
                row_cells[ac] = f8.Cell(expr=row_ov.get(ac, "0"))
            table.add_row(r_id, cells=row_cells)
    table.set_cells(
        non_vertical_rows,
        "fv_acquired_bs",
        expr='SUM(transaction_bs[@row, "pre_deal_close".."new_net_dtl"])',
    )
    table.set_cells(
        non_vertical_rows,
        "acquired_bs",
        expr='transaction_bs[@row, "fv_acquired_bs"] + transaction_bs[@row, "ppa_adjustments"]',
    )
    table.set_cells(
        non_vertical_rows,
        "pf_close",
        expr='SUM(transaction_bs[@row, "acquired_bs".."new_financing"])',
    )
    return table
