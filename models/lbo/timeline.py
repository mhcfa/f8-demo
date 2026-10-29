"""Timeline column definitions, period keys, and layout helpers for the Institutional LBO Reference model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import f8

from models.lbo.assumptions.timeline import TimelineAssumptions

if TYPE_CHECKING:
    from models.lbo.assumptions import LboAssumptions

DEFAULT_TIMELINE = TimelineAssumptions()

STUB_PERIOD_KEY: str = "stub_3q"
ANNUAL_PROJECTION_KEYS: tuple[str, ...] = (
    "fy_2",
    "fy_3",
    "fy_4",
    "fy_5",
    "fy_6",
    "fy_7",
    "fy_8",
    "fy_9",
    "fy_10",
)
POST_CLOSE_PERIOD_KEYS: tuple[str, ...] = (STUB_PERIOD_KEY, *ANNUAL_PROJECTION_KEYS)
EXIT_PERIOD_KEY: str = POST_CLOSE_PERIOD_KEYS[DEFAULT_TIMELINE.exit_year_index]
FINAL_PERIOD_KEY: str = POST_CLOSE_PERIOD_KEYS[-1]
DCF_PROJECTION_KEYS: tuple[str, ...] = (
    STUB_PERIOD_KEY,
    "fy_2",
    "fy_3",
    "fy_4",
    "fy_5",
)
CONCURRENT_PROJECTION_KEYS: tuple[str, ...] = (
    STUB_PERIOD_KEY,
    "fy_2",
    "fy_3",
    "fy_4",
    "fy_5",
)

PeriodKey = Literal[
    "mrq",
    "mrq_plus_1",
    "mrq_plus_2",
    "mrq_plus_3",
    "mrq_plus_4",
    "standalone_close",
    "deal_adjustments",
    "pf_close",
    "stub_3q",
    "fy_2",
    "fy_3",
    "fy_4",
    "fy_5",
    "fy_6",
    "fy_7",
    "fy_8",
    "fy_9",
    "fy_10",
]

PRE_CLOSE_ROLL_COLS: tuple[str, ...] = (
    "mrq_plus_1",
    "mrq_plus_2",
    "mrq_plus_3",
    "mrq_plus_4",
)
PRE_CLOSE_ALL_COLS: tuple[str, ...] = ("mrq", *PRE_CLOSE_ROLL_COLS)
PRE_PF_COLS: tuple[str, ...] = (
    *PRE_CLOSE_ALL_COLS,
    "standalone_close",
    "deal_adjustments",
)


def build_pre_close_quarter_cols(
    timeline: TimelineAssumptions = DEFAULT_TIMELINE,
) -> dict[str, tuple[str | None, list[str]]]:
    """Derive pre-close quarter column headers from timeline assumptions."""
    cy = timeline.close_year
    return {
        "mrq": ("Historical", ["MRQ", f"{cy}-03-31"]),
        "mrq_plus_1": ("Quarterly Rollforward", ["MRQ+1", f"{cy}-06-30"]),
        "mrq_plus_2": ("Quarterly Rollforward", ["MRQ+2", f"{cy}-09-30"]),
        "mrq_plus_3": ("Quarterly Rollforward", ["MRQ+3", f"{cy}-12-31"]),
        "mrq_plus_4": ("Quarterly Rollforward", ["MRQ+4", f"{cy + 1}-03-31"]),
    }


def build_post_close_period_cols(
    timeline: TimelineAssumptions = DEFAULT_TIMELINE,
) -> dict[str, tuple[str | None, list[str]]]:
    """Derive post-close projection period column headers from timeline assumptions."""
    cy = timeline.close_year
    fy_md = f"{timeline.fiscal_year_end_month:02d}-{timeline.fiscal_year_end_day:02d}"
    cols: dict[str, tuple[str | None, list[str]]] = {
        STUB_PERIOD_KEY: (None, ["3 Quarters", "Ending", f"{cy + 1}-{fy_md}"]),
    }
    for idx in range(2, timeline.post_close_years + 1):
        cols[f"fy_{idx}"] = (
            "Annual Projections",
            [f"Year {idx}", f"{cy + idx}"],
        )
    return cols


def build_timeline_columns(
    timeline: TimelineAssumptions = DEFAULT_TIMELINE,
) -> dict[str, tuple[str | None, list[str]]]:
    """Derive full continuous 18-period timeline column definitions from timeline assumptions."""
    close_iso = timeline.close_date_iso
    return {
        **build_pre_close_quarter_cols(timeline),
        "standalone_close": (None, ["Standalone", "at Close", close_iso]),
        "deal_adjustments": (None, ["Deal", "Adjustments"]),
        "pf_close": (None, ["Pro Forma", "at Close", close_iso]),
        **build_post_close_period_cols(timeline),
    }


PRE_CLOSE_QUARTER_COLS: dict[str, tuple[str | None, list[str]]] = build_pre_close_quarter_cols(
    DEFAULT_TIMELINE
)
POST_CLOSE_PERIOD_COLS: dict[str, tuple[str | None, list[str]]] = build_post_close_period_cols(
    DEFAULT_TIMELINE
)
TIMELINE_COLUMNS: dict[str, tuple[str | None, list[str]]] = build_timeline_columns(DEFAULT_TIMELINE)
TIMELINE_COL_KEYS: tuple[str, ...] = tuple(TIMELINE_COLUMNS.keys())


def add_post_close_columns(
    table: f8.Table,
    item_header: str,
    assumptions: LboAssumptions | None = None,
) -> None:
    """Add descriptor, pf_close, and 10 post-close period columns to a table."""
    timeline = assumptions.timeline if assumptions is not None else DEFAULT_TIMELINE
    post_cols = (
        POST_CLOSE_PERIOD_COLS if assumptions is None else build_post_close_period_cols(timeline)
    )
    table.add_column("label", role="descriptor", header=item_header)
    table.add_column("pf_close", headers=["Pro Forma", "at Close", timeline.close_date_iso])
    for col_id, (col_group, col_headers) in post_cols.items():
        table.add_column(col_id, group=col_group, headers=col_headers)


def add_timeline_columns(
    table: f8.Table,
    item_header: str,
    assumptions: LboAssumptions | None = None,
) -> None:
    """Add descriptor and all 18 continuous timeline columns to a table."""
    timeline_cols = (
        TIMELINE_COLUMNS if assumptions is None else build_timeline_columns(assumptions.timeline)
    )
    table.add_column("label", role="descriptor", header=item_header)
    for col_id, (col_group, col_headers) in timeline_cols.items():
        table.add_column(col_id, group=col_group, headers=col_headers)


def inactive_pre_pf_cells(
    label: str,
    *,
    include_pf_close: bool = True,
) -> dict[str, f8.CellInputValue]:
    """Build initial cell mapping with None across inactive pre-close and bridge columns."""
    cols = (*PRE_PF_COLS, "pf_close") if include_pf_close else PRE_PF_COLS
    cells: dict[str, f8.CellInputValue] = dict.fromkeys(cols, None)
    cells["label"] = label
    return cells


__all__ = [
    "ANNUAL_PROJECTION_KEYS",
    "CONCURRENT_PROJECTION_KEYS",
    "DCF_PROJECTION_KEYS",
    "EXIT_PERIOD_KEY",
    "FINAL_PERIOD_KEY",
    "POST_CLOSE_PERIOD_COLS",
    "POST_CLOSE_PERIOD_KEYS",
    "PRE_CLOSE_ALL_COLS",
    "PRE_CLOSE_QUARTER_COLS",
    "PRE_CLOSE_ROLL_COLS",
    "PRE_PF_COLS",
    "PeriodKey",
    "STUB_PERIOD_KEY",
    "TIMELINE_COLUMNS",
    "TIMELINE_COL_KEYS",
    "add_post_close_columns",
    "add_timeline_columns",
    "build_post_close_period_cols",
    "build_pre_close_quarter_cols",
    "build_timeline_columns",
    "inactive_pre_pf_cells",
]
