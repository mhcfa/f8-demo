"""Centralized forecast and transaction assumptions package for Institutional LBO Reference (Case C)."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.lbo.assumptions.baseline import (
    DEFAULT_OPTION_TRANCHES,
    BaselineAssumptions,
    OptionTrancheTerms,
)
from models.lbo.assumptions.deal import (
    CASE_KEYS,
    CaseKey,
    DealAssumptions,
    get_driver_metadata_records,
    meta,
)
from models.lbo.assumptions.financing import (
    NEW_FINANCING_TRANCHE_KEYS,
    TRANCHE_KEYS,
    FinancingAssumptions,
    NewFinancingTrancheKey,
    TrancheKey,
    TrancheTerms,
)
from models.lbo.assumptions.operating import OperatingAssumptions
from models.lbo.assumptions.timeline import TimelineAssumptions


@dataclass(frozen=True)
class LboAssumptions:
    """Composite assumptions container uniting baseline, deal, financing, operating, and timeline drivers."""

    baseline: BaselineAssumptions = field(
        default_factory=BaselineAssumptions,
        metadata=meta(
            rationale="Pre-deal capitalization, 5-quarter standalone bridge, opening MRQ balance sheet, and consensus projections.",
            basis="Composite baseline assumptions container",
            category="container",
        ),
    )
    deal: DealAssumptions = field(
        default_factory=DealAssumptions,
        metadata=meta(
            rationale="Transaction structure, fee, PPA, and tax parameters.",
            basis="Composite deal assumptions container",
            category="container",
        ),
    )
    financing: FinancingAssumptions = field(
        default_factory=FinancingAssumptions,
        metadata=meta(
            rationale="Financing scenario draw schedules and contractual tranche terms.",
            basis="Composite financing assumptions container",
            category="container",
        ),
    )
    operating: OperatingAssumptions = field(
        default_factory=OperatingAssumptions,
        metadata=meta(
            rationale="Operating scenarios, cost savings, and working capital turnover assumptions.",
            basis="Composite operating assumptions container",
            category="container",
        ),
    )
    timeline: TimelineAssumptions = field(
        default_factory=TimelineAssumptions,
        metadata=meta(
            rationale="Transaction closing calendar parameters, fiscal year end, and projection horizon.",
            basis="Composite timeline assumptions container",
            category="container",
        ),
    )


__all__ = [
    "CASE_KEYS",
    "DEFAULT_OPTION_TRANCHES",
    "NEW_FINANCING_TRANCHE_KEYS",
    "TRANCHE_KEYS",
    "BaselineAssumptions",
    "CaseKey",
    "DealAssumptions",
    "FinancingAssumptions",
    "LboAssumptions",
    "NewFinancingTrancheKey",
    "OperatingAssumptions",
    "OptionTrancheTerms",
    "TimelineAssumptions",
    "TrancheKey",
    "TrancheTerms",
    "get_driver_metadata_records",
    "meta",
]
