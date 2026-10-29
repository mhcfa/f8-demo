"""Post-close scheduled debt amortization, excess cash flow sweep waterfall, and 12-tranche roll-forwards."""

from __future__ import annotations

from typing import TYPE_CHECKING

import f8

from models.lbo.registry import (
    NON_REVOLVER_TRANCHE_SPECS,
    SCHED_SWEEP_TRANCHE_SPECS,
    TRANCHE_SPECS,
)
from models.lbo.timeline import (
    ANNUAL_PROJECTION_KEYS,
    FINAL_PERIOD_KEY,
    POST_CLOSE_PERIOD_KEYS,
    PRE_CLOSE_ALL_COLS,
    STUB_PERIOD_KEY,
    add_timeline_columns,
    inactive_pre_pf_cells,
)

if TYPE_CHECKING:
    from models.lbo.assumptions import LboAssumptions

NON_REVOLVER_TRANCHE_KEYS: tuple[str, ...] = tuple(s.key for s in NON_REVOLVER_TRANCHE_SPECS)

TRANCHE_SECTION_TITLES: dict[str, str] = {
    s.key: s.section_title for s in TRANCHE_SPECS if s.key != "revolver"
}

TRANCHE_ROW_LABELS: dict[str, str] = {s.key: s.name for s in TRANCHE_SPECS if s.key != "revolver"}

SCHED_SWEEP_TRANCHE_KEYS: tuple[str, ...] = tuple(s.key for s in SCHED_SWEEP_TRANCHE_SPECS)

INACTIVE_LEGACY_ROLL_COLS: tuple[str, ...] = (
    "mrq",
    "standalone_close",
    "deal_adjustments",
    "pf_close",
)

SCHED_AMORT_STUB_EXPR = (
    'debt_sweep_schedule[@row, "standalone_close"] * '
    f'income_statement["is_fractional_years", "{STUB_PERIOD_KEY}"]'
)

SCHED_AMORT_ANNUAL_EXPR = (
    'IF(debt_sweep_schedule["debt_period_number", @col] = debt_sweep_schedule[@row, "pf_close"], '
    f'1 - SUM(debt_sweep_schedule[@row, "{STUB_PERIOD_KEY}"..col.prev]), '
    'MIN(debt_sweep_schedule[@row, "standalone_close"], '
    f'1 - SUM(debt_sweep_schedule[@row, "{STUB_PERIOD_KEY}"..col.prev])))'
)

SWEEP_OPT_NON_REVOLVER_SPECS: tuple[tuple[str, str, str, str], ...] = tuple(
    (
        tk,
        f"sweep_opt_{tk}",
        f"Optional repayment - {TRANCHE_ROW_LABELS[tk]}",
        (
            f'-MAX(0, MIN(debt_sweep_schedule["debt_{tk}_face_beg", @col] + '
            f'debt_sweep_schedule["debt_{tk}_face_pik", @col] + '
            f'debt_sweep_schedule["debt_{tk}_face_mandatory", @col], '
            'debt_sweep_schedule["sweep_cash_available_for_sweep", @col] + '
            'SUM(debt_sweep_schedule["sweep_opt_revolver"..row.prev, @col]), '
            f'debt_sweep_schedule["debt_{tk}_face_end", "pf_close"] * '
            'debt_sweep_schedule[@row, "deal_adjustments"]))'
        ),
    )
    for tk in NON_REVOLVER_TRANCHE_KEYS
)


