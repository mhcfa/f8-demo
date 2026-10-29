import json

import f8
import pytest

import models
from models.lbo import (
    AVAILABLE_TABLE_IDS,
    DEFAULT_LBO_LAYOUT,
    DEFAULT_THEME_PATH,
    ModelLayout,
    SheetLayout,
    TablePlacement,
    build_lbo_transaction_model,
)


def test_f8_package_installed() -> None:
    assert f8 is not None


def test_models_importable() -> None:
    assert models is not None


def test_lbo_model_loads_workspace_theme_json() -> None:
    assert DEFAULT_THEME_PATH.is_file()
    theme_spec = json.loads(DEFAULT_THEME_PATH.read_text(encoding="utf-8"))
    model = build_lbo_transaction_model()
    assert model.theme == theme_spec
    assert isinstance(model.theme, dict)


def test_default_lbo_layout_contains_all_twenty_nine_tables() -> None:
    all_table_ids: list[str] = []
    for sheet in DEFAULT_LBO_LAYOUT.sheets:
        for t in sheet.tables:
            tid = t if isinstance(t, str) else t.id
            all_table_ids.append(tid)

    assert len(all_table_ids) == 29
    assert len(set(all_table_ids)) == 29
    assert set(all_table_ids) == set(AVAILABLE_TABLE_IDS)


def test_custom_layout_reordering_and_new_sheet() -> None:
    custom_layout = ModelLayout(
        sheets=[
            SheetLayout(
                name="Executive Dashboard",
                tables=[
                    TablePlacement("dashboard_sources_uses"),
                    TablePlacement("dashboard_entry_valuation", right_of="dashboard_sources_uses"),
                    TablePlacement(
                        "dashboard_implied_multiples", below="dashboard_entry_valuation", gap=1
                    ),
                    TablePlacement(
                        "dashboard_returns_summary", right_of="dashboard_entry_valuation", gap=2
                    ),
                    TablePlacement(
                        "dashboard_credit_profile", below="dashboard_returns_summary", gap=1
                    ),
                    TablePlacement(
                        "dashboard_integrity_checks", below="dashboard_credit_profile", gap=1
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
                name="Core Statements",
                tables=[
                    "balance_sheet",  # Balance sheet before income statement
                    "income_statement",
                    "cash_flow_statement",
                ],
            ),
            SheetLayout(
                name="Operations & Debt",
                tables=[
                    "operating_schedule",
                    "working_capital_schedule",
                    "debt_sweep_schedule",
                    "da_schedule",
                    "nol_amt_schedule",
                    "convertible_fdso_schedule",
                    "credit_stats",
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
    model = build_lbo_transaction_model(layout=custom_layout)
    assert len(model.sheets) == 5
    assert [s.name for s in model.sheets] == [
        "Executive Dashboard",
        "Transaction & PPA",
        "Core Statements",
        "Operations & Debt",
        "Valuation & Returns",
    ]
    compiled = model.compile()
    assert compiled is not None


def test_layout_unknown_table_id_raises_value_error() -> None:
    bad_layout = ModelLayout(
        sheets=[
            SheetLayout(
                name="Bad Sheet",
                tables=["non_existent_table_id"],
            )
        ]
    )
    with pytest.raises(ValueError, match="Unknown table ID 'non_existent_table_id'"):
        build_lbo_transaction_model(layout=bad_layout)


def test_layout_duplicate_table_id_raises_value_error() -> None:
    dup_layout = ModelLayout(
        sheets=[
            SheetLayout(name="Sheet1", tables=["income_statement"]),
            SheetLayout(name="Sheet2", tables=["income_statement"]),
        ]
    )
    with pytest.raises(ValueError, match="Duplicate table ID 'income_statement'"):
        build_lbo_transaction_model(layout=dup_layout)
