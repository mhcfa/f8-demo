"""Top-level Institutional LBO Reference (Case C) Model assembler."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import f8

from models.lbo.assumptions import LboAssumptions
from models.lbo.cap_table import build_option_tranches, build_valuation_fdso
from models.lbo.credit_stats import build_credit_stats
from models.lbo.dashboard import (
    build_dashboard_credit_profile,
    build_dashboard_entry_valuation,
    build_dashboard_implied_multiples,
    build_dashboard_integrity_checks,
    build_dashboard_returns_summary,
    build_dashboard_sources_uses,
)
from models.lbo.dcf_wacc import (
    build_dcf_schedule,
    build_dcf_sensitivity,
    build_pre_deal_capm_schedule,
    build_wacc_schedule,
)
from models.lbo.debt_sweep import build_debt_sweep_schedule
from models.lbo.layout import (
    AVAILABLE_TABLE_IDS,
    DEFAULT_LBO_LAYOUT,
    ModelLayout,
    TablePlacement,
)
from models.lbo.operating_da import build_da_schedule, build_operating_schedule
from models.lbo.returns import (
    build_equity_dilution,
    build_exit_valuation,
    build_returns_waterfall,
)
from models.lbo.statements import (
    build_balance_sheet,
    build_cash_flow_statement,
    build_income_statement,
)
from models.lbo.tax_dilution import (
    build_convertible_fdso_schedule,
    build_nol_amt_schedule,
)
from models.lbo.transaction import (
    build_ppa_schedule,
    build_sources_uses,
    build_tranche_fees_oid,
    build_transaction_bs,
)
from models.lbo.working_capital import build_working_capital_schedule

DEFAULT_DELIVERABLE_PATH = Path("deliverables/lbo_model.xlsx")
DEFAULT_THEME_PATH = Path(__file__).resolve().parents[2] / "theme.json"

type _TableBuilder = Callable[[f8.Sheet, LboAssumptions], f8.Table]

TABLE_BUILDERS: dict[str, _TableBuilder] = {
    # 1. Executive Dashboard
    "dashboard_sources_uses": build_dashboard_sources_uses,
    "dashboard_entry_valuation": build_dashboard_entry_valuation,
    "dashboard_implied_multiples": build_dashboard_implied_multiples,
    "dashboard_returns_summary": build_dashboard_returns_summary,
    "dashboard_credit_profile": build_dashboard_credit_profile,
    "dashboard_integrity_checks": build_dashboard_integrity_checks,
    # 2. Transaction & PPA
    "option_tranches": build_option_tranches,
    "valuation_fdso": build_valuation_fdso,
    "sources_uses": build_sources_uses,
    "tranche_fees_oid": build_tranche_fees_oid,
    "ppa_schedule": build_ppa_schedule,
    "transaction_bs": build_transaction_bs,
    # 3. LBO Model
    "income_statement": build_income_statement,
    "balance_sheet": build_balance_sheet,
    "cash_flow_statement": build_cash_flow_statement,
    "working_capital_schedule": build_working_capital_schedule,
    "debt_sweep_schedule": build_debt_sweep_schedule,
    "da_schedule": build_da_schedule,
    "nol_amt_schedule": build_nol_amt_schedule,
    "convertible_fdso_schedule": build_convertible_fdso_schedule,
    "credit_stats": build_credit_stats,
    "operating_schedule": build_operating_schedule,
    # 4. Valuation & Returns
    "dcf_schedule": build_dcf_schedule,
    "exit_valuation": build_exit_valuation,
    "returns_waterfall": build_returns_waterfall,
    "equity_dilution": build_equity_dilution,
    "pre_deal_capm_schedule": build_pre_deal_capm_schedule,
    "wacc_schedule": build_wacc_schedule,
    "dcf_sensitivity": build_dcf_sensitivity,
}


def build_lbo_transaction_model(
    assumptions: LboAssumptions | None = None,
    layout: ModelLayout | None = None,
) -> f8.Model:
    """Assemble the Institutional LBO Reference (Case C) f8.Model according to the specified declarative layout.

    Args:
        assumptions: Baseline, deal, financing, and operating assumptions (defaults to `LboAssumptions()`).
        layout: Declarative workbook topology and table layout (defaults to `DEFAULT_LBO_LAYOUT`).

    Returns:
        Uncompiled `f8.Model` populated with worksheets and scheduled tables.
    """
    resolved_assumptions = assumptions if assumptions is not None else LboAssumptions()
    resolved_layout = layout if layout is not None else DEFAULT_LBO_LAYOUT

    model = f8.Model(name="Institutional LBO Model", theme=DEFAULT_THEME_PATH)

    seen_table_ids: set[str] = set()
    for sheet_spec in resolved_layout.sheets:
        sheet = model.add_sheet(
            name=sheet_spec.name,
            tab_color=sheet_spec.tab_color,
            show_gridlines=sheet_spec.show_gridlines,
            freeze_panes=sheet_spec.freeze_panes,
        )
        for item in sheet_spec.tables:
            placement = TablePlacement(id=item) if isinstance(item, str) else item
            table_id = placement.id

            if table_id not in TABLE_BUILDERS:
                msg = (
                    f"Unknown table ID '{table_id}' in sheet '{sheet_spec.name}'. "
                    f"Available table IDs: {list(AVAILABLE_TABLE_IDS)}"
                )
                raise ValueError(msg)

            if table_id in seen_table_ids:
                msg = f"Duplicate table ID '{table_id}' encountered across workbook layout."
                raise ValueError(msg)
            seen_table_ids.add(table_id)

            builder = TABLE_BUILDERS[table_id]
            table = builder(sheet, resolved_assumptions)

            # Ensure spatial placement is explicitly applied
            if placement.right_of is not None:
                table.right_of = placement.right_of
                table.below = None
            elif placement.below is not None:
                table.below = placement.below
                table.right_of = None
            if placement.gap is not None:
                table.gap = placement.gap

    return model


def compile_lbo_transaction_model(
    assumptions: LboAssumptions | None = None,
    layout: ModelLayout | None = None,
) -> f8.CompiledModel:
    """Build and compile the complete Institutional LBO Reference (Case C) f8.Model into a CompiledModel."""
    return build_lbo_transaction_model(assumptions=assumptions, layout=layout).compile()


def emit_lbo_workbook(
    output_path: str | Path = DEFAULT_DELIVERABLE_PATH,
    assumptions: LboAssumptions | None = None,
    layout: ModelLayout | None = None,
) -> Path:
    """Compile and save the Institutional LBO Reference (Case C) live-formula Excel (.xlsx) deliverable."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    compiled = compile_lbo_transaction_model(assumptions=assumptions, layout=layout)
    compiled.save(str(target))
    return target
