from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NAV_FILE = PROJECT_ROOT / "data" / "processed" / "02_nav_history_clean.csv"
FUND_MASTER_FILE = PROJECT_ROOT / "data" / "raw" / "01_fund_master.csv"
BENCHMARK_FILE = PROJECT_ROOT / "data" / "raw" / "10_benchmark_indices.csv"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RISK_FREE_RATE = 0.065
TRADING_DAYS = 252
RISK_FREE_DAILY = RISK_FREE_RATE / TRADING_DAYS


def calculate_cagr(start_value, end_value, years):
    """Calculate CAGR."""
    if pd.isna(start_value) or pd.isna(end_value):
        return np.nan

    if start_value <= 0 or end_value <= 0 or years <= 0:
        return np.nan

    return (end_value / start_value) ** (1 / years) - 1


def calculate_max_drawdown(returns):
    """Calculate maximum drawdown."""
    wealth = (1 + returns.fillna(0)).cumprod()
    peak = wealth.cummax()
    drawdown = wealth / peak - 1

    return drawdown.min()


def calculate_alpha_beta(fund_returns, benchmark_returns):
    """Calculate CAPM Alpha and Beta."""

    data = pd.concat(
        [fund_returns.rename("fund"), benchmark_returns.rename("benchmark")],
        axis=1
    ).dropna()

    if len(data) < 30:
        return np.nan, np.nan

    benchmark_variance = data["benchmark"].var()

    if benchmark_variance == 0 or pd.isna(benchmark_variance):
        return np.nan, np.nan

    beta = data["fund"].cov(data["benchmark"]) / benchmark_variance

    fund_mean = data["fund"].mean()
    benchmark_mean = data["benchmark"].mean()

    alpha = (
        (fund_mean - RISK_FREE_DAILY)
        - beta * (benchmark_mean - RISK_FREE_DAILY)
    ) * TRADING_DAYS

    return alpha, beta


print("=" * 65)
print("Bluestock Mutual Fund Performance Analytics")
print("=" * 65)

if not NAV_FILE.exists():
    raise FileNotFoundError(f"NAV file not found: {NAV_FILE}")

nav = pd.read_csv(NAV_FILE)

nav["date"] = pd.to_datetime(nav["date"], errors="coerce")

if "amfi_code" not in nav.columns:
    raise ValueError(
        "amfi_code column not found in NAV data. "
        f"Available columns: {nav.columns.tolist()}"
    )

if "nav" not in nav.columns:
    raise ValueError(
        "nav column not found in NAV data. "
        f"Available columns: {nav.columns.tolist()}"
    )

nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")

nav = (
    nav.dropna(subset=["amfi_code", "date", "nav"])
       .sort_values(["amfi_code", "date"])
)

print(f"NAV records: {len(nav):,}")
print(f"Funds: {nav['amfi_code'].nunique()}")

nav["daily_return"] = (
    nav.groupby("amfi_code")["nav"]
       .pct_change()
)

daily_returns = nav[
    ["amfi_code", "date", "nav", "daily_return"]
].copy()

daily_returns.to_csv(
    REPORTS_DIR / "daily_returns.csv",
    index=False
)

if not BENCHMARK_FILE.exists():
    raise FileNotFoundError(
        f"Benchmark file not found: {BENCHMARK_FILE}"
    )

benchmark = pd.read_csv(BENCHMARK_FILE)

benchmark["date"] = pd.to_datetime(
    benchmark["date"],
    errors="coerce"
)

benchmark["close_value"] = pd.to_numeric(
    benchmark["close_value"],
    errors="coerce"
)

benchmark = benchmark[
    benchmark["index_name"].astype(str).str.upper() == "NIFTY100"
].copy()

benchmark = (
    benchmark.dropna(subset=["date", "close_value"])
             .sort_values("date")
)

benchmark["benchmark_return"] = benchmark["close_value"].pct_change()

benchmark_returns = benchmark.set_index("date")["benchmark_return"]

print(f"NIFTY100 benchmark records: {len(benchmark):,}")

scorecard = []

