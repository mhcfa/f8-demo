"""Centralized transaction timeline, period indexing, and calendar scheduling assumptions."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.lbo.assumptions.deal import meta


def _default_returns_schedule_dates(
    close_year: int = 2022,
    close_month: int = 12,
    close_day: int = 31,
    fy_end_month: int = 9,
    fy_end_day: int = 30,
    post_close_years: int = 10,
) -> tuple[tuple[int, int, int], ...]:
    """Generate calendar (year, month, day) schedule from close through FY end of post-close years."""
    close_dt = (close_year, close_month, close_day)
    annual_dts = tuple(
        (close_year + offset, fy_end_month, fy_end_day) for offset in range(1, post_close_years + 1)
    )
    return (close_dt, *annual_dts)


@dataclass(frozen=True)
class TimelineAssumptions:
    """Centralized timeline parameters governing transaction close and projection horizons."""

    close_year: int = field(
        default=2022,
        metadata=meta(
            rationale="Anchor transaction closing calendar year (2022).",
            basis="Transaction close calendar year defining pre-close and post-close temporal anchor",
            category="timeline",
        ),
    )
    close_month: int = field(
        default=12,
        metadata=meta(
            rationale="Transaction closing calendar month (December).",
            basis="Transaction close occurs on month 12",
            category="timeline",
        ),
    )
    close_day: int = field(
        default=31,
        metadata=meta(
            rationale="Transaction closing calendar day (December 31).",
            basis="Transaction close occurs on day 31",
            category="timeline",
        ),
    )
    fiscal_year_end_month: int = field(
        default=9,
        metadata=meta(
            rationale="Company fiscal year-end calendar month (September).",
            basis="Company fiscal year ends on September 30",
            category="timeline",
        ),
    )
    fiscal_year_end_day: int = field(
        default=30,
        metadata=meta(
            rationale="Company fiscal year-end calendar day (September 30).",
            basis="Company fiscal year ends on September 30",
            category="timeline",
        ),
    )
    historical_quarters: int = field(
        default=5,
        metadata=meta(
            rationale="Number of historical pre-close quarters evaluated in standalone bridge.",
            basis="5 pre-close quarters spanning MRQ through MRQ+4",
            category="timeline",
        ),
    )
    post_close_years: int = field(
        default=10,
        metadata=meta(
            rationale="Number of post-close projection periods (stub period + 9 full fiscal years).",
            basis="10 post-close projection periods (Year 1 stub through Year 10)",
            category="timeline",
        ),
    )
    exit_year_index: int = field(
        default=4,
        metadata=meta(
            rationale="Zero-based index of the benchmark exit year within post-close periods (index 4 = Year 5 / FY2027).",
            basis="Benchmark sponsor exit occurs at the end of post-close year 5",
            category="timeline",
        ),
    )
    returns_schedule_dates: tuple[tuple[int, int, int], ...] = field(
        default_factory=_default_returns_schedule_dates,
        metadata=meta(
            rationale="Calendar (year, month, day) schedule from transaction close (2022-12-31) through FY2032 (2032-09-30) for XIRR discounting.",
            basis="Exact period-end dates for Actual/365 XIRR evaluation",
            category="timeline",
        ),
    )

    def __post_init__(self) -> None:
        """Derive returns_schedule_dates dynamically if non-default close parameters are provided."""
        expected_default = _default_returns_schedule_dates()
        if self.returns_schedule_dates == expected_default and (
            self.close_year != 2022
            or self.close_month != 12
            or self.close_day != 31
            or self.fiscal_year_end_month != 9
            or self.fiscal_year_end_day != 30
            or self.post_close_years != 10
        ):
            object.__setattr__(
                self,
                "returns_schedule_dates",
                _default_returns_schedule_dates(
                    close_year=self.close_year,
                    close_month=self.close_month,
                    close_day=self.close_day,
                    fy_end_month=self.fiscal_year_end_month,
                    fy_end_day=self.fiscal_year_end_day,
                    post_close_years=self.post_close_years,
                ),
            )

    @property
    def close_date(self) -> tuple[int, int, int]:
        """Return the transaction closing (year, month, day) tuple."""
        return (self.close_year, self.close_month, self.close_day)

    @property
    def close_date_iso(self) -> str:
        """Return the transaction closing date as an ISO-8601 string (YYYY-MM-DD)."""
        return f"{self.close_year:04d}-{self.close_month:02d}-{self.close_day:02d}"

    @property
    def exit_fiscal_year(self) -> int:
        """Return the calendar year corresponding to the benchmark exit fiscal year."""
        return self.close_year + self.exit_year_index + 1

    @property
    def exit_period_key(self) -> str:
        """Return the coordinate column key of the benchmark exit period."""
        return f"fy_{self.exit_year_index + 1}"

    @property
    def final_period_key(self) -> str:
        """Return the coordinate column key of the final post-close period."""
        return f"fy_{self.post_close_years}"

    @property
    def capex_cohort_years(self) -> tuple[str, ...]:
        """Return tuple of calendar year strings corresponding to capex cohorts 1 through 10."""
        return tuple(
            str(self.close_year + offset) for offset in range(1, self.post_close_years + 1)
        )


__all__ = [
    "TimelineAssumptions",
]
