"""Single source of truth (SSOT) domain registries for capital structure tranches and balance sheet accounts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import f8

    from models.lbo.assumptions.financing import TrancheKey


@dataclass(frozen=True)
class TrancheSpec:
    """Canonical specification for a capital structure tranche across all model schedules."""

    key: TrancheKey
    name: str
    section_title: str
    is_senior: bool
    is_preferred: bool
    is_new_financing: bool
    bs_row_id: str
    tx_row_id: str


TRANCHE_SPECS: tuple[TrancheSpec, ...] = (
    TrancheSpec(
        key="legacy_debt",
        name="Legacy debt",
        section_title="Legacy Debt",
        is_senior=False,
        is_preferred=False,
        is_new_financing=False,
        bs_row_id="bs_existing_lt_debt",
        tx_row_id="existing_lt_debt",
    ),
    TrancheSpec(
        key="revolver",
        name="Revolver",
        section_title="Revolving Credit Facility",
        is_senior=True,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_revolver",
        tx_row_id="revolver",
    ),
    TrancheSpec(
        key="term_loan_a",
        name="Term loan - A",
        section_title="Term Loan - A",
        is_senior=True,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_term_loan_a",
        tx_row_id="term_loan_a",
    ),
    TrancheSpec(
        key="term_loan_b",
        name="Term loan - B",
        section_title="Term Loan - B",
        is_senior=True,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_term_loan_b",
        tx_row_id="term_loan_b",
    ),
    TrancheSpec(
        key="senior_note",
        name="Senior note",
        section_title="Senior Note",
        is_senior=True,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_senior_note",
        tx_row_id="senior_note",
    ),
    TrancheSpec(
        key="subordinated_note",
        name="Subordinated note",
        section_title="Subordinated Note",
        is_senior=False,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_subordinated_note",
        tx_row_id="subordinated_note",
    ),
    TrancheSpec(
        key="mezzanine",
        name="Mezzanine",
        section_title="Mezzanine",
        is_senior=False,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_mezzanine",
        tx_row_id="mezzanine",
    ),
    TrancheSpec(
        key="seller_note",
        name="Seller note",
        section_title="Seller Note",
        is_senior=False,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_seller_note",
        tx_row_id="seller_note",
    ),
    TrancheSpec(
        key="convertible_bond",
        name="Convertible bond",
        section_title="Convertible Bond",
        is_senior=False,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_convertible_bond",
        tx_row_id="convertible_bond",
    ),
    TrancheSpec(
        key="debt_8",
        name="[Debt 8]",
        section_title="[Debt 8]",
        is_senior=False,
        is_preferred=False,
        is_new_financing=True,
        bs_row_id="bs_debt_8",
        tx_row_id="debt_8",
    ),
    TrancheSpec(
        key="preferred_a",
        name="Preferred stock - A",
        section_title="Preferred Stock - A",
        is_senior=False,
        is_preferred=True,
        is_new_financing=True,
        bs_row_id="bs_preferred_a",
        tx_row_id="preferred_a",
    ),
    TrancheSpec(
        key="preferred_b",
        name="Preferred stock - B",
        section_title="Preferred Stock - B",
        is_senior=False,
        is_preferred=True,
        is_new_financing=True,
        bs_row_id="bs_preferred_b",
        tx_row_id="preferred_b",
    ),
)

TRANCHE_SPEC_MAP: dict[str, TrancheSpec] = {s.key: s for s in TRANCHE_SPECS}
NEW_FINANCING_TRANCHE_SPECS: tuple[TrancheSpec, ...] = tuple(
    s for s in TRANCHE_SPECS if s.is_new_financing
)
NON_REVOLVER_TRANCHE_SPECS: tuple[TrancheSpec, ...] = tuple(
    s for s in TRANCHE_SPECS if s.key != "revolver"
)
SCHED_SWEEP_TRANCHE_SPECS: tuple[TrancheSpec, ...] = tuple(
    s for s in TRANCHE_SPECS if s.is_new_financing and s.key != "revolver"
)


def get_tranche_spec(key: str) -> TrancheSpec:
    """Retrieve TrancheSpec by canonical tranche key."""
    if key not in TRANCHE_SPEC_MAP:
        msg = f"Unknown tranche key: {key}"
        raise KeyError(msg)
    return TRANCHE_SPEC_MAP[key]


@dataclass(frozen=True)
class BalanceSheetAccountSpec:
    """Canonical specification for a balance sheet row across continuous timeline and transaction bridge."""

    bs_row_id: str
    tx_row_id: str
    label: str
    timeline_expr: str
    style: f8.SemanticStyle | None = None
    is_vertical_calc: bool = False
    tx_vertical_expr: str | None = None

    @property
    def pf_close_expr(self) -> str | None:
        """Expression linking pro forma close in balance_sheet to transaction_bs."""
        if self.is_vertical_calc:
            return None
        return f'transaction_bs["{self.tx_row_id}", "pf_close"]'

    @property
    def tx_pre_deal_expr(self) -> str | None:
        """Expression linking pre-deal close in transaction_bs to standalone close in balance_sheet."""
        if self.is_vertical_calc:
            return None
        return f'balance_sheet["{self.bs_row_id}", "standalone_close"]'


BALANCE_SHEET_ACCOUNTS: tuple[BalanceSheetAccountSpec, ...] = (
    BalanceSheetAccountSpec(
        bs_row_id="bs_cash",
        tx_row_id="cash",
        label="Cash & equivalents",
        timeline_expr='balance_sheet["bs_cash", col.prev] + cash_flow_statement["cf_change_in_cash", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_accounts_receivable",
        tx_row_id="accounts_receivable",
        label="Accounts receivable",
        timeline_expr='working_capital_schedule["wc_accounts_receivable", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_inventories",
        tx_row_id="inventories",
        label="Inventories",
        timeline_expr='working_capital_schedule["wc_inventories", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_dta_current",
        tx_row_id="dta_current",
        label="Deferred tax asset, current",
        timeline_expr='working_capital_schedule["wc_dta_current", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_prepaid_expenses",
        tx_row_id="prepaid_expenses",
        label="Prepaid expenses & other",
        timeline_expr='working_capital_schedule["wc_prepaid_expenses", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_current_assets",
        tx_row_id="total_current_assets",
        label="Total current assets",
        timeline_expr='SUM(balance_sheet["bs_cash".."bs_prepaid_expenses", @col])',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='SUM(transaction_bs["cash".."prepaid_expenses", @col])',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_ppe_gross",
        tx_row_id="ppe_gross",
        label="PP&E, gross",
        timeline_expr='balance_sheet["bs_ppe_gross", col.prev] + income_statement["is_capex", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_accumulated_depreciation",
        tx_row_id="accumulated_depreciation",
        label="Accumulated depreciation",
        timeline_expr='balance_sheet["bs_accumulated_depreciation", col.prev] - income_statement["is_depreciation", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_ppe_net",
        tx_row_id="ppe_net",
        label="PP&E, net",
        timeline_expr='balance_sheet["bs_ppe_gross", @col] + balance_sheet["bs_accumulated_depreciation", @col]',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["ppe_gross", @col] + transaction_bs["accumulated_depreciation", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_equity_investments",
        tx_row_id="equity_investments",
        label="Equity investments",
        timeline_expr='balance_sheet["bs_equity_investments", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_capitalized_financing_costs",
        tx_row_id="capitalized_financing_costs",
        label="Capitalized financing costs",
        timeline_expr='balance_sheet["bs_capitalized_financing_costs", col.prev] - income_statement["is_amort_deferred_financing", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_goodwill",
        tx_row_id="goodwill",
        label="Goodwill, net",
        timeline_expr='balance_sheet["bs_goodwill", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_intangibles_net",
        tx_row_id="intangibles_net",
        label="Intangible assets, net",
        timeline_expr='balance_sheet["bs_intangibles_net", col.prev] - income_statement["is_amortization", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_operating_rights",
        tx_row_id="operating_rights",
        label="Operating rights, net",
        timeline_expr='balance_sheet["bs_operating_rights", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_other_lt_assets",
        tx_row_id="other_lt_assets",
        label="Other long-term assets",
        timeline_expr='balance_sheet["bs_other_lt_assets", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_assets",
        tx_row_id="total_assets",
        label="Total assets",
        timeline_expr='balance_sheet["bs_total_current_assets", @col] + balance_sheet["bs_ppe_net", @col] + SUM(balance_sheet["bs_equity_investments".."bs_other_lt_assets", @col])',
        style="total",
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["total_current_assets", @col] + transaction_bs["ppe_net", @col] + SUM(transaction_bs["equity_investments".."other_lt_assets", @col])',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_short_term_debt",
        tx_row_id="short_term_debt",
        label="Short-term debt",
        timeline_expr='balance_sheet["bs_short_term_debt", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_accounts_payable",
        tx_row_id="accounts_payable",
        label="Accounts payable",
        timeline_expr='working_capital_schedule["wc_accounts_payable", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_accrued_liabilities",
        tx_row_id="accrued_liabilities",
        label="Accrued liabilities",
        timeline_expr='working_capital_schedule["wc_accrued_liabilities", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_client_deposits",
        tx_row_id="client_deposits",
        label="Client deposits",
        timeline_expr='working_capital_schedule["wc_client_deposits", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_other_current_liabilities",
        tx_row_id="other_current_liabilities",
        label="Other current liabilities",
        timeline_expr='working_capital_schedule["wc_other_current_liabilities", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_current_liabilities",
        tx_row_id="total_current_liabilities",
        label="Total current liabilities",
        timeline_expr='SUM(balance_sheet["bs_short_term_debt".."bs_other_current_liabilities", @col])',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='SUM(transaction_bs["short_term_debt".."other_current_liabilities", @col])',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_capital_leases",
        tx_row_id="capital_leases",
        label="Capital leases",
        timeline_expr='balance_sheet["bs_capital_leases", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_existing_lt_debt",
        tx_row_id="existing_lt_debt",
        label="Existing LT debt (excl. current portion)",
        timeline_expr='debt_sweep_schedule["debt_legacy_debt_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_revolver",
        tx_row_id="revolver",
        label="Revolver",
        timeline_expr='debt_sweep_schedule["debt_revolver_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_term_loan_a",
        tx_row_id="term_loan_a",
        label="Term loan - A",
        timeline_expr='debt_sweep_schedule["debt_term_loan_a_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_term_loan_b",
        tx_row_id="term_loan_b",
        label="Term loan - B",
        timeline_expr='debt_sweep_schedule["debt_term_loan_b_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_senior_note",
        tx_row_id="senior_note",
        label="Senior note",
        timeline_expr='debt_sweep_schedule["debt_senior_note_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_subordinated_note",
        tx_row_id="subordinated_note",
        label="Subordinated note",
        timeline_expr='debt_sweep_schedule["debt_subordinated_note_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_mezzanine",
        tx_row_id="mezzanine",
        label="Mezzanine",
        timeline_expr='debt_sweep_schedule["debt_mezzanine_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_seller_note",
        tx_row_id="seller_note",
        label="Seller note",
        timeline_expr='debt_sweep_schedule["debt_seller_note_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_convertible_bond",
        tx_row_id="convertible_bond",
        label="Convertible bond",
        timeline_expr='debt_sweep_schedule["debt_convertible_bond_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_debt_8",
        tx_row_id="debt_8",
        label="[Debt 8]",
        timeline_expr='debt_sweep_schedule["debt_debt_8_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_debt",
        tx_row_id="total_debt",
        label="Total debt",
        timeline_expr='balance_sheet["bs_short_term_debt", @col] + SUM(balance_sheet["bs_capital_leases".."bs_debt_8", @col])',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["short_term_debt", @col] + SUM(transaction_bs["capital_leases".."debt_8", @col])',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_net_dtl",
        tx_row_id="net_dtl",
        label="Net deferred tax liability / (asset)",
        timeline_expr='nol_amt_schedule["tax_net_dtl_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_other_lt_liabilities",
        tx_row_id="other_lt_liabilities",
        label="Other long-term liabilities",
        timeline_expr='balance_sheet["bs_other_lt_liabilities", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_liabilities",
        tx_row_id="total_liabilities",
        label="Total liabilities",
        timeline_expr='balance_sheet["bs_total_current_liabilities", @col] + SUM(balance_sheet["bs_capital_leases".."bs_debt_8", @col]) + balance_sheet["bs_net_dtl", @col] + balance_sheet["bs_other_lt_liabilities", @col]',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["total_current_liabilities", @col] + SUM(transaction_bs["capital_leases".."debt_8", @col]) + transaction_bs["net_dtl", @col] + transaction_bs["other_lt_liabilities", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_noncontrolling_interest",
        tx_row_id="noncontrolling_interest",
        label="Noncontrolling (minority) interest",
        timeline_expr='balance_sheet["bs_noncontrolling_interest", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_preferred_a",
        tx_row_id="preferred_a",
        label="Preferred Stock - A",
        timeline_expr='debt_sweep_schedule["debt_preferred_a_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_preferred_b",
        tx_row_id="preferred_b",
        label="Preferred Stock - B",
        timeline_expr='debt_sweep_schedule["debt_preferred_b_book_end", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_common_stock_par",
        tx_row_id="common_stock",
        label="Common stock, par value",
        timeline_expr='balance_sheet["bs_common_stock_par", col.prev]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_apic",
        tx_row_id="apic",
        label="Additional paid-in capital (APIC)",
        timeline_expr='balance_sheet["bs_apic", col.prev] + income_statement["is_sbc", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_retained_earnings",
        tx_row_id="retained_earnings",
        label="Retained earnings",
        timeline_expr='balance_sheet["bs_retained_earnings", col.prev] + income_statement["is_gaap_net_income_common", @col] + cash_flow_statement["cf_common_dividend", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_equity",
        tx_row_id="total_equity",
        label="Total shareholders' equity",
        timeline_expr='SUM(balance_sheet["bs_preferred_a".."bs_retained_earnings", @col])',
        style="subtotal",
        is_vertical_calc=True,
        tx_vertical_expr='SUM(transaction_bs["preferred_a".."retained_earnings", @col])',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_total_liabilities_and_equity",
        tx_row_id="total_liabilities_and_equity",
        label="Liabilities & shareholders' equity",
        timeline_expr='balance_sheet["bs_total_liabilities", @col] + balance_sheet["bs_noncontrolling_interest", @col] + balance_sheet["bs_total_equity", @col]',
        style="total",
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["total_liabilities", @col] + transaction_bs["noncontrolling_interest", @col] + transaction_bs["total_equity", @col]',
    ),
    BalanceSheetAccountSpec(
        bs_row_id="bs_balance_check",
        tx_row_id="bs_check",
        label="Balance sheet check",
        timeline_expr='balance_sheet["bs_total_assets", @col] - balance_sheet["bs_total_liabilities_and_equity", @col]',
        style=None,
        is_vertical_calc=True,
        tx_vertical_expr='transaction_bs["total_assets", @col] - transaction_bs["total_liabilities_and_equity", @col]',
    ),
)

BALANCE_SHEET_ACCOUNT_MAP: dict[str, BalanceSheetAccountSpec] = {
    s.bs_row_id: s for s in BALANCE_SHEET_ACCOUNTS
}
TX_BALANCE_SHEET_ACCOUNT_MAP: dict[str, BalanceSheetAccountSpec] = {
    s.tx_row_id: s for s in BALANCE_SHEET_ACCOUNTS
}


def get_bs_account(bs_row_id: str) -> BalanceSheetAccountSpec:
    """Retrieve BalanceSheetAccountSpec by balance_sheet row ID."""
    if bs_row_id not in BALANCE_SHEET_ACCOUNT_MAP:
        msg = f"Unknown balance sheet account row ID: {bs_row_id}"
        raise KeyError(msg)
    return BALANCE_SHEET_ACCOUNT_MAP[bs_row_id]


def get_tx_bs_account(tx_row_id: str) -> BalanceSheetAccountSpec:
    """Retrieve BalanceSheetAccountSpec by transaction_bs row ID."""
    if tx_row_id not in TX_BALANCE_SHEET_ACCOUNT_MAP:
        msg = f"Unknown transaction balance sheet row ID: {tx_row_id}"
        raise KeyError(msg)
    return TX_BALANCE_SHEET_ACCOUNT_MAP[tx_row_id]


__all__ = [
    "BALANCE_SHEET_ACCOUNTS",
    "BALANCE_SHEET_ACCOUNT_MAP",
    "NEW_FINANCING_TRANCHE_SPECS",
    "NON_REVOLVER_TRANCHE_SPECS",
    "SCHED_SWEEP_TRANCHE_SPECS",
    "TRANCHE_SPECS",
    "TRANCHE_SPEC_MAP",
    "TX_BALANCE_SHEET_ACCOUNT_MAP",
    "BalanceSheetAccountSpec",
    "TrancheSpec",
    "get_bs_account",
    "get_tranche_spec",
    "get_tx_bs_account",
]
