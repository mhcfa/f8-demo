"""Declarative worksheet and table layout configuration for the Institutional LBO Reference (Case C) model.

This module decouples the visual presentation, worksheet arrangement, and table ordering
from the underlying financial calculation schedules and assumptions.

Analysts can modify table ordering, split tables across new worksheets, or adjust
relative placement (`right_of`, `below`, `gap`) directly in Python without touching
underlying financial statements or formula logic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TablePlacement:
    """Positioning specification for a table on a worksheet.

    Attributes:
        id: Unique table identifier matching a registered table builder.
        right_of: Optional ID of an earlier table on the same sheet to place this table immediately to the right of.
        below: Optional ID of an earlier table on the same sheet to place this table below.
        gap: Physical gutter count (rows if stacked/below, columns if right_of). Defaults to 2 for stack and 1 for right_of.
    """

    id: str
    right_of: str | None = None
    below: str | None = None
    gap: int | None = None


@dataclass(frozen=True)
class SheetLayout:
    """Worksheet configuration and table sequence.

    Attributes:
        name: Worksheet tab title.
        tables: Ordered sequence of tables to place on this worksheet. Can be specified as either
            a string table ID (which uses default vertical stacking) or a `TablePlacement` object.
        tab_color: Optional hex color string without '#' (e.g. '1F497D').
        show_gridlines: Whether Excel gridlines are enabled (defaults to True).
        freeze_panes: Optional (row, col) split coordinates for panes.
    """

    name: str
    tables: Sequence[TablePlacement | str] = ()
    tab_color: str | None = None
    show_gridlines: bool = True
    freeze_panes: tuple[int, int] | None = None


@dataclass(frozen=True)
class ModelLayout:
    """Complete workbook layout specification.

    Attributes:
        sheets: Ordered sequence of worksheet layouts.
    """

    sheets: Sequence[SheetLayout] = ()


TableId = Literal[
    # Executive Dashboard
    "dashboard_sources_uses",
    "dashboard_entry_valuation",
    "dashboard_implied_multiples",
    "dashboard_returns_summary",
    "dashboard_credit_profile",
    "dashboard_integrity_checks",
    # Transaction & PPA
    "option_tranches",
    "valuation_fdso",
    "sources_uses",
    "tranche_fees_oid",
    "ppa_schedule",
    "transaction_bs",
    # LBO Model (Continuous Timeline)
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "working_capital_schedule",
    "debt_sweep_schedule",
    "da_schedule",
    "nol_amt_schedule",
    "convertible_fdso_schedule",
    "credit_stats",
    "operating_schedule",
    # Valuation & Returns
    "dcf_schedule",
    "exit_valuation",
    "returns_waterfall",
    "equity_dilution",
    "pre_deal_capm_schedule",
    "wacc_schedule",
    "dcf_sensitivity",
]

# All 29 canonical table identifiers available in the LBO model:
AVAILABLE_TABLE_IDS: tuple[str, ...] = (
    # Executive Dashboard
    "dashboard_sources_uses",
    "dashboard_entry_valuation",
    "dashboard_implied_multiples",
    "dashboard_returns_summary",
    "dashboard_credit_profile",
    "dashboard_integrity_checks",
    # Transaction & PPA
    "option_tranches",
    "valuation_fdso",
    "sources_uses",
    "tranche_fees_oid",
    "ppa_schedule",
    "transaction_bs",
    # LBO Model (Continuous Timeline)
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "working_capital_schedule",
    "debt_sweep_schedule",
    "da_schedule",
    "nol_amt_schedule",
    "convertible_fdso_schedule",
    "credit_stats",
    "operating_schedule",
    # Valuation & Returns
    "dcf_schedule",
    "exit_valuation",
    "returns_waterfall",
    "equity_dilution",
    "pre_deal_capm_schedule",
    "wacc_schedule",
    "dcf_sensitivity",
)


DEFAULT_LBO_LAYOUT = ModelLayout(
    sheets=[
        SheetLayout(
            name="Executive Dashboard",
            tables=[
                TablePlacement("dashboard_sources_uses"),
                TablePlacement(
                    "dashboard_entry_valuation",
                    right_of="dashboard_sources_uses",
                ),
                TablePlacement(
                    "dashboard_implied_multiples",
                    right_of="dashboard_entry_valuation",
                    gap=1,
                ),
                TablePlacement(
                    "dashboard_returns_summary",
                    below="dashboard_entry_valuation",
                    gap=1,
                ),
                TablePlacement(
                    "dashboard_credit_profile",
                    below="dashboard_sources_uses",
                    gap=1,
                ),
                TablePlacement(
                    "dashboard_integrity_checks",
                    below="dashboard_implied_multiples",
                    gap=1,
                ),
            ],
        ),
        SheetLayout(
            name="Transaction & PPA",
            tables=[
                "option_tranches",
                "valuation_fdso",
                "sources_uses",
                "tranche_fees_oid",
                "ppa_schedule",
                "transaction_bs",
            ],
        ),
        SheetLayout(
            name="LBO Model",
            tables=[
                "income_statement",
                "balance_sheet",
                "cash_flow_statement",
                "working_capital_schedule",
                "debt_sweep_schedule",
                "da_schedule",
                "nol_amt_schedule",
                "convertible_fdso_schedule",
                "credit_stats",
                "operating_schedule",
            ],
        ),
        SheetLayout(
            name="Valuation & Returns",
            tables=[
                "dcf_schedule",
                "exit_valuation",
                "returns_waterfall",
                "equity_dilution",
                "pre_deal_capm_schedule",
                "wacc_schedule",
                "dcf_sensitivity",
            ],
        ),
    ]
)

__all__ = [
    "AVAILABLE_TABLE_IDS",
    "DEFAULT_LBO_LAYOUT",
    "ModelLayout",
    "SheetLayout",
    "TableId",
    "TablePlacement",
]
