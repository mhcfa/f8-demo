"""Pre-deal capitalization, option tranches, and diluted share count builders (`option_tranches`, `valuation_and_fdso`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import f8

if TYPE_CHECKING:
    from models.lbo.assumptions import LboAssumptions


OPTION_TRANCHE_ROWS: tuple[str, ...] = (
    "tranche_1",
    "tranche_2",
    "tranche_3",
    "tranche_4",
    "tranche_5",
    "tranche_6",
    "tranche_7",
    "tranche_8",
    "tranche_9",
    "tranche_10",
)

OPTION_TRANCHE_LABELS: tuple[str, ...] = (
    "Tranche 1",
    "Tranche 2",
    "Tranche 3",
    "Tranche 4",
    "Tranche 5",
    "Tranche 6",
    "Tranche 7",
    "Tranche 8",
    "Tranche 9",
    "Tranche 10",
)

OPTION_INPUT_COLS: tuple[str, ...] = (
    "options_outstanding",
    "outstanding_strike",
    "options_exercisable",
    "exercisable_strike",
)

VALUATION_INPUT_ROWS: tuple[tuple[str, str, f8.FormatPreset, int], ...] = (
    ("current_share_price", "Current share price", "currency", 2),
    ("offer_premium", "Offer premium", "percentage", 1),
    ("basic_shares_outstanding", "Basic shares outstanding", "number", 3),
    ("legacy_convertible_face_value", "Legacy convertible debt face value", "currency", 1),
    ("legacy_conversion_price", "Legacy convertible debt conversion price", "currency", 2),
)


def build_option_tranches(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `option_tranches` f8.Table from centralized baseline assumptions."""
    base = assumptions.baseline

    table = sheet.add_table(
        "option_tranches",
        "Stock Option Tranches Schedule",
        subtitle="Units: Shares and $ in millions, except per-share figures",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Tranche")
    table.add_column(
        "options_outstanding",
        group="Option Liquidation Method",
        headers=["Options", "Outst. (M)"],
        format="number",
        decimals=3,
    )
    table.add_column(
        "outstanding_strike",
        group="Option Liquidation Method",
        headers=["Exercise", "Price ($)"],
        format="currency",
        decimals=2,
    )
    table.add_column(
        "itm_options",
        group="Option Liquidation Method",
        headers=["ITM", "Options (M)"],
        format="number",
        decimals=3,
    )
    table.add_column(
        "liquidation_proceeds",
        group="Option Liquidation Method",
        headers=["Liquidation", "Proceeds"],
        format="currency",
        decimals=3,
    )
    table.add_column(
        "options_exercisable",
        group="Treasury Stock Method",
        headers=["Options", "Exerc. (M)"],
        format="number",
        decimals=3,
    )
    table.add_column(
        "exercisable_strike",
        group="Treasury Stock Method",
        headers=["Exercisable", "Strike ($)"],
        format="currency",
        decimals=2,
    )
    table.add_column(
        "treasury_method_shares",
        group="Treasury Stock Method",
        headers=["Treasury", "Shares (M)"],
        format="number",
        decimals=3,
    )

    for row_id, row_label, tranche in zip(
        OPTION_TRANCHE_ROWS, OPTION_TRANCHE_LABELS, base.option_tranches, strict=True
    ):
        cells: dict[str, f8.CellInputValue] = {"label": row_label}
        for col_id in OPTION_INPUT_COLS:
            val: float = getattr(tranche, col_id)
            cells[col_id] = val
        table.add_row(row_id, cells=cells, style="data")

    table.set_cells(
        slice("tranche_1", "tranche_10"),
        "itm_options",
        expr=(
            'IF(option_tranches[@row, "outstanding_strike"] < '
            'valuation_and_fdso["offer_price_per_share", "value"], '
            'option_tranches[@row, "options_outstanding"], 0)'
        ),
        style="data",
        format="number",
        decimals=3,
    )
    table.set_cells(
        slice("tranche_1", "tranche_10"),
        "liquidation_proceeds",
        expr='option_tranches[@row, "itm_options"] * option_tranches[@row, "outstanding_strike"]',
        style="data",
        format="currency",
        decimals=3,
    )
    table.set_cells(
        slice("tranche_1", "tranche_10"),
        "treasury_method_shares",
        expr=(
            'IF(option_tranches[@row, "exercisable_strike"] < '
            'valuation_and_fdso["current_share_price", "value"], '
            'option_tranches[@row, "options_exercisable"] - '
            '(option_tranches[@row, "options_exercisable"] * '
            'option_tranches[@row, "exercisable_strike"]) / '
            'valuation_and_fdso["current_share_price", "value"], 0)'
        ),
        style="data",
        format="number",
        decimals=3,
    )

    table.add_row(
        "options_total",
        cells={
            "label": "Total Options",
            "options_outstanding": None,
            "outstanding_strike": None,
            "options_exercisable": None,
            "exercisable_strike": None,
        },
        style="total",
    )
    table.set_cells(
        "options_total",
        ("itm_options", "treasury_method_shares"),
        expr='SUM(option_tranches["tranche_1".."tranche_10", @col])',
        style="total",
        format="number",
        decimals=3,
    )
    table.set_cell(
        "options_total",
        "liquidation_proceeds",
        expr='SUM(option_tranches["tranche_1".."tranche_10", @col])',
        style="total",
        format="currency",
        decimals=3,
    )

    return table


def build_valuation_fdso(
    sheet: f8.Sheet,
    assumptions: LboAssumptions,
) -> f8.Table:
    """Build the `valuation_and_fdso` f8.Table from centralized baseline assumptions."""
    base = assumptions.baseline

    table = sheet.add_table(
        "valuation_and_fdso",
        "Offer Price & Fully Diluted Shares Schedule",
        subtitle="Units: Shares and $ in millions, except per-share figures",
        currency="USD",
    )
    table.add_column("label", role="descriptor", header="Valuation & Share Metric")
    table.add_column(
        "value",
        headers=["Metric", "Value"],
        format="number",
        decimals=3,
    )

    input_map: dict[str, tuple[str, f8.FormatPreset, int]] = {
        row_id: (label, fmt, dec) for row_id, label, fmt, dec in VALUATION_INPUT_ROWS
    }
    for row_id in ("current_share_price", "offer_premium"):
        label, fmt, dec = input_map[row_id]
        scalar_val: float = getattr(base, row_id)
        table.add_row(
            row_id,
            cells={
                "label": label,
                "value": f8.Cell(
                    value=scalar_val,
                    style="data",
                    format=fmt,
                    decimals=dec,
                ),
            },
            style="data",
        )

    table.add_row(
        "offer_price_per_share",
        cells={"label": "Offer price per share"},
        style="subtotal",
    )
    table.set_cell(
        "offer_price_per_share",
        "value",
        expr=(
            'valuation_and_fdso["current_share_price", "value"] * '
            '(1 + valuation_and_fdso["offer_premium", "value"])'
        ),
        style="subtotal",
        format="currency",
        decimals=2,
    )

    for row_id in (
        "basic_shares_outstanding",
        "legacy_convertible_face_value",
        "legacy_conversion_price",
    ):
        label, fmt, dec = input_map[row_id]
        scalar_val = getattr(base, row_id)
        table.add_row(
            row_id,
            cells={
                "label": label,
                "value": f8.Cell(
                    value=scalar_val,
                    style="data",
                    format=fmt,
                    decimals=dec,
                ),
            },
            style="data",
        )

    table.add_row(
        "legacy_convertible_shares",
        cells={"label": "Legacy convertible debt shares if converted"},
        style="data",
    )
    table.set_cell(
        "legacy_convertible_shares",
        "value",
        expr=(
            'valuation_and_fdso["legacy_convertible_face_value", "value"] / '
            'valuation_and_fdso["legacy_conversion_price", "value"]'
        ),
        style="data",
        format="number",
        decimals=3,
    )

    table.add_row(
        "fdso_liquidation",
        cells={"label": "Fully diluted shares outstanding (option liquidation method)"},
        style="total",
    )
    table.set_cell(
        "fdso_liquidation",
        "value",
        expr=(
            'valuation_and_fdso["basic_shares_outstanding", "value"] + '
            'option_tranches["options_total", "itm_options"] + '
            'IF(valuation_and_fdso["legacy_conversion_price", "value"] < '
            'valuation_and_fdso["offer_price_per_share", "value"], '
            'valuation_and_fdso["legacy_convertible_shares", "value"], 0)'
        ),
        style="total",
        format="number",
        decimals=3,
    )

    table.add_row(
        "fdso_treasury",
        cells={"label": "Fully diluted shares outstanding (treasury stock method)"},
        style="total",
    )
    table.set_cell(
        "fdso_treasury",
        "value",
        expr=(
            'valuation_and_fdso["basic_shares_outstanding", "value"] + '
            'option_tranches["options_total", "treasury_method_shares"] + '
            'IF(valuation_and_fdso["legacy_conversion_price", "value"] < '
            'valuation_and_fdso["current_share_price", "value"], '
            'valuation_and_fdso["legacy_convertible_shares", "value"], 0)'
        ),
        style="total",
        format="number",
        decimals=3,
    )

    return table
