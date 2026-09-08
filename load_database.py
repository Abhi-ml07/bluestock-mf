import os
import pandas as pd
from sqlalchemy import create_engine, text

if os.path.exists("bluestock_mf.db"):
    os.remove("bluestock_mf.db")

engine = create_engine("sqlite:///bluestock_mf.db")

with engine.begin() as conn:
    script = open("sql/schema.sql", encoding="utf-8").read()
    for statement in script.split(";"):
        if statement.strip():
            conn.exec_driver_sql(statement)

funds = pd.read_csv("data/raw/01_fund_master.csv")
nav = pd.read_csv("data/processed/02_nav_history_clean.csv")
transactions = pd.read_csv("data/processed/08_investor_transactions_clean.csv")
performance = pd.read_csv("data/processed/07_scheme_performance_clean.csv")
aum = pd.read_csv("data/raw/03_aum_by_fund_house.csv")
sip = pd.read_csv("data/raw/04_monthly_sip_inflows.csv")
folio_count = pd.read_csv("data/raw/06_industry_folio_count.csv")
category_inflows = pd.read_csv("data/raw/05_category_inflows.csv")
benchmark = pd.read_csv("data/raw/10_benchmark_indices.csv")

funds["launch_date"] = pd.to_datetime(funds["launch_date"]).dt.strftime("%Y-%m-%d")

nav["date"] = pd.to_datetime(nav["date"]).dt.strftime("%Y-%m-%d")

transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"]
).dt.strftime("%Y-%m-%d")

aum["date"] = pd.to_datetime(aum["date"]).dt.strftime("%Y-%m-%d")

sip["month"] = pd.to_datetime(sip["month"]).dt.strftime("%Y-%m-%d")

folio_count["month"] = pd.to_datetime(
    folio_count["month"]
).dt.strftime("%Y-%m-%d")

category_inflows["month"] = pd.to_datetime(
    category_inflows["month"]
).dt.strftime("%Y-%m-%d")

benchmark["date"] = pd.to_datetime(
    benchmark["date"]
).dt.strftime("%Y-%m-%d")

funds.to_sql("dim_fund", engine, if_exists="append", index=False)

dates = pd.concat([
    nav[["date"]],
    transactions[["transaction_date"]].rename(columns={"transaction_date": "date"}),
    aum[["date"]],
    sip[["month"]].rename(columns={"month": "date"}),
    folio_count[["month"]].rename(columns={"month": "date"}),
    category_inflows[["month"]].rename(columns={"month": "date"}),
    benchmark[["date"]]
]).drop_duplicates()

dates["date"] = pd.to_datetime(dates["date"])
dates["year"] = dates["date"].dt.year
dates["month"] = dates["date"].dt.month
dates["month_name"] = dates["date"].dt.month_name()
dates["quarter"] = dates["date"].dt.quarter
dates["day"] = dates["date"].dt.day
dates["day_name"] = dates["date"].dt.day_name()
dates["date"] = dates["date"].dt.strftime("%Y-%m-%d")

dates.to_sql("dim_date", engine, if_exists="append", index=False)

fund_houses = funds[["fund_house"]].drop_duplicates().reset_index(drop=True)

fund_houses["fund_house_id"] = range(1, len(fund_houses) + 1)

fund_houses = fund_houses[["fund_house_id", "fund_house"]]

fund_houses.to_sql("dim_fund_house", engine, if_exists="append", index=False)

nav.to_sql("fact_nav", engine, if_exists="append", index=False)

transactions.insert(
    0,
    "transaction_id",
    range(1, len(transactions) + 1)
)

transactions.to_sql(
    "fact_transactions",
    engine,
    if_exists="append",
    index=False
)

performance["anomaly_flag"] = performance["anomaly_flag"].astype(int)

performance.to_sql(
    "fact_performance",
    engine,
    if_exists="append",
    index=False
)

aum = aum.merge(
    fund_houses,
    on="fund_house",
    how="left"
)

aum.to_sql(
    "fact_aum",
    engine,
    if_exists="append",
    index=False
)

sip.to_sql(
    "fact_sip",
    engine,
    if_exists="append",
    index=False
)

folio_count.to_sql(
    "fact_folio_count",
    engine,
    if_exists="append",
    index=False
)

category_inflows.to_sql(
    "fact_category_inflows",
    engine,
    if_exists="append",
    index=False
)

benchmark.to_sql(
    "fact_benchmark",
    engine,
    if_exists="append",
    index=False
)

tables = [
    "dim_date",
    "dim_fund",
    "dim_fund_house",
    "fact_aum",
    "fact_benchmark",
    "fact_category_inflows",
    "fact_folio_count",
    "fact_nav",
    "fact_performance",
    "fact_sip",
    "fact_transactions"
]

print("Database created successfully")
print("Tables:")

for table in tables:
    with engine.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        ).scalar()

    print(f"{table}: {count} rows")