for amfi_code, group in nav.groupby("amfi_code"):

    group = group.sort_values("date").copy()

    returns = group["daily_return"].dropna()

    if len(group) == 0:
        continue

    latest_date = group["date"].max()

    latest_nav = group.iloc[-1]["nav"]

    cagr_values = {}

    for years in [1, 3, 5]:

        target_date = latest_date - pd.DateOffset(years=years)

        historical = group[group["date"] <= target_date]

        if len(historical) > 0:

            start_nav = historical.iloc[-1]["nav"]

            actual_days = (
                latest_date - historical.iloc[-1]["date"]
            ).days

            actual_years = actual_days / 365.25

            if actual_years > 0:
                cagr_values[f"cagr_{years}y"] = calculate_cagr(
                    start_nav,
                    latest_nav,
                    actual_years
                )
            else:
                cagr_values[f"cagr_{years}y"] = np.nan

        else:
            cagr_values[f"cagr_{years}y"] = np.nan

    if len(returns) > 1 and returns.std() != 0:

        sharpe = (
            (returns.mean() - RISK_FREE_DAILY)
            / returns.std()
        ) * np.sqrt(TRADING_DAYS)

    else:
        sharpe = np.nan

    downside_returns = returns[
        returns < RISK_FREE_DAILY
    ]

    if len(downside_returns) > 0:

        downside_deviation = np.sqrt(
            ((downside_returns - RISK_FREE_DAILY) ** 2).mean()
        )

        if downside_deviation != 0:

            sortino = (
                (returns.mean() - RISK_FREE_DAILY)
                / downside_deviation
            ) * np.sqrt(TRADING_DAYS)

        else:
            sortino = np.nan

    else:
        sortino = np.nan

    max_drawdown = calculate_max_drawdown(returns)

    fund_return_series = (
        group.set_index("date")["daily_return"]
    )

    alpha, beta = calculate_alpha_beta(
        fund_return_series,
        benchmark_returns
    )

    scorecard.append({
        "amfi_code": amfi_code,
        "cagr_1y": cagr_values.get("cagr_1y"),
        "cagr_3y": cagr_values.get("cagr_3y"),
        "cagr_5y": cagr_values.get("cagr_5y"),
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "alpha": alpha,
        "beta": beta,
        "max_drawdown": max_drawdown,
    })


scorecard = pd.DataFrame(scorecard)

if FUND_MASTER_FILE.exists():

    fund_master = pd.read_csv(FUND_MASTER_FILE)

    if "amfi_code" in fund_master.columns:

        possible_columns = [
            "amfi_code",
            "fund_name",
            "scheme_name",
            "fund_house",
            "category",
            "expense_ratio"
        ]

        available_columns = [
            col for col in possible_columns
            if col in fund_master.columns
        ]

        fund_master_small = fund_master[
            available_columns
        ].drop_duplicates("amfi_code")

        scorecard = scorecard.merge(
            fund_master_small,
            on="amfi_code",
            how="left"
        )


def percentile_score(series, higher_is_better=True):

    result = series.rank(
        pct=True,
        ascending=not higher_is_better
    )

    return result


scorecard["score_cagr"] = percentile_score(
    scorecard["cagr_3y"],
    higher_is_better=True
)

scorecard["score_sharpe"] = percentile_score(
    scorecard["sharpe_ratio"],
    higher_is_better=True
)

scorecard["score_alpha"] = percentile_score(
    scorecard["alpha"],
    higher_is_better=True
)

scorecard["score_drawdown"] = percentile_score(
    scorecard["max_drawdown"],
    higher_is_better=True
)

scorecard["fund_score"] = (
    scorecard["score_cagr"] * 0.35
    + scorecard["score_sharpe"] * 0.30
    + scorecard["score_alpha"] * 0.20
    + scorecard["score_drawdown"] * 0.15
)

alpha_beta_columns = [
    "amfi_code",
    "alpha",
    "beta"
]

scorecard[
    alpha_beta_columns
].to_csv(
    REPORTS_DIR / "alpha_beta.csv",
    index=False
)

scorecard.to_csv(
    REPORTS_DIR / "fund_scorecard.csv",
    index=False
)

print()
print("Created:")

print(f"  {REPORTS_DIR / 'daily_returns.csv'}")
print(f"  {REPORTS_DIR / 'alpha_beta.csv'}")
print(f"  {REPORTS_DIR / 'fund_scorecard.csv'}")

print()
print("Top scorecard rows:")

display_columns = [
    "amfi_code",
    "cagr_3y",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "beta",
    "max_drawdown",
    "fund_score"
]

print(
    scorecard[display_columns]
    .head(10)
    .to_string(index=False)
)

print()
print("Done.")