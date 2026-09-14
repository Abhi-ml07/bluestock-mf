# Day 1 — Data Quality Summary
* Fund master contains **40 schemes** across **10 fund houses**.
* **34 schemes are Equity** and **6 are Debt**.
* **Large Cap** is the largest sub-category with 14 schemes.
* **Moderate** is the largest risk category with 16 schemes.
* All **40 AMFI codes** in the fund master are present in the NAV history. No missing or extra codes were found.
* Live MFAPI data was successfully fetched, but **5 of 6 codes returned different scheme details** from the supplied fund master. The original project data was kept unchanged.

## Analytics app and scheduled ETL

Install dependencies with `pip install -r requirements.txt`, then launch the dashboard:

```bash
streamlit run streamlit_app.py
```

`run_pipeline.py` fetches the six configured NAV histories from MFAPI before refreshing the cleaned data and SQLite database. On a Linux host, make `cron_etl.sh` executable and add this crontab entry for 8 PM every weekday:

```cron
0 20 * * 1-5 /path/to/bluestock-mf/cron_etl.sh >> /path/to/bluestock-mf/reports/etl.log 2>&1
```

The Friday run sends the HTML summary when `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `REPORT_RECIPIENT` are configured. Generate it without sending with `python weekly_report.py`.
