# European Power Market Fundamentals

**How do renewable generation, electricity demand, and cross-border flows relate to negative day-ahead prices and daily price spreads?**

A DE-LU portfolio study targeting the full 2024 calendar year. Spain and Portugal are later extensions.

**Status:** pipeline, analysis modules, notebook, tests and six chart/report generators implemented. Official retrieval and empirical findings await ENTSOE_API_KEY. No new numerical findings or completed empirical charts are claimed.

## Reproduce

Use Python 3.11+ from this repository directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Set ENTSOE_API_KEY securely in your environment.
python -m pytest -q
python -m power_market.run
```

The final command downloads monthly official XML, validates coverage and writes outputs. Data and credentials are excluded from Git. Dependencies are bounded; record pip freeze with the successful run.

## Deliverables

- power_market/data.py: retrieval, units, provenance and interval alignment.
- power_market/analysis.py: residual load, daily spreads and negative-price runs.
- power_market/run.py: six charts, coverage/association tables and market report.
- notebooks/fundamentals.ipynb: guided analysis using the modules.
- [Inspection](docs/inspection.md), [data and methods](docs/data-methods.md), [report status](reports/market-report.md).

Charts cover price distribution, seasonality, daily spreads/negative hours, physical fundamentals, flow conditions and three unusual days. Each includes units, dates and source notes. All require validated official data.

## Findings and limitations

No empirical findings are available yet. After successful execution see outputs/market-report.md, summary.json, associations.csv and the six PNG charts. Residual load is demand minus wind and solar generation. Negative-price exposure informs renewable revenue review; daily ranges screen flexibility opportunities but are not storage profits. Actual fundamentals and flows are ex post; correlations do not identify causal effects or actionable forecasts.

UTC interval alignment preserves daylight-saving changes and different resolutions. Missing observations remain missing; incomplete required series stop report generation. See the methodology for units, source access, rights, border definitions and limitations.

## Preserved work and future scope

Both original notebooks remain intact as historical explorations, and the original README is preserved in docs/legacy-readme.md. Their useful source-query and daily-price ideas informed this implementation. Their unsupported trading claims are superseded. No dashboard or additional model complexity is needed. Spain/Portugal, ex-ante fundamentals and seasonally controlled sensitivity checks are future extensions after DE-LU validation.