def _add_driver_rows(table: f8.Table, assumptions: LboAssumptions) -> None:
    table.add_section_header("Financing Assumptions & Rate Curves")
    fin = assumptions.financing
    cash_rate_cells = inactive_pre_pf_cells("Cash interest yield (%)", include_pf_close=False)
    cash_rate_cells["pf_close"] = fin.cash_interest_rate
    for c_id in POST_CLOSE_PERIOD_KEYS:
        cash_rate_cells[c_id] = None
    table.add_row(
        "cash_interest_rate",
        cells=cash_rate_cells,
        style="data",
        format="percentage",
        decimals=2,
    )

    rev_fee_cells = inactive_pre_pf_cells(
        "Revolver undrawn commitment fee rate (%)",
        include_pf_close=False,
    )
    rev_fee_cells["pf_close"] = fin.revolver_undrawn_commitment_fee_rate
    for c_id in POST_CLOSE_PERIOD_KEYS:
        rev_fee_cells[c_id] = None
    table.add_row(
        "revolver_undrawn_fee_rate",
        cells=rev_fee_cells,
        style="data",
        format="percentage",
        decimals=2,
    )

    p_cells = inactive_pre_pf_cells("Post-close period index")
    for p_idx, col_id in enumerate(POST_CLOSE_PERIOD_KEYS, start=1):
        p_cells[col_id] = float(p_idx)
    table.add_row("debt_period_number", cells=p_cells, format="integer")

    table.add_row_gutter()
    table.add_section_header("Scheduled Debt Amortization Rates (%)")
    for tk in NON_REVOLVER_TRANCHE_KEYS:
        terms = fin.get_tranche(tk)
        sa_r = f"debt_sched_amort_{tk}"
        sa_lbl = f"Scheduled amortization % - {TRANCHE_ROW_LABELS[tk]}"
        sa_cells = inactive_pre_pf_cells(sa_lbl, include_pf_close=False)
        sa_cells["standalone_close"] = terms.periodic_amort_rate
        sa_cells["pf_close"] = f8.Cell(value=terms.term_years, style="data", format="number")
        table.add_row(
            sa_r,
            cells=sa_cells,
            format="percentage",
            decimals=2,
        )
    first_sa_r = f"debt_sched_amort_{NON_REVOLVER_TRANCHE_KEYS[0]}"
    last_sa_r = f"debt_sched_amort_{NON_REVOLVER_TRANCHE_KEYS[-1]}"
    table.set_cells(
        slice(first_sa_r, last_sa_r),
        STUB_PERIOD_KEY,
        expr=SCHED_AMORT_STUB_EXPR,
    )
    table.set_cells(
        slice(first_sa_r, last_sa_r),
        slice(ANNUAL_PROJECTION_KEYS[0], FINAL_PERIOD_KEY),
        expr=SCHED_AMORT_ANNUAL_EXPR,
    )

    table.add_row_gutter()
    table.add_section_header("Original Issue Discount (OID) Remaining Life (Years)")
    for tk in SCHED_SWEEP_TRANCHE_KEYS:
        oid_r = f"debt_oid_rem_life_{tk}"
        oid_lbl = f"Remaining OID amortization life (yrs) - {TRANCHE_ROW_LABELS[tk]}"
        oid_cells = inactive_pre_pf_cells(oid_lbl, include_pf_close=False)
        oid_cells["pf_close"] = f8.Cell(expr=f'tranche_fees_oid["{tk}", "oid_amort_years"]')
        table.add_row(
            oid_r,
            cells=oid_cells,
            expr='MAX(debt_sweep_schedule[@row, col.prev] - income_statement["is_fractional_years", @col], 0)',
            format="number",
            decimals=2,
        )

    table.add_row_gutter()
    table.add_section_header("Benchmark Interest Rate")
    libor_cells = inactive_pre_pf_cells("3-month LIBOR")
    for col_id, l_val in zip(POST_CLOSE_PERIOD_KEYS, fin.libor_curve, strict=True):
        libor_cells[col_id] = l_val
    table.add_row("debt_libor", cells=libor_cells, style="data", format="percentage", decimals=2)

    table.add_row_gutter()
    table.add_section_header("Stated Interest & Dividend Rates (%)")
    all_rate_tranches = ("legacy_debt", "revolver", *SCHED_SWEEP_TRANCHE_KEYS)
    for tk in all_rate_tranches:
        lbl = "Revolver" if tk == "revolver" else TRANCHE_ROW_LABELS[tk]
        rate_lbl = f"Stated interest / dividend rate - {lbl}"
        is_legacy = tk == "legacy_debt"
        if is_legacy:
            rate_cells: dict[str, f8.CellInputValue] = dict.fromkeys(
                INACTIVE_LEGACY_ROLL_COLS, None
            )
            rate_cells["label"] = rate_lbl
        else:
            rate_cells = inactive_pre_pf_cells(rate_lbl)
        rate_expr = (
            f'IF(tranche_fees_oid["{tk}", "fixed_coupon_rate"] = 0, '
            f'debt_sweep_schedule["debt_libor", @col] + tranche_fees_oid["{tk}", "libor_spread"], '
            f'tranche_fees_oid["{tk}", "fixed_coupon_rate"])'
        )
        table.add_row(
            f"debt_rate_{tk}",
            cells=rate_cells,
            expr=rate_expr,
            format="percentage",
            decimals=2,
        )

    table.add_row_gutter()
    table.add_section_header("Payment-in-Kind (PIK) Schedule (%)")
    for tk in SCHED_SWEEP_TRANCHE_KEYS:
        pik_r = f"debt_pik_pct_{tk}"
        pik_lbl = f"PIK % of interest / dividend - {TRANCHE_ROW_LABELS[tk]}"
        pik_cells = inactive_pre_pf_cells(pik_lbl)
        for col_id, p_val in zip(
            POST_CLOSE_PERIOD_KEYS, fin.get_tranche(tk).pik_pct_schedule, strict=True
        ):
            pik_cells[col_id] = p_val
        table.add_row(pik_r, cells=pik_cells, style="data", format="percentage", decimals=2)


