# Institutional LBO Model (`models.lbo`)

A production-grade, 29-schedule Wall Street Leveraged Buyout (LBO) model codified with [`f8-engine`](https://pypi.org/project/f8-engine/).

This self-contained package illustrates how to author, audit, and compile a fully integrated multi-schedule corporate finance model in Python while emitting a clean, live-formula Excel deliverable (`.xlsx`).

---

## Preview

### Executive Dashboard
Emitted live Excel executive command center featuring 3-column synchronized layout:
![Executive Dashboard](../../assets/lbo-dashboard.png)

### Transaction & Purchase Price Allocation
Pre-deal option tranches, fully diluted share count, sources & uses, debt fees, and PPA write-ups:
![Transaction & PPA](../../assets/lbo-transaction.png)

---

## Model Architecture

The model spans an **18-column unified timeline**:
- **Historical Bridge**: 4 pre-deal historical quarters (`2022-03-31` through `2022-12-31`) and bridge quarter (`2023-03-31`)
- **Transaction Stub**: Standalone close, deal adjustments, Pro Forma Close, and 3-quarter stub (`2023-09-30`)
- **Post-Close Forecast**: Full post-close projection horizon (`2024-09-30` through `2032-09-30`)

### 4-Sheet Institutional Layout

1. **Executive Dashboard** (3-column executive command center):
   - Sources & Uses Summary
   - Entry Valuation & Transaction Structure
   - Implied Transaction Multiples
   - Sponsor Returns Summary (MoIC & IRR)
   - Credit Profile & Leverage Progression
   - Model Integrity Checks (Statement Equality, Cash Tie-outs, Circularity Invariants)

2. **Transaction & PPA**:
   - Option Tranches (In-the-money option liquidation and treasury stock method)
   - Fully Diluted Shares Outstanding (Pre-deal)
   - Sources & Uses of Funds
   - Financing Fees & Original Issue Discount (OID) Amortization
   - Purchase Price Allocation (Fair-value write-ups, DTL creation, Goodwill recognition)
   - Transaction Balance Sheet (Pre-deal, adjustments, pro forma opening)

3. **LBO Model**:
   - Income Statement (Standalone vs. Pro Forma with EPS accretion/dilution)
   - Balance Sheet (100% live accounting equality `Assets = Liabilities + Equity`)
   - Cash Flow Statement (Operating, investing, and financing cash flows with zero plugs)
   - Working Capital Schedule (Receivables, inventory, payables, accruals turnover)
   - Debt Sweep Schedule (Revolver, Term Loan A/B, Senior Notes, Mezzanine PIK, Preferred Stock with contractual priority mechanics)
   - Depreciation & Amortization Schedule
   - Section 382 NOL & AMT Carryforward Schedule
   - Convertible Security Dilution & Diluted Share Count
   - Credit Statistics & Covenant Compliance (Debt/EBITDA, Interest Coverage, FCCR)
   - Operating Schedule (Revenue drivers, COGS, OpEx, CapEx, D&A)

4. **Valuation & Returns**:
   - DCF Valuation Schedule (Exact-date unlevered free cash flows, terminal value)
   - Exit Valuation & Sponsor Returns Waterfall (Gross/Net MoIC, IRR across exit years)
   - Equity Dilution Schedule
   - Pre-deal CAPM & Pro Forma WACC Schedule
   - DCF Sensitivity Matrix

---

## Usage

From the repository root:

```bash
# Emit the live OpenXML Excel workbook
uv run python -m models.lbo deliverables/lbo_model.xlsx

# Run the LBO verification test suite (190 tests)
uv run pytest tests/lbo
```

---

## Package Structure

```text
models/lbo/
├── __init__.py                 # Public package exports
├── __main__.py                 # CLI entry point (python -m models.lbo)
├── model.py                    # Model composition, compilation, and Excel emitter
├── layout.py                   # Declarative multi-sheet layout engine
├── registry.py                 # SSOT schedule and tranche configuration specs
├── timeline.py                 # Unified 18-period timeline builder
├── dashboard.py                # Executive dashboard tables
├── transaction.py              # Sources & uses, PPA, fees, transaction balance sheet
├── statements.py               # Core balance sheet, income, and cash flow statements
├── operating_da.py             # Operating buildup, revenue breakdown, depreciation/amortization
├── debt_sweep.py               # Priority cash flow sweep and debt schedules
├── working_capital.py          # Working capital schedules
├── tax_dilution.py             # Section 382 NOL, AMT, convertible dilution
├── credit_stats.py             # Credit ratios, interest coverage, leverage metrics
├── dcf_wacc.py                 # WACC, unlevered FCF discounting, sensitivity analysis
├── cap_table.py                # Option tranches and fully diluted equity counts
├── returns.py                  # Returns waterfall, equity dilution, IRR & MoIC calculations
└── assumptions/                # Self-contained @dataclass(frozen=True) forward assumptions
    ├── __init__.py             # LboAssumptions top-level container
    ├── baseline.py             # Pre-deal capital structure, share prices, historical statements
    ├── deal.py                 # Purchase price, financing tranches, fees, PPA parameters
    ├── financing.py            # Spreads, margins, PIK toggles, mandatory amortization
    ├── operating.py            # Revenue growth, margin profiles, working capital days
    └── timeline.py             # Closing calendar, fiscal year boundaries, stub periods
```
