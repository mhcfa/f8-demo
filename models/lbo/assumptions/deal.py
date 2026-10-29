"""Centralized deal, purchase price allocation, and tax assumptions for Institutional LBO Reference (Case C)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Literal

CaseKey = Literal[
    "case_1_no_deal",
    "case_2_refi_a",
    "case_3_refi_b",
    "case_4_lbo_a",
    "case_5_lbo_b",
    "case_6_lbo_c",
]

CASE_KEYS: tuple[str, ...] = (
    "case_1_no_deal",
    "case_2_refi_a",
    "case_3_refi_b",
    "case_4_lbo_a",
    "case_5_lbo_b",
    "case_6_lbo_c",
)


def meta(
    rationale: str,
    basis: str,
    category: str = "general",
    **extra: Any,
) -> dict[str, Any]:
    """Build structured driver metadata dictionary for dataclass fields."""
    return {
        "rationale": rationale,
        "basis": basis,
        "category": category,
        **extra,
    }


def get_driver_metadata_records(
    container: object,
    prefix: str = "",
) -> list[dict[str, Any]]:
    """Extract flat list of driver metadata records for documentation and tables."""
    if not is_dataclass(container) or isinstance(container, type):
        msg = f"Expected dataclass instance, got {type(container).__name__}"
        raise TypeError(msg)

    records: list[dict[str, Any]] = []
    for f in fields(container):
        val = getattr(container, f.name)
        qualified_name = f"{prefix}{f.name}" if prefix else f.name
        if is_dataclass(val) and not isinstance(val, type):
            records.extend(get_driver_metadata_records(val, prefix=f"{qualified_name}."))
        else:
            records.append(
                {
                    "name": qualified_name,
                    "value": val,
                    "type": str(f.type),
                    "rationale": f.metadata.get("rationale", ""),
                    "basis": f.metadata.get("basis", ""),
                    "category": f.metadata.get("category", "general"),
                }
            )
    return records


def _default_legal_fees() -> Mapping[str, float]:
    return MappingProxyType(
        {
            "case_1_no_deal": 0.0,
            "case_2_refi_a": 2.5,
            "case_3_refi_b": 2.5,
            "case_4_lbo_a": 3.0,
            "case_5_lbo_b": 3.0,
            "case_6_lbo_c": 3.0,
        }
    )


def _default_accounting_fees() -> Mapping[str, float]:
    return MappingProxyType(
        {
            "case_1_no_deal": 0.0,
            "case_2_refi_a": 2.0,
            "case_3_refi_b": 2.0,
            "case_4_lbo_a": 2.5,
            "case_5_lbo_b": 2.5,
            "case_6_lbo_c": 2.5,
        }
    )


def _default_printing_fees() -> Mapping[str, float]:
    return MappingProxyType(
        {
            "case_1_no_deal": 0.0,
            "case_2_refi_a": 1.0,
            "case_3_refi_b": 1.0,
            "case_4_lbo_a": 1.0,
            "case_5_lbo_b": 1.0,
            "case_6_lbo_c": 1.0,
        }
    )


def _default_other_fees() -> Mapping[str, float]:
    return MappingProxyType(
        {
            "case_1_no_deal": 0.0,
            "case_2_refi_a": 1.0,
            "case_3_refi_b": 1.0,
            "case_4_lbo_a": 2.0,
            "case_5_lbo_b": 2.0,
            "case_6_lbo_c": 2.0,
        }
    )


def _default_legacy_debt_refinanced_flags() -> Mapping[str, int]:
    return MappingProxyType(
        {
            "case_1_no_deal": 0,
            "case_2_refi_a": 1,
            "case_3_refi_b": 1,
            "case_4_lbo_a": 1,
            "case_5_lbo_b": 1,
            "case_6_lbo_c": 1,
        }
    )


@dataclass(frozen=True)
class DealAssumptions:
    """Transaction structure, fee, PPA, and tax drivers for the Institutional LBO Reference (Case C) model."""

    active_financing_case: int = field(
        default=6,
        metadata=meta(
            rationale="Active financing scenario selector (Case 6 = LBO C with TLA, Senior, Sub, and Pref A).",
            basis="Scenario selector (1=No deal, 2=Refi A, 3=Refi B, 4=LBO A, 5=LBO B, 6=LBO C)",
            category="scenario",
        ),
    )
    active_operating_case: int = field(
        default=3,
        metadata=meta(
            rationale="Active operating scenario selector (Case 3 = Analyst Case consensus forecast).",
            basis="Scenario selector (1=Flat, 2=Management, 3=Analyst, 4=Downside)",
            category="scenario",
        ),
    )
    close_quarter: str = field(
        default="mrq_plus_3",
        metadata=meta(
            rationale="Transaction close after 3 quarters of pre-close standalone operations (2012-12-31).",
            basis="3 quarters from MRQ (2012-03-31) to transaction close (2012-12-31)",
            category="scenario",
        ),
    )
    minimum_cash_balance: float = field(
        default=100.0,
        metadata=meta(
            rationale="Minimum operating cash retained on balance sheet at transaction close; excess cash swept to sources.",
            basis="$100.0M minimum cash threshold",
            category="cash_policy",
        ),
    )
    advisory_fee_rate: float = field(
        default=0.01,
        metadata=meta(
            rationale="M&A advisory fee calculated as 1.00% of equity purchase price in LBO scenarios.",
            basis="1.00% of equity purchase price",
            category="transaction_fees",
        ),
    )
    sponsor_fee_rate: float = field(
        default=0.0065,
        metadata=meta(
            rationale="Private equity sponsor deal fee calculated as 0.65% of equity purchase price in LBO scenarios.",
            basis="0.65% of equity purchase price",
            category="transaction_fees",
        ),
    )
    legacy_debt_prepayment_penalty_rate: float = field(
        default=0.02,
        metadata=meta(
            rationale="Call premium / prepayment penalty on refinanced legacy long-term debt ($230.0M * 2.00% = $4.6M).",
            basis="2.00% of legacy debt face value refinanced",
            category="transaction_fees",
        ),
    )
    legal_fee_by_case: Mapping[str, float] = field(
        default_factory=_default_legal_fees,
        metadata=meta(
            rationale="Fixed legal transaction fees ($2.5M in refinancing cases; $3.0M in LBO cases).",
            basis="Case-specific legal fee schedule ($M)",
            category="transaction_fees",
        ),
    )
    accounting_fee_by_case: Mapping[str, float] = field(
        default_factory=_default_accounting_fees,
        metadata=meta(
            rationale="Fixed accounting and diligence fees ($2.0M in refinancing cases; $2.5M in LBO cases).",
            basis="Case-specific accounting fee schedule ($M)",
            category="transaction_fees",
        ),
    )
    printing_fee_by_case: Mapping[str, float] = field(
        default_factory=_default_printing_fees,
        metadata=meta(
            rationale="Fixed financial printing and filing costs ($1.0M across all active financing cases).",
            basis="Case-specific printing fee schedule ($M)",
            category="transaction_fees",
        ),
    )
    other_fee_by_case: Mapping[str, float] = field(
        default_factory=_default_other_fees,
        metadata=meta(
            rationale="Other transaction advisory and closing expenses ($1.0M in refinancing cases; $2.0M in LBO cases).",
            basis="Case-specific other fee schedule ($M)",
            category="transaction_fees",
        ),
    )
    legacy_debt_refinanced_by_case: Mapping[str, int] = field(
        default_factory=_default_legacy_debt_refinanced_flags,
        metadata=meta(
            rationale="Binary trigger indicating whether existing $230.0M LT debt is retired at transaction close.",
            basis="1 = refinance existing debt at close, 0 = leave existing debt in place",
            category="transaction_structure",
        ),
    )
    excess_purchase_price_to_intangibles_pct: float = field(
        default=0.25,
        metadata=meta(
            rationale="25.0% of excess purchase price over book equity is allocated to finite-lived identifiable intangibles.",
            basis="25.0% allocation of excess purchase price",
            category="ppa",
        ),
    )
    existing_intangibles_purch_acct_pct: float = field(
        default=0.0,
        metadata=meta(
            rationale="Share of existing identifiable intangibles written off in purchase accounting (0.0%).",
            basis="0.0% write-off of existing identifiable intangibles",
            category="ppa",
        ),
    )
    ppe_fair_value_mark: float = field(
        default=15.0,
        metadata=meta(
            rationale="Pre-tax fair value step-up to gross PP&E at transaction close ($15.0M).",
            basis="Appraised fair value write-up on gross PP&E ($M)",
            category="ppa",
        ),
    )
    ppe_writeup_depr_period_years: float = field(
        default=7.0,
        metadata=meta(
            rationale="Useful life over which the $15.0M PP&E fair value step-up is depreciated post-close.",
            basis="7.0-year straight-line depreciation period",
            category="ppa",
        ),
    )
    intangibles_writeup_amort_period_years: float = field(
        default=5.0,
        metadata=meta(
            rationale="Useful life over which identifiable intangible fair value write-up ($109.455M) is amortized.",
            basis="5.0-year straight-line amortization period",
            category="ppa",
        ),
    )
    statutory_tax_rate: float = field(
        default=0.35,
        metadata=meta(
            rationale="35.0% statutory corporate tax rate applied to transaction tax shields, DTL creation, and deal charges.",
            basis="Statutory marginal corporate tax rate (35.0%)",
            category="tax",
        ),
    )
    federal_tax_rate: float = field(
        default=0.3299,
        metadata=meta(
            rationale="32.99% federal corporate income tax rate on pre-tax income after state tax deduction.",
            basis="Federal statutory rate (32.99%) deductible against state taxes",
            category="tax",
        ),
    )
    state_local_tax_rate: float = field(
        default=0.03,
        metadata=meta(
            rationale="3.00% blended state and local corporate income tax rate.",
            basis="State and local statutory rate (3.00%)",
            category="tax",
        ),
    )
    amt_tax_rate: float = field(
        default=0.20,
        metadata=meta(
            rationale="20.0% Alternative Minimum Tax (AMT) rate on AMT taxable income.",
            basis="Corporate AMT rate (20.0%)",
            category="tax",
        ),
    )
    amt_max_offset: float = field(
        default=0.90,
        metadata=meta(
            rationale="90.0% maximum NOL offset cap under Alternative Minimum Tax rules.",
            basis="Statutory AMT NOL utilization limit (90.0%)",
            category="tax",
        ),
    )
    irs_section_382_rate: float = field(
        default=0.0283,
        metadata=meta(
            rationale="2.83% IRS Section 382 long-term tax-exempt rate governing annual pre-change NOL utilization limit.",
            basis="IRS Section 382 applicable federal long-term tax-exempt rate",
            category="tax",
        ),
    )
    nol_remaining_life_years: float = field(
        default=15.0,
        metadata=meta(
            rationale="15.0-year remaining carryforward expiration window for net operating losses.",
            basis="Statutory NOL carryforward period (years)",
            category="tax",
        ),
    )
    existing_nol: float = field(
        default=0.0,
        metadata=meta(
            rationale="Pre-transaction net operating loss carryforward balance at close ($0.0M).",
            basis="Opening NOL balance ($M)",
            category="tax",
        ),
    )
    amt_credit_carryforward: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening AMT credit carryforward balance at close ($0.0M).",
            basis="Opening AMT credit balance ($M)",
            category="tax",
        ),
    )
    exit_valuation_method: int = field(
        default=1,
        metadata=meta(
            rationale="Active exit valuation methodology selector (1 = EBITDA multiple, 2 = GAAP P/E, 3 = Cash P/E).",
            basis="Integer selector 1..3 (default 1 = EBITDA multiple method)",
            category="exit_valuation",
        ),
    )
    exit_year: int = field(
        default=4,
        metadata=meta(
            rationale="Active exit period index across the 10 post-close periods (4 = Year 4 ending 2026-09-30).",
            basis="Post-close period index 1..10 (1 = stub_3q, 4 = fy_4, 10 = fy_10)",
            category="exit_valuation",
        ),
    )
    exit_ebitda_multiple: float = field(
        default=5.0,
        metadata=meta(
            rationale="Forward enterprise value / annualized EBITDA multiple applied across post-close exit horizons (5.0x).",
            basis="Forward EV/EBITDA exit multiple (x)",
            category="exit_valuation",
        ),
    )
    exit_pe_multiple: float = field(
        default=14.0,
        metadata=meta(
            rationale="Forward price / annualized earnings multiple applied to GAAP and Cash P/E exit valuation methods (14.0x).",
            basis="Forward P/E exit multiple (x)",
            category="exit_valuation",
        ),
    )
    mgmt_performance_equity_pct: float = field(
        default=0.005,
        metadata=meta(
            rationale="Management performance equity allocation diluting common and tranche kicker ownership on a full-dilution basis (0.50%).",
            basis="Percentage of fully diluted exit equity allocated to management incentive pool",
            category="equity_dilution",
        ),
    )
    pre_tx_levered_beta: float = field(
        default=0.86,
        metadata=meta(
            rationale="Pre-transaction observed levered equity beta used to unlever and relever target beta in WACC analysis (0.86).",
            basis="Observed historical levered equity beta prior to transaction close",
            category="wacc_dcf",
        ),
    )
    risk_free_rate: float = field(
        default=0.045,
        metadata=meta(
            rationale="Risk-free interest rate benchmark used in CAPM cost of equity calculation (4.50%).",
            basis="Long-term US Treasury constant-maturity yield benchmark (4.50%)",
            category="wacc_dcf",
        ),
    )
    market_risk_premium: float = field(
        default=0.04,
        metadata=meta(
            rationale="Expected equity market risk premium over the risk-free rate in CAPM cost of equity (4.00%).",
            basis="Equity market risk premium (4.00%)",
            category="wacc_dcf",
        ),
    )
    manual_wacc: float = field(
        default=0.12,
        metadata=meta(
            rationale="Manual weighted average cost of capital input for standalone DCF valuation and sensitivity center (12.00%).",
            basis="User-specified discount rate when wacc_selector = 1 (12.00%)",
            category="wacc_dcf",
        ),
    )
    wacc_selector: int = field(
        default=1,
        metadata=meta(
            rationale="Active WACC method selector for DCF valuation (1 = manual WACC 12.00%, 2 = CAPM/capital-structure calculated WACC 7.77%).",
            basis="Integer selector 1..2 (1 = manual_wacc, 2 = calculated WACC)",
            category="wacc_dcf",
        ),
    )
    dcf_wacc_step: float = field(
        default=0.01,
        metadata=meta(
            rationale="Discount rate step increment (+/- 1.00%) around the active WACC in the 3x3 DCF sensitivity matrices.",
            basis="100 bps (1.00%) WACC sensitivity step",
            category="wacc_dcf",
        ),
    )
    dcf_terminal_ebitda_multiples: tuple[float, ...] = field(
        default=(4.5, 5.0, 5.5),
        metadata=meta(
            rationale="Three terminal FY2017 EV/EBITDA exit multiples evaluated across the EBITDA Multiple Method DCF sensitivity table (4.5x, 5.0x, 5.5x).",
            basis="3-column terminal EV/EBITDA multiple vector (x)",
            category="wacc_dcf",
        ),
    )
    dcf_terminal_growth_rates: tuple[float, ...] = field(
        default=(0.0, 0.005, 0.01),
        metadata=meta(
            rationale="Three perpetuity UFCF growth rates evaluated across the Perpetuity Growth Method DCF sensitivity table (0.00%, 0.50%, 1.00%).",
            basis="3-column terminal perpetuity growth rate vector",
            category="wacc_dcf",
        ),
    )
    balance_check_tolerance: float = field(
        default=0.001,
        metadata=meta(
            rationale="Absolute dollar tolerance ($0.001M) for Executive Dashboard Sources & Uses and Balance Sheet integrity checks.",
            basis="Maximum absolute balance sheet / sources-uses discrepancy ($M)",
            category="model_checks",
        ),
    )

    @property
    def combined_effective_tax_rate(self) -> float:
        """Combined federal and state effective tax rate: state + fed * (1 - state)."""
        return self.state_local_tax_rate + self.federal_tax_rate * (1.0 - self.state_local_tax_rate)