def _add_sweep_waterfall_rows(table: f8.Table, assumptions: LboAssumptions) -> None:
    table.add_row_gutter()
    table.add_section_header("Cash Sweep Waterfall")
    fin = assumptions.financing

    def add_sw(
        row_id: str,
        lbl: str,
        expr: str,
        style: f8.SemanticStyle | None = None,
        sweep_flag: int | None = None,
    ) -> None:
        if sweep_flag is None:
            cells = inactive_pre_pf_cells(lbl)
        else:
            cells = dict.fromkeys((*PRE_CLOSE_ALL_COLS, "standalone_close", "pf_close"), None)
            cells["label"] = lbl
            cells["deal_adjustments"] = f8.Cell(
                value=float(sweep_flag),
                style="data",
                format="integer",
            )
        table.add_row(
            row_id,
            cells=cells,
            expr=expr,
            style=style,
            format="currency",
            decimals=3,
        )

    add_sw("sweep_beg_cash", "Beginning cash balance", 'balance_sheet["bs_cash", col.prev]')
    add_sw(
        "sweep_min_cash",
        "( – ) Minimum cash balance",
        '-dashboard_entry_valuation["minimum_cash_balance", "metric_value"]',
    )
    add_sw(
        "sweep_excess_cash",
        "Excess cash / (cash deficit)",
        'debt_sweep_schedule["sweep_beg_cash", @col] + debt_sweep_schedule["sweep_min_cash", @col]',
        "subtotal",
    )
    add_sw(
        "sweep_cf_available_debt_service",
        "( + ) Cash flow available for debt service",
        'cash_flow_statement["cf_cash_available_for_debt_repayment", @col]',
    )
    add_sw(
        "sweep_total_cash_available",
        "Total cash available for debt service",
        'debt_sweep_schedule["sweep_excess_cash", @col] + debt_sweep_schedule["sweep_cf_available_debt_service", @col]',
        "subtotal",
    )
    table.add_row_gutter()
    table.add_section_header("Mandatory Debt Amortization")
    for tk in SCHED_SWEEP_TRANCHE_KEYS:
        add_sw(
            f"sweep_sched_{tk}",
            f"Scheduled repayment - {TRANCHE_ROW_LABELS[tk]}",
            f'debt_sweep_schedule["debt_{tk}_face_mandatory", @col]',
        )
    first_sched_r = f"sweep_sched_{SCHED_SWEEP_TRANCHE_KEYS[0]}"
    last_sched_r = f"sweep_sched_{SCHED_SWEEP_TRANCHE_KEYS[-1]}"
    add_sw(
        "sweep_scheduled_repayment_total",
        "( – ) Scheduled debt repayment",
        f'SUM(debt_sweep_schedule["{first_sched_r}".."{last_sched_r}", @col])',
        "subtotal",
    )
    add_sw(
        "sweep_cash_available_for_sweep",
        "Cash available for sweep / (revolver draw)",
        'debt_sweep_schedule["sweep_total_cash_available", @col] + debt_sweep_schedule["sweep_scheduled_repayment_total", @col]',
        "subtotal",
    )

    table.add_row_gutter()
    table.add_section_header("Optional Debt Prepayment Waterfall (Seniority Order)")

    rev_sweep = fin.revolver.cash_sweep_enabled
    rev_opt_expr = (
        "0"
        if rev_sweep == 0
        else '-MAX(0, MIN(debt_sweep_schedule["debt_revolver_beg", @col], debt_sweep_schedule["sweep_cash_available_for_sweep", @col]))'
    )
    add_sw(
        "sweep_opt_revolver",
        "Optional repayment - Revolver",
        rev_opt_expr,
        sweep_flag=rev_sweep,
    )

    for tk, opt_r, opt_lbl, active_opt_expr in SWEEP_OPT_NON_REVOLVER_SPECS:
        terms = fin.get_tranche(tk)
        opt_expr = "0" if terms.cash_sweep_enabled == 0 else active_opt_expr
        add_sw(
            opt_r,
            opt_lbl,
            opt_expr,
            sweep_flag=terms.cash_sweep_enabled,
        )

    last_opt_r = f"sweep_opt_{NON_REVOLVER_TRANCHE_KEYS[-1]}"
    add_sw(
        "sweep_optional_repayment_total",
        "Total optional debt repayment",
        f'SUM(debt_sweep_schedule["sweep_opt_revolver".."{last_opt_r}", @col])',
        "total",
    )


