# Bluestock Mutual Fund Analytics

Bluestock MF Analytics is a mutual-fund data platform for ingesting NAV data, cleaning and loading investment datasets, analyzing fund and investor behavior, and exploring results through interactive dashboards.

# Day 1 — Data Quality Summary
* Fund master contains **40 schemes** across **10 fund houses**.
* **34 schemes are Equity** and **6 are Debt**.
* **Large Cap** is the largest sub-category with 14 schemes.
* **Moderate** is the largest risk category with 16 schemes.
* All **40 AMFI codes** in the fund master are present in the NAV history. No missing or extra codes were found.
* Live MFAPI data was successfully fetched, but **5 of 6 codes returned different scheme details** from the supplied fund master. The original project data was kept unchanged.


# The project provides:

- Automated NAV retrieval from `mfapi.in`
- Notebook-based data ingestion and cleaning
- SQLite warehouse creation
- Fund performance, risk, and recommendation analysis
- Streamlit dashboard with interactive filters and charts
- Power BI dashboard at `dashboard/bluestock_mf.pbix`
- Monte Carlo NAV projection and portfolio analytics utilities
- Weekly HTML performance reports with optional email delivery

## Project Structure

```text
data/raw/                 Source datasets and live NAV files
data/processed/           Cleaned datasets used by analytics and dashboards
notebooks/                Data ingestion, cleaning, EDA, and analytics notebooks
sql/                      SQLite schema and analytical queries
dashboard/                Power BI dashboard file
reports/                  Generated CSV, chart, and HTML reports
analytics.py              NAV, Monte Carlo, and portfolio analytics helpers
data_ingestion.py         Raw CSV discovery and loading utility
live_nav_fetch.py         MFAPI NAV downloader
load_database.py          SQLite warehouse builder
run_pipeline.py           End-to-end ETL entry point
streamlit_app.py          Interactive Streamlit dashboard
weekly_report.py          HTML report generator and SMTP sender
cron_etl.sh               Weekday ETL and Friday report scheduler
```

## Requirements

- Python 3.10 or newer
- Internet access for live NAV retrieval from `https://api.mfapi.in`
- Power BI Desktop is optional and only required for the `.pbix` dashboard

Install the Python dependencies from the project root.

### Windows PowerShell

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the ETL Pipeline

Run the complete pipeline from the repository root:

```bash
python run_pipeline.py
```

The pipeline performs these steps:

1. Fetches live NAV histories for the six configured AMFI schemes in `live_nav_fetch.py`.
2. Executes `notebooks/01_data_ingestion.ipynb`.
3. Executes `notebooks/02_data_cleaning.ipynb`.
4. Rebuilds `bluestock_mf.db` using `load_database.py`.
5. Validates the resulting warehouse tables.

To fetch only the live NAV files:

```bash
python live_nav_fetch.py
```

To rebuild the SQLite database from the existing processed files:

```bash
python load_database.py
```

The database is written to `bluestock_mf.db`. Running `load_database.py` recreates the database from the current CSV inputs.

## Run the Streamlit Dashboard

Start the interactive dashboard from the repository root:

```bash
streamlit run streamlit_app.py
```

Open the local URL shown by Streamlit, normally:

```text
http://localhost:8501
```

The dashboard contains five sections:

### Industry Overview

- Total AUM
- Monthly SIP inflows
- Total folios
- Number of schemes and fund houses
- Fund-house AUM chart
- Industry AUM and folio trends

### Fund Performance

- Fund-house filter
- Category filter
- Scheme filter
- Three-year return/CAGR
- Sharpe ratio
- Alpha
- Maximum drawdown
- Fund scorecard
- Return-versus-risk chart

### Investor Analytics

- Total transaction count
- SIP transaction count
- Invested amount
- Unique investors
- Transaction-type distribution
- State-wise investment
- Age-group analysis
- Monthly investment trend

### SIP & Market Trends

- SIP inflow and SIP AUM trends
- Category-level net inflows
- Benchmark index selector
- NIFTY benchmark comparison when available
- Monthly benchmark trends

