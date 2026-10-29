"""Centralized pre-deal capitalization, quarterly baseline, opening balance sheet, and consensus assumptions."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.lbo.assumptions.deal import meta


@dataclass(frozen=True)
class OptionTrancheTerms:
    """Pre-deal employee stock option tranche strike and share count parameters."""

    options_outstanding: float = field(
        metadata=meta(
            rationale="Total stock options outstanding in tranche (millions of shares) for buyout option liquidation.",
            basis="Options outstanding (M shares)",
            category="cap_table",
        ),
    )
    outstanding_strike: float = field(
        metadata=meta(
            rationale="Weighted-average exercise price ($/share) of total options outstanding in tranche.",
            basis="Exercise strike price ($/share)",
            category="cap_table",
        ),
    )
    options_exercisable: float = field(
        metadata=meta(
            rationale="Vested and currently exercisable stock options in tranche (millions of shares) for treasury stock method.",
            basis="Exercisable options (M shares)",
            category="cap_table",
        ),
    )
    exercisable_strike: float = field(
        metadata=meta(
            rationale="Weighted-average exercise price ($/share) of vested exercisable options in tranche.",
            basis="Exercisable strike price ($/share)",
            category="cap_table",
        ),
    )


DEFAULT_OPTION_TRANCHES: tuple[OptionTrancheTerms, ...] = (
    OptionTrancheTerms(
        options_outstanding=0.402,
        outstanding_strike=9.13,
        options_exercisable=0.209,
        exercisable_strike=9.04,
    ),
    OptionTrancheTerms(
        options_outstanding=0.12,
        outstanding_strike=9.93,
        options_exercisable=0.059,
        exercisable_strike=10.03,
    ),
    OptionTrancheTerms(
        options_outstanding=0.466,
        outstanding_strike=11.6,
        options_exercisable=0.221,
        exercisable_strike=11.53,
    ),
    OptionTrancheTerms(
        options_outstanding=0.3,
        outstanding_strike=12.64,
        options_exercisable=0.3,
        exercisable_strike=12.69,
    ),
    OptionTrancheTerms(
        options_outstanding=0.52,
        outstanding_strike=19.48,
        options_exercisable=0.269,
        exercisable_strike=19.54,
    ),
    OptionTrancheTerms(
        options_outstanding=0.422,
        outstanding_strike=27.03,
        options_exercisable=0.211,
        exercisable_strike=27.06,
    ),
    OptionTrancheTerms(
        options_outstanding=0.375,
        outstanding_strike=45.78,
        options_exercisable=0.187,
        exercisable_strike=45.75,
    ),
    OptionTrancheTerms(
        options_outstanding=0.0,
        outstanding_strike=0.0,
        options_exercisable=0.0,
        exercisable_strike=0.0,
    ),
    OptionTrancheTerms(
        options_outstanding=0.0,
        outstanding_strike=0.0,
        options_exercisable=0.0,
        exercisable_strike=0.0,
    ),
    OptionTrancheTerms(
        options_outstanding=0.0,
        outstanding_strike=0.0,
        options_exercisable=0.0,
        exercisable_strike=0.0,
    ),
)


@dataclass(frozen=True)
class BaselineAssumptions:
    """Pre-deal capitalization, 5-quarter standalone bridge, opening MRQ balance sheet, and consensus inputs."""

    option_tranches: tuple[OptionTrancheTerms, ...] = field(
        default=DEFAULT_OPTION_TRANCHES,
        metadata=meta(
            rationale="Ten pre-deal stock option tranches (Tranches 1-4 in-the-money at $16.0125 offer price; Tranches 5-7 out-of-the-money).",
            basis="10-tranche option schedule",
            category="cap_table",
        ),
    )
    current_share_price: float = field(
        default=12.81,
        metadata=meta(
            rationale="Unaffected pre-deal market share price ($12.81/sh) used for treasury stock dilution and offer price calculation.",
            basis="Pre-deal common stock trading price ($/share)",
            category="cap_table",
        ),
    )
    offer_premium: float = field(
        default=0.25,
        metadata=meta(
            rationale="Acquisition offer premium of 25.0% over current share price yielding $16.0125/sh offer price.",
            basis="Percentage premium over unaffected share price",
            category="cap_table",
        ),
    )
    basic_shares_outstanding: float = field(
        default=34.922,
        metadata=meta(
            rationale="Pre-deal basic common shares outstanding (34.922M shares).",
            basis="Basic common shares outstanding (M)",
            category="cap_table",
        ),
    )
    legacy_convertible_face_value: float = field(
        default=230.0,
        metadata=meta(
            rationale="Face value of existing 14.25% convertible long-term debt ($230.0M).",
            basis="Principal face value ($M)",
            category="cap_table",
        ),
    )
    legacy_conversion_price: float = field(
        default=26.77,
        metadata=meta(
            rationale="Conversion strike price ($26.77/sh) on existing convertible long-term debt (out-of-the-money at $16.0125 offer price).",
            basis="Conversion price ($/share)",
            category="cap_table",
        ),
    )
    pre_close_fractional_years: tuple[float, ...] = field(
        default=(0.25, 0.25, 0.25, 0.25, 0.25),
        metadata=meta(
            rationale="Quarterly fractional year length (0.25) across MRQ (2012-03-31) through MRQ+4 (2013-03-31).",
            basis="Fraction of 12-month fiscal year per quarter (MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_prior_quarter_sales: tuple[float, ...] = field(
        default=(105.6, 106.7, 108.405, 110.7, 112.2),
        metadata=meta(
            rationale="Prior-quarter net sales anchor ($105.6M prior to MRQ) and sequential quarterly sales series.",
            basis="Prior quarter net sales ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_sales: tuple[float, ...] = field(
        default=(106.7, 108.405, 110.7, 112.2, 114.0),
        metadata=meta(
            rationale="Standalone pre-close quarterly net sales ($106.7M in MRQ rising to $112.2M at close MRQ+3 and $114.0M in MRQ+4).",
            basis="Quarterly net sales ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_cogs: tuple[float, ...] = field(
        default=(54.7, 56.1, 56.8, 57.5, 58.4),
        metadata=meta(
            rationale="Standalone pre-close quarterly cost of goods sold ($54.7M in MRQ to $58.4M in MRQ+4).",
            basis="Quarterly COGS ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_sga: tuple[float, ...] = field(
        default=(20.2, 20.7, 21.0, 21.2, 21.6),
        metadata=meta(
            rationale="Standalone pre-close quarterly selling, general, and administrative expense ($20.2M in MRQ to $21.6M in MRQ+4).",
            basis="Quarterly SG&A ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_depreciation: tuple[float, ...] = field(
        default=(3.3, 3.3, 3.3, 3.3, 3.3),
        metadata=meta(
            rationale="Standalone pre-close quarterly depreciation expense ($3.3M per quarter).",
            basis="Quarterly depreciation ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_amortization: tuple[float, ...] = field(
        default=(4.5, 4.5, 4.5, 4.5, 4.5),
        metadata=meta(
            rationale="Standalone pre-close quarterly intangible asset amortization ($4.5M per quarter).",
            basis="Quarterly intangible amortization ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_sbc: tuple[float, ...] = field(
        default=(2.9, 2.004999999999999, 2.9000000000000057, 3.099999999999998, 3.099999999999998),
        metadata=meta(
            rationale="Standalone pre-close quarterly stock-based compensation expense across MRQ..MRQ+4.",
            basis="Quarterly SBC expense ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_interest_income: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Pre-close quarterly interest income on cash balances ($0.0M across MRQ..MRQ+4).",
            basis="Quarterly interest income ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_non_operating_income: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Pre-close quarterly other non-operating income/expense ($0.0M across MRQ..MRQ+4).",
            basis="Quarterly non-operating income ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_preferred_dividend: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Pre-close quarterly preferred stock dividends ($0.0M across MRQ..MRQ+4).",
            basis="Quarterly preferred dividend ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_noncontrolling_interest: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Pre-close quarterly noncontrolling (minority) interest deduction ($0.0M across MRQ..MRQ+4).",
            basis="Quarterly noncontrolling interest ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_equity_income: tuple[float, ...] = field(
        default=(0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Pre-close quarterly equity income in affiliates ($0.0M across MRQ..MRQ+4).",
            basis="Quarterly equity income in affiliates ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_capex: tuple[float, ...] = field(
        default=(
            5.0,
            5.126757263355202,
            5.187441424554827,
            5.257731958762887,
            5.342080599812559,
        ),
        metadata=meta(
            rationale="Standalone pre-close quarterly capital expenditures ($5.0M in MRQ scaling with sales across MRQ+1..MRQ+4).",
            basis="Quarterly capital expenditures ($M, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    pre_close_common_dividend_per_share: tuple[float, ...] = field(
        default=(0.05, 0.05, 0.05, 0.05, 0.05),
        metadata=meta(
            rationale="Pre-close quarterly common stock dividend per share ($0.05/sh per quarter).",
            basis="Quarterly common dividend ($/share, MRQ..MRQ+4)",
            category="income_statement",
        ),
    )
    mrq_interest_existing_debt: float = field(
        default=8.2,
        metadata=meta(
            rationale="Historical MRQ (2012-03-31) interest expense on existing long-term debt ($8.2M).",
            basis="MRQ reported interest expense ($M)",
            category="income_statement",
        ),
    )
    mrq_tax_provision: float = field(
        default=4.515,
        metadata=meta(
            rationale="Historical MRQ (2012-03-31) income tax provision ($4.515M, 35.0% of $12.9M EBT).",
            basis="MRQ reported tax provision ($M)",
            category="income_statement",
        ),
    )
    mrq_cash: float = field(
        default=146.606,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) cash and equivalents balance ($146.606M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_accounts_receivable: float = field(
        default=131.443,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) accounts receivable balance ($131.443M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_inventories: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) inventories balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_dta_current: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) current deferred tax asset balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_prepaid_expenses: float = field(
        default=8.223,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) prepaid expenses and other current assets ($8.223M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_ppe_gross: float = field(
        default=175.41400000000002,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) gross property, plant, and equipment ($175.414M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_accumulated_depreciation: float = field(
        default=-142.44400000000002,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) accumulated depreciation contra-asset (-$142.444M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_equity_investments: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) equity investments balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_capitalized_financing_costs: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) capitalized financing costs balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_goodwill: float = field(
        default=61.094,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) net goodwill balance ($61.094M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_intangibles_net: float = field(
        default=37.491,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) net identifiable intangible assets ($37.491M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_operating_rights: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) net operating rights ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_other_lt_assets: float = field(
        default=14.29,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) other long-term assets ($14.29M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_short_term_debt: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) short-term debt ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_accounts_payable: float = field(
        default=20.662,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) accounts payable ($20.662M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_accrued_liabilities: float = field(
        default=15.38,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) accrued liabilities ($15.38M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_client_deposits: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) client deposits ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_other_current_liabilities: float = field(
        default=59.132999999999996,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) other current liabilities ($59.133M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_capital_leases: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) capital lease obligations ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_existing_lt_debt: float = field(
        default=230.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) existing long-term debt ($230.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_revolver: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) revolving credit facility balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_term_loan_a: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Term Loan A balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_term_loan_b: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Term Loan B balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_senior_note: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Senior Note balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_subordinated_note: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Subordinated Note balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_mezzanine: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Mezzanine debt balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_seller_note: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Seller Note balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_convertible_bond: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Convertible Bond balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_debt_8: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) placeholder Debt 8 balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_net_dtl: float = field(
        default=-8.828,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) net deferred tax liability / (asset) (-$8.828M net DTA).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_other_lt_liabilities: float = field(
        default=17.917,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) other long-term liabilities ($17.917M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_noncontrolling_interest: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) noncontrolling interest balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_preferred_a: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Preferred Stock A balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_preferred_b: float = field(
        default=0.0,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) Preferred Stock B balance ($0.0M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_common_stock: float = field(
        default=12.609,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) common stock par value ($12.609M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_apic: float = field(
        default=20.154,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) additional paid-in capital ($20.154M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    mrq_retained_earnings: float = field(
        default=65.09,
        metadata=meta(
            rationale="Opening MRQ (2012-03-31) retained earnings ($65.09M).",
            basis="MRQ balance sheet account ($M)",
            category="opening_bs",
        ),
    )
    analyst_fractional_years: tuple[float, ...] = field(
        default=(1.0, 0.75, 1.0, 1.0),
        metadata=meta(
            rationale="Consensus analyst fractional year lengths across FY2012 (1.0), 3Q2013 stub (0.75), FY2014 (1.0), and FY2015 (1.0).",
            basis="Fractional years per period (fy2012, stub_3q2013, fy2014, fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_revenue: tuple[float, ...] = field(
        default=(458.1, 351.0, 470.5, 474.7),
        metadata=meta(
            rationale="Consensus analyst revenue projections ($458.1M in FY12, $351.0M in 3Q13 stub, $470.5M in FY14, $474.7M in FY15).",
            basis="Consensus revenue ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_cogs: tuple[float, ...] = field(
        default=(239.6, 187.35000000000002, 252.2, 252.2),
        metadata=meta(
            rationale="Consensus analyst COGS projections ($239.6M in FY12, $187.35M in 3Q13 stub, $252.2M in FY14..FY15).",
            basis="Consensus COGS ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_sga: tuple[float, ...] = field(
        default=(88.3, 68.775, 92.4, 92.4),
        metadata=meta(
            rationale="Consensus analyst SG&A projections ($88.3M in FY12, $68.775M in 3Q13 stub, $92.4M in FY14..FY15).",
            basis="Consensus SG&A ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_depreciation: tuple[float, ...] = field(
        default=(14.1, 10.575, 14.1, 14.1),
        metadata=meta(
            rationale="Consensus analyst standalone depreciation projections ($14.1M in FY12, $10.575M in 3Q13 stub, $14.1M in FY14..FY15).",
            basis="Consensus depreciation ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_amortization: tuple[float, ...] = field(
        default=(19.6, 14.924999999999999, 20.0, 20.0),
        metadata=meta(
            rationale="Consensus analyst standalone amortization projections ($19.6M in FY12, $14.925M in 3Q13 stub, $20.0M in FY14..FY15).",
            basis="Consensus amortization ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_sbc: tuple[float, ...] = field(
        default=(10.8, 7.949999999999999, 10.7, 10.7),
        metadata=meta(
            rationale="Consensus analyst stock-based compensation projections ($10.8M in FY12, $7.95M in 3Q13 stub, $10.7M in FY14..FY15).",
            basis="Consensus SBC ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    analyst_capex: tuple[float, ...] = field(
        default=(16.0, 12.75, 18.0, 19.0),
        metadata=meta(
            rationale="Consensus analyst capital expenditure projections ($16.0M in FY12, $12.75M in 3Q13 stub, $18.0M in FY14, $19.0M in FY15).",
            basis="Consensus capex ($M, fy2012..fy2015)",
            category="consensus_projections",
        ),
    )
    standalone_post_close_gaap_eps: tuple[float, ...] = field(
        default=(
            0.7091843433611082,
            0.9392215307725688,
            1.0279630005873808,
            1.0530015824273418,
            1.078535726077637,
            1.67002454205314,
            1.6999102905078411,
            1.7301630686741927,
            1.7607868045246877,
            1.7917854653310405,
        ),
        metadata=meta(
            rationale="Standalone No-Deal post-close diluted GAAP EPS baseline across 3Q13 stub through FY22.",
            basis="Diluted GAAP EPS ($/share, 3Q13..FY22 under Case 1: No Deal)",
            category="post_close_eps",
        ),
    )
    standalone_post_close_cash_eps: tuple[float, ...] = field(
        default=(
            1.1337465739483972,
            1.5090165243913565,
            1.5977579942061684,
            1.6278829500593046,
            1.6585488721241677,
            2.25521527622591,
            2.2903248314468714,
            2.325848047598226,
            2.3617892689141424,
            2.3981528826438443,
        ),
        metadata=meta(
            rationale="Standalone No-Deal post-close diluted cash EPS baseline across 3Q13 stub through FY22.",
            basis="Diluted cash EPS ($/share, 3Q13..FY22 under Case 1: No Deal)",
            category="post_close_eps",
        ),
    )

    def get_mrq_bs_balance(self, row_id: str) -> float:
        """Retrieve opening MRQ balance sheet leaf account balance by canonical row key."""
        attr_name = f"mrq_{row_id}"
        if not hasattr(self, attr_name):
            msg = f"Unknown opening MRQ balance sheet row key: {row_id}"
            raise KeyError(msg)
        val: float = getattr(self, attr_name)
        return val