def _add_tranche_rollforward_rows(table: f8.Table, assumptions: LboAssumptions) -> None:
    table.add_row_gutter()
    table.add_section_header("Debt Tranche Roll-Forwards & Expense Ledgers")
    fin = assumptions.financing

    def add_d(
        row_id: str,
        lbl: str,
        expr: str,
        pf_expr: str | None = None,
        style: f8.SemanticStyle | None = None,
        is_legacy: bool = False,
        mrq_expr: str | None = None,
        pre_roll_expr: str | None = None,
    ) -> None:
        if is_legacy:
            cells: dict[str, f8.CellInputValue] = dict.fromkeys(INACTIVE_LEGACY_ROLL_COLS, None)
            cells["label"] = lbl
            if mrq_expr is not None:
                cells["mrq"] = f8.Cell(expr=mrq_expr, style=style)
        else:
            cells = inactive_pre_pf_cells(lbl)
            if mrq_expr is not None:
                cells["mrq"] = f8.Cell(expr=mrq_expr, style=style)
        if pf_expr is not None:
            cells["pf_close"] = f8.Cell(expr=pf_expr, style=style)
        table.add_row(row_id, cells=cells, expr=expr, style=style, format="currency", decimals=3)
        if pre_roll_expr is not None:
            table.set_cells(
                row_id,
                slice("mrq_plus_1", "mrq_plus_4"),
                expr=pre_roll_expr,
                style=style,
            )

    table.add_row_gutter()
    table.add_section_header("Revolving Credit Facility")
    add_d(
        "debt_revolver_beg",
        "Revolver - Beginning balance",
        'debt_sweep_schedule["debt_revolver_end", col.prev]',
    )
    add_d(
        "debt_revolver_draw",
        "Revolver - Draw-down",
        'MIN(MAX(0, -debt_sweep_schedule["sweep_cash_available_for_sweep", @col]), debt_sweep_schedule["debt_revolver_commitment", @col] - debt_sweep_schedule["debt_revolver_beg", @col])',
    )
    add_d(
        "debt_revolver_paydown",
        "Revolver - Pay-down",
        'debt_sweep_schedule["sweep_opt_revolver", @col]',
    )
    add_d(
        "debt_revolver_end",
        "Revolver - Ending balance",
        'SUM(debt_sweep_schedule["debt_revolver_beg".."debt_revolver_paydown", @col])',
        pf_expr='sources_uses["revolver_draw", "active_case"]',
        style="subtotal",
    )
    add_d(
        "debt_revolver_commitment",
        "Revolver - Bank commitment",
        'debt_sweep_schedule["debt_revolver_commitment", col.prev]',
        pf_expr='sources_uses["revolver_commitment", "active_case"]',
    )
    add_d(
        "debt_revolver_undrawn",
        "Revolver - Undrawn balance",
        'debt_sweep_schedule["debt_revolver_commitment", @col] - debt_sweep_schedule["debt_revolver_end", @col]',
        pf_expr='debt_sweep_schedule["debt_revolver_commitment", "pf_close"] - debt_sweep_schedule["debt_revolver_end", "pf_close"]',
    )
    add_d(
        "debt_revolver_interest_drawn",
        "Revolver - Interest on drawn balance",
        'debt_sweep_schedule["debt_rate_revolver", @col] * debt_sweep_schedule["debt_revolver_beg", @col] * income_statement["is_fractional_years", @col]',
    )
    add_d(
        "debt_revolver_commitment_fee",
        "Revolver - Undrawn commitment fee",
        'debt_sweep_schedule["revolver_undrawn_fee_rate", "pf_close"] * debt_sweep_schedule["debt_revolver_undrawn", col.prev] * income_statement["is_fractional_years", @col]',
    )
    add_d(
        "debt_revolver_total_interest",
        "Revolver - Total interest expense",
        'debt_sweep_schedule["debt_revolver_interest_drawn", @col] + debt_sweep_schedule["debt_revolver_commitment_fee", @col]',
        style="subtotal",
    )

    for tk in NON_REVOLVER_TRANCHE_KEYS:
        table.add_row_gutter()
        table.add_section_header(TRANCHE_SECTION_TITLES[tk])
        is_leg = tk == "legacy_debt"
        lbl = TRANCHE_ROW_LABELS[tk]
        terms = fin.get_tranche(tk)
        has_oid = not is_leg and terms.oid_rate != 0

        # Face value roll-forward
        add_d(
            f"debt_{tk}_face_beg",
            f"{lbl} - Face value - Beginning balance",
            f'debt_sweep_schedule["debt_{tk}_face_end", col.prev]',
            is_legacy=is_leg,
        )
        pik_expr = (
            "0"
            if is_leg
            else f'debt_sweep_schedule["debt_{tk}_book_interest", @col] * debt_sweep_schedule["debt_pik_pct_{tk}", @col]'
        )
        add_d(
            f"debt_{tk}_face_pik",
            f"{lbl} - Face value - PIK accretion",
            pik_expr,
            is_legacy=is_leg,
        )
        mand_expr = (
            f'-MIN(debt_sweep_schedule["debt_{tk}_face_beg", @col], '
            f'debt_sweep_schedule["debt_sched_amort_{tk}", @col] * debt_sweep_schedule["debt_{tk}_face_end", "pf_close"])'
        )
        add_d(
            f"debt_{tk}_face_mandatory",
            f"{lbl} - Face value - Mandatory repayment",
            mand_expr,
            is_legacy=is_leg,
            pre_roll_expr="0" if is_leg else None,
        )
        add_d(
            f"debt_{tk}_face_optional",
            f"{lbl} - Face value - Optional repayment",
            f'debt_sweep_schedule["sweep_opt_{tk}", @col]',
            is_legacy=is_leg,
            pre_roll_expr="0" if is_leg else None,
        )
        pf_face_expr = (
            'transaction_bs["existing_lt_debt", "pf_close"]'
            if is_leg
            else f'sources_uses["{tk}", "active_case"]'
        )
        add_d(
            f"debt_{tk}_face_end",
            f"{lbl} - Face value - Ending balance",
            f'SUM(debt_sweep_schedule["debt_{tk}_face_beg".."debt_{tk}_face_optional", @col])',
            pf_expr=pf_face_expr,
            style="subtotal",
            is_legacy=is_leg,
            mrq_expr='balance_sheet["bs_existing_lt_debt", "mrq"]' if is_leg else None,
        )

        # Book value roll-forward
        add_d(
            f"debt_{tk}_book_beg",
            f"{lbl} - Book value - Beginning balance",
            f'debt_sweep_schedule["debt_{tk}_book_end", col.prev]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_oid_amort",
            f"{lbl} - Book value - Amortization of OID",
            f'-debt_sweep_schedule["debt_{tk}_oid_amort", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_pik",
            f"{lbl} - Book value - PIK accretion",
            f'debt_sweep_schedule["debt_{tk}_face_pik", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_mandatory",
            f"{lbl} - Book value - Mandatory repayment",
            f'debt_sweep_schedule["debt_{tk}_face_mandatory", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_optional",
            f"{lbl} - Book value - Optional repayment",
            f'debt_sweep_schedule["debt_{tk}_face_optional", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_oid_loss",
            f"{lbl} - Book value - Loss on unamortized OID",
            f'-debt_sweep_schedule["debt_{tk}_oid_loss", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_end",
            f"{lbl} - Book value - Ending balance",
            f'SUM(debt_sweep_schedule["debt_{tk}_book_beg".."debt_{tk}_book_oid_loss", @col])',
            pf_expr=f'debt_sweep_schedule["debt_{tk}_face_end", "pf_close"] - debt_sweep_schedule["debt_{tk}_oid_end", "pf_close"]',
            style="subtotal",
            is_legacy=is_leg,
            mrq_expr=(
                f'debt_sweep_schedule["debt_{tk}_face_end", "mrq"] - debt_sweep_schedule["debt_{tk}_oid_end", "mrq"]'
                if is_leg
                else None
            ),
        )

        # OID balance roll-forward
        add_d(
            f"debt_{tk}_oid_beg",
            f"{lbl} - OID - Beginning balance",
            f'debt_sweep_schedule["debt_{tk}_oid_end", col.prev]',
            is_legacy=is_leg,
        )
        oid_amort_expr = (
            f'IFERROR(-MIN((debt_sweep_schedule["debt_{tk}_oid_beg", @col] / debt_sweep_schedule["debt_oid_rem_life_{tk}", col.prev]) * income_statement["is_fractional_years", @col], debt_sweep_schedule["debt_{tk}_oid_beg", @col]), 0)'
            if has_oid
            else "0"
        )
        add_d(
            f"debt_{tk}_oid_amort",
            f"{lbl} - OID - Amortization of OID",
            oid_amort_expr,
            is_legacy=is_leg,
        )
        oid_loss_expr = (
            f'IFERROR((debt_sweep_schedule["debt_{tk}_oid_beg", @col] + debt_sweep_schedule["debt_{tk}_oid_amort", @col]) * '
            f'(debt_sweep_schedule["debt_{tk}_face_mandatory", @col] + debt_sweep_schedule["debt_{tk}_face_optional", @col]) / '
            f'debt_sweep_schedule["debt_{tk}_face_beg", @col], 0)'
            if has_oid
            else "0"
        )
        add_d(
            f"debt_{tk}_oid_loss",
            f"{lbl} - OID - Loss on unamortized OID",
            oid_loss_expr,
            is_legacy=is_leg,
        )
        pf_oid_expr = "0" if is_leg else f'tranche_fees_oid["{tk}", "oid_amount"]'
        add_d(
            f"debt_{tk}_oid_end",
            f"{lbl} - OID - Ending balance",
            f'SUM(debt_sweep_schedule["debt_{tk}_oid_beg".."debt_{tk}_oid_loss", @col])',
            pf_expr=pf_oid_expr,
            style="subtotal",
            is_legacy=is_leg,
            mrq_expr="0" if is_leg else None,
        )

        # Interest & dividend expenses
        cash_int_expr = (
            f'debt_sweep_schedule["debt_rate_{tk}", @col] * '
            f'debt_sweep_schedule["debt_{tk}_face_beg", @col] * '
            'income_statement["is_fractional_years", @col]'
        )
        add_d(
            f"debt_{tk}_cash_interest",
            f"{lbl} - Actual interest expense / preferred dividend",
            cash_int_expr,
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_interest_oid_amort",
            f"{lbl} - Interest - Amortization of OID",
            f'-debt_sweep_schedule["debt_{tk}_oid_amort", @col]',
            is_legacy=is_leg,
        )
        add_d(
            f"debt_{tk}_book_interest",
            f"{lbl} - Book interest expense / preferred dividend",
            f'debt_sweep_schedule["debt_{tk}_cash_interest", @col] + debt_sweep_schedule["debt_{tk}_interest_oid_amort", @col]',
            style="subtotal",
            is_legacy=is_leg,
        )

    table.add_row_gutter()
    table.add_section_header("Aggregate Original Issue Discount (OID) Summary")
    tot_oid_amort = " + ".join(
        f'debt_sweep_schedule["debt_{tk}_book_oid_amort", @col]' for tk in NON_REVOLVER_TRANCHE_KEYS
    )
    tot_oid_loss = " + ".join(
        f'debt_sweep_schedule["debt_{tk}_book_oid_loss", @col]' for tk in NON_REVOLVER_TRANCHE_KEYS
    )
    add_d("debt_total_oid_amort", "Total amortization of OID", tot_oid_amort, style="total")
    add_d(
        "debt_total_oid_loss",
        "Total loss on unamortized OID at repayment",
        tot_oid_loss,
        style="total",
    )


def build_debt_sweep_schedule(sheet: f8.Sheet, assumptions: LboAssumptions) -> f8.Table:
    """Build the `debt_sweep_schedule` cash sweep waterfall and 12-tranche debt/preferred roll-forward."""
    sub = "Units: $ in millions"
    table = sheet.add_table(
        "debt_sweep_schedule",
        "Debt Amortization, Cash Sweep Waterfall & Tranche Roll-Forwards",
        subtitle=sub,
        currency="USD",
    )
    add_timeline_columns(table, "Debt & Cash Sweep Line Item")
    _add_driver_rows(table, assumptions)
    _add_sweep_waterfall_rows(table, assumptions)
    _add_tranche_rollforward_rows(table, assumptions)
    return table