### NAV Detail

- Mutual-fund selector
- Historical NAV chart
- One-year return
- Three-year return
- Sharpe ratio
- Maximum drawdown
- Recent NAV records

## Open the Power BI Dashboard

Open this file in Power BI Desktop:

```text
dashboard/bluestock_mf.pbix
```

The Power BI file is kept as the report-oriented dashboard, while Streamlit provides a Python-based interactive companion.

## Scheduled ETL

### Linux cron

Make the scheduler executable:

```bash
chmod +x cron_etl.sh
```

Add this entry to run at 8:00 PM every weekday:

```cron
0 20 * * 1-5 /absolute/path/to/bluestock-mf/cron_etl.sh >> /absolute/path/to/bluestock-mf/reports/etl.log 2>&1
```

The wrapper runs `run_pipeline.py`. On Fridays it also attempts to send the weekly HTML report when the SMTP variables below are configured.

### Windows Task Scheduler

Create a task that runs every weekday at 8:00 PM with:

- Program: `D:\bluestock-mf\venv\Scripts\python.exe`
- Arguments: `D:\bluestock-mf\run_pipeline.py`
- Start in: `D:\bluestock-mf`

For a Friday report, add a second weekly action for `weekly_report.py --send`.

## Weekly HTML Report and Email

Generate the report without sending an email:

```bash
python weekly_report.py
```

The output is written to:

```text
reports/weekly_performance_report.html
```

To send the report, configure these environment variables before running:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
REPORT_RECIPIENT
```

Then run:

```bash
python weekly_report.py --send
```

Do not commit SMTP passwords or other credentials to the repository.

## Dataset Descriptions

### Raw datasets

| File | Description |
| --- | --- |
| `01_fund_master.csv` | Scheme master data, AMFI codes, fund houses, categories, plans, benchmarks, fees, and risk categories. |
| `02_nav_history.csv` | Historical daily NAV by AMFI code. |
| `03_aum_by_fund_house.csv` | Fund-house AUM, date, and scheme count. |
| `04_monthly_sip_inflows.csv` | Monthly SIP inflows, active accounts, new accounts, SIP AUM, and year-over-year growth. |
| `05_category_inflows.csv` | Monthly net inflows by mutual-fund category. |
| `06_industry_folio_count.csv` | Total, equity, debt, hybrid, and other folio counts by month. |
| `07_scheme_performance.csv` | Scheme-level returns, alpha, beta, Sharpe, volatility, drawdown, AUM, fees, and risk grade. |
| `08_investor_transactions.csv` | Investor transactions with dates, types, amounts, state, city, age group, gender, and payment mode. |
| `09_portfolio_holdings.csv` | Scheme holdings, securities, sectors, weights, values, and prices. |
| `10_benchmark_indices.csv` | Benchmark index observations by date and index name. |
| `*_live_nav.csv` | NAV histories fetched from MFAPI for the configured schemes. |

### Processed datasets

| File | Description |
| --- | --- |
| `02_nav_history_clean.csv` | Cleaned and normalized NAV history. |
| `07_scheme_performance_clean.csv` | Cleaned scheme performance table used by the dashboard. |
| `08_investor_transactions_clean.csv` | Cleaned investor transaction table. |
| `alpha_beta.csv` | Alpha and beta analysis with ranking. |
| `fund_scorecard.csv` | Composite fund scorecard covering CAGR, Sharpe, alpha, expense, and drawdown metrics. |

## Analytics and Reports

`analytics.py` contains reusable functions for NAV loading, Monte Carlo projection, portfolio optimization, and fund labels. Additional notebooks provide data quality checks, exploratory analysis, performance analytics, and advanced investor and risk analysis.

Generated outputs are stored in `reports/`, including:

- `var_cvar_report.csv`
- `weekly_performance_report.html`
- ETL logs when the scheduler redirects output to `reports/etl.log`

## Data Quality Note

Live MFAPI scheme metadata can differ from the supplied fund master. The ETL stores fetched NAV files separately under `data/raw/` and does not overwrite the original fund master metadata.
