"""Centralized operating, working capital, and cost-savings assumptions for Institutional LBO Reference (Case C)."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.lbo.assumptions.deal import meta


@dataclass(frozen=True)
class OperatingAssumptions:
    """Operating case drivers, cost-savings phase-in parameters, and working capital assumptions."""

    annual_cogs_savings: float = field(
        default=10.0,
        metadata=meta(
            rationale="Full-run-rate annual COGS cost savings achieved under sponsor ownership ($10.0M/year).",
            basis="Annualized COGS cost reduction ($M/year)",
            category="cost_savings",
        ),
    )
    annual_sga_savings: float = field(
        default=20.0,
        metadata=meta(
            rationale="Full-run-rate annual SG&A cost savings achieved under sponsor ownership ($20.0M/year).",
            basis="Annualized SG&A cost reduction ($M/year)",
            category="cost_savings",
        ),
    )
    cogs_savings_phase_in: tuple[float, ...] = field(
        default=(0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        metadata=meta(
            rationale="COGS savings phase-in schedule across FY13 (0%) and FY14..FY22 (100%).",
            basis="Phase-in multiplier by post-close fiscal year (FY13..FY22)",
            category="cost_savings",
        ),
    )
    sga_savings_phase_in: tuple[float, ...] = field(
        default=(0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        metadata=meta(
            rationale="SG&A savings phase-in schedule across FY13 (0%) and FY14..FY22 (100%).",
            basis="Phase-in multiplier by post-close fiscal year (FY13..FY22)",
            category="cost_savings",
        ),
    )
    management_sales_growth: tuple[float, ...] = field(
        default=(0.14, 0.045, 0.035, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025),
        metadata=meta(
            rationale="Management Case annual top-line revenue growth rate assumption (14.0% in FY13 tapering to 2.5% in FY16..FY22).",
            basis="Annual YoY revenue growth rate (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_sales_growth: tuple[float, ...] = field(
        default=(0.015, 0.005341880341880323, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        metadata=meta(
            rationale="Downside Case annual top-line revenue growth trajectory (1.5% in FY13, 0.53% in FY14, 0.0% in FY15..FY22).",
            basis="Annual YoY revenue growth rate (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_cogs_pct_sales: tuple[float, ...] = field(
        default=(0.52, 0.515, 0.515, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51),
        metadata=meta(
            rationale="Management Case standalone COGS as a percentage of sales before sponsor cost savings.",
            basis="COGS / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_cogs_pct_sales: tuple[float, ...] = field(
        default=(0.525, 0.539, 0.542, 0.542, 0.542, 0.542, 0.542, 0.542, 0.542, 0.542),
        metadata=meta(
            rationale="Downside Case standalone COGS as a percentage of sales reflecting margin compression.",
            basis="COGS / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_sga_pct_sales: tuple[float, ...] = field(
        default=(0.19, 0.19, 0.189, 0.188, 0.187, 0.187, 0.187, 0.187, 0.187, 0.187),
        metadata=meta(
            rationale="Management Case standalone SG&A as a percentage of sales before sponsor cost savings.",
            basis="SG&A / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_sga_pct_sales: tuple[float, ...] = field(
        default=(0.20, 0.21, 0.22, 0.22, 0.22, 0.22, 0.22, 0.22, 0.22, 0.22),
        metadata=meta(
            rationale="Downside Case standalone SG&A as a percentage of sales reflecting operating deleverage.",
            basis="SG&A / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_depr_pct_sales: tuple[float, ...] = field(
        default=(0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03),
        metadata=meta(
            rationale="Management Case standalone depreciation as a percentage of sales prior to PP&E write-up.",
            basis="Standalone Depreciation / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_depr_pct_sales: tuple[float, ...] = field(
        default=(0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03),
        metadata=meta(
            rationale="Downside Case standalone depreciation as a percentage of sales prior to PP&E write-up.",
            basis="Standalone Depreciation / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_amort_pct_sales: tuple[float, ...] = field(
        default=(0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04),
        metadata=meta(
            rationale="Management Case standalone intangible amortization as a percentage of sales prior to PPA step-up.",
            basis="Standalone Amortization / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_amort_pct_sales: tuple[float, ...] = field(
        default=(0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04),
        metadata=meta(
            rationale="Downside Case standalone intangible amortization as a percentage of sales prior to PPA step-up.",
            basis="Standalone Amortization / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_sbc_pct_sales: tuple[float, ...] = field(
        default=(0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025),
        metadata=meta(
            rationale="Management Case stock-based compensation expense as a percentage of sales (2.50%).",
            basis="SBC / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_sbc_pct_sales: tuple[float, ...] = field(
        default=(0.0275, 0.0275, 0.0275, 0.0275, 0.0275, 0.0275, 0.0275, 0.0275, 0.0275, 0.0275),
        metadata=meta(
            rationale="Downside Case stock-based compensation expense as a percentage of sales (2.75%).",
            basis="SBC / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    management_capex_pct_sales: tuple[float, ...] = field(
        default=(0.045, 0.044, 0.043, 0.043, 0.043, 0.043, 0.043, 0.043, 0.043, 0.043),
        metadata=meta(
            rationale="Management Case capital expenditures as a percentage of sales (4.5% tapering to 4.3%).",
            basis="Capex / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    downside_capex_pct_sales: tuple[float, ...] = field(
        default=(0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05),
        metadata=meta(
            rationale="Downside Case capital expenditures as a percentage of sales (5.0% flat).",
            basis="Capex / Sales ratio (FY13..FY22)",
            category="operating_scenarios",
        ),
    )
    post_close_fractional_years: tuple[float, ...] = field(
        default=(0.75, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        metadata=meta(
            rationale="Fractional year lengths across the 10 post-close periods (0.75 for 3Q2013 stub; 1.0 for FY14..FY22).",
            basis="Fraction of 12-month fiscal year per period",
            category="calendar",
        ),
    )
    capex_useful_life_years: float = field(
        default=7.0,
        metadata=meta(
            rationale="Straight-line depreciation useful life for post-close capital expenditure cohorts (7.0 years).",
            basis="Useful life in years for new capex additions",
            category="depreciation",
        ),
    )
    capex_salvage_value: float = field(
        default=0.0,
        metadata=meta(
            rationale="Assumed terminal salvage value for post-close capital expenditure cohorts ($0.0M).",
            basis="Salvage value ($M)",
            category="depreciation",
        ),
    )
    sponsor_management_fee_annual: float = field(
        default=0.0,
        metadata=meta(
            rationale="Annual private equity sponsor monitoring/management fee ($0.0M/year in baseline).",
            basis="Annual management fee ($M/year)",
            category="cost_savings",
        ),
    )
