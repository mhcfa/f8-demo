"""Centralized financing scenario matrices and tranche terms for Institutional LBO Reference (Case C)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from models.lbo.assumptions.deal import CASE_KEYS, meta

TrancheKey = Literal[
    "legacy_debt",
    "revolver",
    "term_loan_a",
    "term_loan_b",
    "senior_note",
    "subordinated_note",
    "mezzanine",
    "seller_note",
    "convertible_bond",
    "debt_8",
    "preferred_a",
    "preferred_b",
]

NEW_FINANCING_TRANCHE_KEYS: tuple[str, ...] = (
    "revolver",
    "term_loan_a",
    "term_loan_b",
    "senior_note",
    "subordinated_note",
    "mezzanine",
    "seller_note",
    "convertible_bond",
    "debt_8",
    "preferred_a",
    "preferred_b",
)

NewFinancingTrancheKey = Literal[
    "revolver",
    "term_loan_a",
    "term_loan_b",
    "senior_note",
    "subordinated_note",
    "mezzanine",
    "seller_note",
    "convertible_bond",
    "debt_8",
    "preferred_a",
    "preferred_b",
]

TRANCHE_KEYS: tuple[str, ...] = (
    "legacy_debt",
    *NEW_FINANCING_TRANCHE_KEYS,
)


def _case_floats(
    c1: float, c2: float, c3: float, c4: float, c5: float, c6: float
) -> Callable[[], Mapping[str, float]]:
    return lambda: MappingProxyType(dict(zip(CASE_KEYS, (c1, c2, c3, c4, c5, c6), strict=True)))


def _case_ints(
    c1: int, c2: int, c3: int, c4: int, c5: int, c6: int
) -> Callable[[], Mapping[str, int]]:
    return lambda: MappingProxyType(dict(zip(CASE_KEYS, (c1, c2, c3, c4, c5, c6), strict=True)))


@dataclass(frozen=True)
class TrancheTerms:
    """Contractual pricing, fee, OID, and amortization terms for a capital structure tranche."""

    is_senior: int = field(
        metadata=meta(
            rationale="Binary indicator (1=Senior, 0=Subordinated/Preferred) for senior leverage ratio calculation.",
            basis="1 = senior debt tranche, 0 = subordinated or preferred",
            category="tranche_terms",
        ),
    )
    is_preferred: int = field(
        metadata=meta(
            rationale="Binary indicator (1=Preferred stock, 0=Debt) governing fee netting vs capitalization.",
            basis="1 = preferred equity security (fee netted against APIC), 0 = debt security (fee capitalized)",
            category="tranche_terms",
        ),
    )
    financing_fee_rate: float = field(
        metadata=meta(
            rationale="Upfront underwriting/arrangement fee percentage applied to commitment (revolver) or draw.",
            basis="Percentage of commitment (revolver) or gross principal drawn",
            category="tranche_terms",
        ),
    )
    fee_amort_years: float = field(
        metadata=meta(
            rationale="Straight-line amortization period (years) for capitalized debt issuance costs.",
            basis="Contractual maturity / fee amortization period in years",
            category="tranche_terms",
        ),
    )
    fixed_coupon_rate: float = field(
        metadata=meta(
            rationale="Fixed annual coupon or preferred dividend rate (0.0 for floating-rate tranches).",
            basis="Annual fixed interest / dividend rate",
            category="tranche_terms",
        ),
    )
    libor_spread: float = field(
        metadata=meta(
            rationale="Annual interest rate spread over 3-month LIBOR for floating-rate debt tranches.",
            basis="Spread over 3-month LIBOR (0.0 for fixed-rate tranches)",
            category="tranche_terms",
        ),
    )
    oid_rate: float = field(
        metadata=meta(
            rationale="Original issue discount (OID) percentage withheld from gross proceeds at issuance.",
            basis="Percentage of gross principal / liquidation preference at issuance",
            category="tranche_terms",
        ),
    )
    oid_amort_years: float = field(
        metadata=meta(
            rationale="Straight-line amortization period (years) for original issue discount.",
            basis="OID amortization horizon in years",
            category="tranche_terms",
        ),
    )
    periodic_amort_rate: float = field(
        default=0.0,
        metadata=meta(
            rationale="Mandatory annual principal amortization percentage of initial face value.",
            basis="Annual mandatory amortization rate (% of initial principal)",
            category="tranche_terms",
        ),
    )
    term_years: float = field(
        default=0.0,
        metadata=meta(
            rationale="Contractual maturity term in years from transaction close.",
            basis="Contractual tenor in years",
            category="tranche_terms",
        ),
    )
    cash_sweep_enabled: int = field(
        default=0,
        metadata=meta(
            rationale="Binary flag indicating whether excess cash flow sweep applies to this tranche.",
            basis="1 = participates in mandatory excess cash sweep, 0 = no cash sweep",
            category="tranche_terms",
        ),
    )
    conversion_price: float = field(
        default=0.0,
        metadata=meta(
            rationale="Per-share conversion price for convertible debt instruments ($26.77/sh for legacy debt).",
            basis="Conversion strike price ($/share)",
            category="tranche_terms",
        ),
    )
    pik_pct_schedule: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Period-by-period share of book interest/dividend paid-in-kind (PIK) across the 10 post-close periods.",
            basis="PIK percentage of book interest / preferred dividend (FY13..FY22)",
            category="tranche_terms",
        ),
    )
    equity_kicker_pct: float = field(
        default=0.0,
        metadata=meta(
            rationale="Partial-dilution equity kicker share allocated to the tranche (2.00% Subordinated Note, 0.25% Preferred Stock A).",
            basis="Percentage of partially diluted post-close equity allocated to tranche warrants/kicker",
            category="tranche_terms",
        ),
    )
    prepayment_premium_schedule: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Period-by-period early repayment call premium rate across the 10 post-close projection periods.",
            basis="Prepayment call premium percentage of principal repaid at exit (FY13..FY22)",
            category="tranche_terms",
        ),
    )
    draws_by_case: Mapping[str, float] = field(
        default_factory=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Gross principal / liquidation preference drawn across financing Cases 1-6 ($M).",
            basis="Gross principal drawn at transaction close by financing case ($M)",
            category="financing_scenarios",
        ),
    )


def _tranche_factory(
    is_senior: int,
    is_preferred: int,
    fee_rate: float,
    fee_amort: float,
    fixed_rate: float,
    spread: float,
    oid_rate: float,
    oid_amort: float,
    amort_rate: float = 0.0,
    term: float = 0.0,
    sweep: int = 0,
    conv_price: float = 0.0,
    pik_schedule: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    equity_kicker: float = 0.0,
    prepay_schedule: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    draws_by_case: Mapping[str, float] | None = None,
) -> Callable[[], TrancheTerms]:
    return lambda: TrancheTerms(
        is_senior=is_senior,
        is_preferred=is_preferred,
        financing_fee_rate=fee_rate,
        fee_amort_years=fee_amort,
        fixed_coupon_rate=fixed_rate,
        libor_spread=spread,
        oid_rate=oid_rate,
        oid_amort_years=oid_amort,
        periodic_amort_rate=amort_rate,
        term_years=term,
        cash_sweep_enabled=sweep,
        conversion_price=conv_price,
        pik_pct_schedule=pik_schedule,
        equity_kicker_pct=equity_kicker,
        prepayment_premium_schedule=prepay_schedule,
        draws_by_case=draws_by_case
        if draws_by_case is not None
        else _case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
    )


@dataclass(frozen=True)
class FinancingAssumptions:
    """Financing scenario draw schedules and contractual tranche terms across Cases 1-6."""

    case_numbers_by_case: Mapping[str, int] = field(
        default_factory=_case_ints(1, 2, 3, 4, 5, 6),
        metadata=meta(
            rationale="Sequential scenario numbers (1..6) for the six financing cases.",
            basis="Integer index 1..6",
            category="financing_scenarios",
        ),
    )
    lbo_flag_by_case: Mapping[str, int] = field(
        default_factory=_case_ints(0, 0, 0, 1, 1, 1),
        metadata=meta(
            rationale="Binary indicator distinguishing standalone/refinancing cases (Cases 1-3 = 0) from LBO cases (Cases 4-6 = 1).",
            basis="1 = LBO buyout transaction, 0 = standalone / debt refinancing",
            category="financing_scenarios",
        ),
    )
    revolver_commitment_by_case: Mapping[str, float] = field(
        default_factory=_case_floats(0.0, 100.0, 100.0, 100.0, 100.0, 100.0),
        metadata=meta(
            rationale="Bank revolving credit facility commitment ($0.0M in Case 1; $100.0M in Cases 2-6).",
            basis="Committed revolving credit line ($M)",
            category="financing_scenarios",
        ),
    )
    management_equity_by_case: Mapping[str, float] = field(
        default_factory=_case_floats(0.0, 0.0, 0.0, 10.0, 10.0, 10.0),
        metadata=meta(
            rationale="Management rollover / co-investment equity contribution ($10.0M across LBO Cases 4-6; $0.0M in Cases 1-3).",
            basis="Management equity contribution ($M)",
            category="financing_scenarios",
        ),
    )
    legacy_debt: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.0,
            0.0,
            0.1425,
            0.0,
            0.0,
            4.0,
            0.0,
            5.0,
            0,
            26.77,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Existing $230.0M 14.25% fixed-rate convertible long-term debt ($26.77/sh conversion strike).",
            basis="14.25% fixed coupon, $26.77/sh conversion strike",
            category="tranche_terms",
        ),
    )
    revolver: TrancheTerms = field(
        default_factory=_tranche_factory(
            1,
            0,
            0.0175,
            5.0,
            0.0,
            0.0425,
            0.0,
            0.0,
            0.0,
            0.0,
            1,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Senior secured revolving credit facility (L+4.25%, 1.75% upfront fee on commitment, 5-yr amort).",
            basis="Senior secured revolver terms",
            category="tranche_terms",
        ),
    )
    term_loan_a: TrancheTerms = field(
        default_factory=_tranche_factory(
            1,
            0,
            0.02,
            5.0,
            0.0,
            0.0479,
            0.0,
            4.0,
            0.20,
            5.0,
            1,
            draws_by_case=_case_floats(0.0, 125.0, 75.0, 150.0, 0.0, 50.0)(),
        ),
        metadata=meta(
            rationale="Senior secured Term Loan A (L+4.79%, 2.00% fee, 5-yr fee amort, 20% annual principal amort, cash sweep).",
            basis="Senior secured Term Loan A terms",
            category="tranche_terms",
        ),
    )
    term_loan_b: TrancheTerms = field(
        default_factory=_tranche_factory(
            1,
            0,
            0.02,
            5.0,
            0.0,
            0.06,
            0.0,
            4.0,
            0.05,
            6.0,
            1,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 75.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Senior secured Term Loan B (L+6.00%, 2.00% fee, 5-yr fee amort, 5% annual principal amort, cash sweep).",
            basis="Senior secured Term Loan B terms",
            category="tranche_terms",
        ),
    )
    senior_note: TrancheTerms = field(
        default_factory=_tranche_factory(
            1,
            0,
            0.0225,
            7.0,
            0.0,
            0.065,
            0.05,
            4.0,
            0.0,
            8.0,
            0,
            draws_by_case=_case_floats(0.0, 50.0, 100.0, 75.0, 100.0, 100.0)(),
        ),
        metadata=meta(
            rationale="Senior Note (L+6.50% floating, 2.25% fee, 7-yr fee amort, 5.00% OID over 4 yrs, 8-yr bullet).",
            basis="Senior Note terms",
            category="tranche_terms",
        ),
    )
    subordinated_note: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.03,
            7.0,
            0.1025,
            0.0,
            0.05,
            4.0,
            0.0,
            6.0,
            0,
            equity_kicker=0.02,
            prepay_schedule=(0.05, 0.03, 0.02, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 50.0)(),
        ),
        metadata=meta(
            rationale="Subordinated Note (10.25% fixed cash coupon, 0% PIK, 3.00% fee over 7 yrs, 5.00% OID over 4 yrs, 6-yr term).",
            basis="Subordinated Note terms",
            category="tranche_terms",
        ),
    )
    mezzanine: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.03,
            7.0,
            0.105,
            0.0,
            0.05,
            4.0,
            0.0,
            1.0,
            0,
            prepay_schedule=(0.02, 0.02, 0.02, 0.02, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0),
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Mezzanine debt (10.50% fixed coupon, 3.00% fee over 7 yrs, 5.00% OID over 4 yrs).",
            basis="Mezzanine debt terms",
            category="tranche_terms",
        ),
    )
    seller_note: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.03,
            7.0,
            0.105,
            0.0,
            0.05,
            4.0,
            0.0,
            3.0,
            0,
            0.0,
            (1.0, 1.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Seller note (10.50% fixed coupon, 3.00% fee over 7 yrs, 5.00% OID over 4 yrs).",
            basis="Seller note terms",
            category="tranche_terms",
        ),
    )
    convertible_bond: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.03,
            7.0,
            0.11,
            0.0,
            0.0,
            4.0,
            0.0,
            3.0,
            0,
            0.0,
            (1.0, 1.0, 1.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Convertible bond (11.00% fixed coupon, 3.00% fee over 7 yrs, 0.00% OID).",
            basis="Convertible bond terms",
            category="tranche_terms",
        ),
    )
    debt_8: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            0,
            0.03,
            7.0,
            0.0,
            0.0,
            0.0,
            4.0,
            0.0,
            3.0,
            0,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Placeholder Debt 8 tranche (0.00% coupon, 3.00% fee over 7 yrs, 0.00% OID).",
            basis="Placeholder Debt 8 terms",
            category="tranche_terms",
        ),
    )
    preferred_a: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            1,
            0.03,
            0.0,
            0.12,
            0.0,
            0.05,
            4.0,
            0.0,
            0.0,
            0,
            0.0,
            (1.0, 1.0, 1.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            equity_kicker=0.0025,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 10.0, 75.0, 10.0)(),
        ),
        metadata=meta(
            rationale="Preferred Stock A (12.00% PIK dividend, 3.00% fee netted against APIC, 5.00% OID amortized over 4 yrs).",
            basis="Preferred Stock A terms",
            category="tranche_terms",
        ),
    )
    preferred_b: TrancheTerms = field(
        default_factory=_tranche_factory(
            0,
            1,
            0.03,
            0.0,
            0.125,
            0.0,
            0.0,
            4.0,
            draws_by_case=_case_floats(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)(),
        ),
        metadata=meta(
            rationale="Preferred Stock B (12.50% dividend, 3.00% fee netted against APIC, 0.00% OID).",
            basis="Preferred Stock B terms",
            category="tranche_terms",
        ),
    )
    libor_curve: tuple[float, ...] = field(
        default=(
            0.0278,
            0.0321555,
            0.03739725,
            0.041604,
            0.04573675,
            0.048315,
            0.0498055,
            0.0511235,
            0.05222525,
            0.0531,
        ),
        metadata=meta(
            rationale="Forward 3-month LIBOR curve across the 10 post-close projection periods (2.78% rising to 5.31%).",
            basis="Annualized 3-month LIBOR forward rate by period (FY13..FY22)",
            category="interest_rates",
        ),
    )
    cash_interest_rate: float = field(
        default=0.01,
        metadata=meta(
            rationale="Annual interest yield earned on beginning cash and equivalents balances (1.00%).",
            basis="Annual interest rate on cash balances",
            category="interest_rates",
        ),
    )
    revolver_undrawn_commitment_fee_rate: float = field(
        default=0.005,
        metadata=meta(
            rationale="Annual commitment fee charged on undrawn revolving credit facility capacity (0.50%).",
            basis="Annual percentage fee on beginning undrawn revolver balance",
            category="interest_rates",
        ),
    )
    average_interest_flag: int = field(
        default=0,
        metadata=meta(
            rationale="Interest calculation basis selector (0 = beginning debt balance, 1 = average debt balance).",
            basis="0 = beginning balance (acyclic), 1 = average balance",
            category="interest_rates",
        ),
    )

    def get_tranche(self, tranche_key: str) -> TrancheTerms:
        """Retrieve TrancheTerms by canonical tranche key."""
        if tranche_key not in TRANCHE_KEYS:
            msg = f"Unknown tranche key: {tranche_key}"
            raise KeyError(msg)
        res: TrancheTerms = getattr(self, tranche_key)
        return res

    def get_draws_by_case(self, tranche_key: str) -> Mapping[str, float]:
        """Retrieve case-by-case draw mapping for a capital structure tranche."""
        return self.get_tranche(tranche_key).draws_by_case
