"""CLI entry point to compile and emit the Institutional LBO Excel deliverable."""

from __future__ import annotations

import sys
from pathlib import Path

from models.lbo.model import DEFAULT_DELIVERABLE_PATH, emit_lbo_workbook


def main() -> None:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DELIVERABLE_PATH
    print(f"Compiling Institutional LBO Model into '{dest}'...")
    output = emit_lbo_workbook(output_path=dest)
    print(f"✓ Emitted live-formula Excel workbook: {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
