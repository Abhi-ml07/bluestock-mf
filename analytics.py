from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize


PROJECT_ROOT = Path(__file__).resolve().parent
NAV_FILE = PROJECT_ROOT / "data" / "processed" / "02_nav_history_clean.csv"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PERFORMANCE_FILE = PROJECT_ROOT / "data" / "processed" / "07_scheme_performance_clean.csv"
DEFAULT_CODES = [125497, 119551, 120503, 118632, 119092, 120841]


def load_nav_history(codes=None):
    codes = codes or DEFAULT_CODES
    live_sources = [(code, next(RAW_DATA_DIR.glob(f"{code}_*_live_nav.csv"), None)) for code in codes]
    live_sources = [(code, path) for code, path in live_sources if path is not None]
    if live_sources:
        frames = []
        for code, path in live_sources:
            frame = pd.read_csv(path)
            frame["amfi_code"] = code
            frames.append(frame)
        nav = pd.concat(frames, ignore_index=True)
    else:
        nav = pd.read_csv(NAV_FILE, parse_dates=["date"])
    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["amfi_code"] = pd.to_numeric(nav["amfi_code"], errors="coerce").astype("Int64")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    return nav[
        nav["amfi_code"].isin(codes) & nav["nav"].gt(0)
    ].dropna(subset=["date", "nav"])


def nav_matrix(codes=None):
    nav = load_nav_history(codes)
    matrix = nav.pivot_table(index="date", columns="amfi_code", values="nav", aggfunc="last")
    return matrix.sort_index().ffill().dropna(axis=1, how="all").dropna()


def monte_carlo_projection(series, years=5, simulations=2000, seed=42):
    values = pd.Series(series).dropna().astype(float)
    if len(values) < 30 or values.iloc[-1] <= 0:
        raise ValueError("At least 30 positive NAV observations are required.")

    daily_returns = values.pct_change().dropna()
    rng = np.random.default_rng(seed)
    periods = years * 252
    drift = daily_returns.mean()
    volatility = daily_returns.std()
    shocks = rng.normal(size=(periods, simulations))
    paths = values.iloc[-1] * np.exp(
        np.cumsum((drift - 0.5 * volatility**2) + volatility * shocks, axis=0)
    )
    if isinstance(values.index, pd.DatetimeIndex):
        forecast_start = values.index.max()
    else:
        forecast_start = pd.Timestamp.today().normalize()
    dates = pd.bdate_range(forecast_start, periods=periods + 1)[1:]
    return pd.DataFrame({
        "date": dates,
        "lower_5": np.percentile(paths, 5, axis=1),
        "median": np.percentile(paths, 50, axis=1),
        "upper_95": np.percentile(paths, 95, axis=1),
    })


def optimize_portfolio(codes, risk_free_rate=0.06):
    prices = nav_matrix(codes)
    returns = prices.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if returns.empty or len(prices.columns) < 2:
        raise ValueError("At least two funds with valid overlapping NAV history are required.")
    annual_returns = returns.mean() * 252
    annual_covariance = returns.cov() * 252
    count = len(prices.columns)
    initial = np.repeat(1 / count, count)

    def portfolio_stats(weights):
        expected = float(weights @ annual_returns)
        volatility = float(np.sqrt(weights @ annual_covariance @ weights))
        sharpe = (expected - risk_free_rate) / volatility if volatility else 0.0
        return expected, volatility, sharpe

    result = minimize(
        lambda weights: -portfolio_stats(weights)[2], initial, method="SLSQP",
        bounds=[(0, 1)] * count,
        constraints={"type": "eq", "fun": lambda weights: weights.sum() - 1},
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not result.success:
        raise RuntimeError(f"Portfolio optimization failed: {result.message}")

    expected, volatility, sharpe = portfolio_stats(result.x)
    weights = pd.DataFrame({"amfi_code": prices.columns.astype(int), "weight": result.x})
    weights["weight_pct"] = weights["weight"] * 100
    weights["expected_return_pct"] = weights["amfi_code"].map(annual_returns) * 100

    targets = np.linspace(annual_returns.min(), annual_returns.max(), 25)
    frontier = []
    for target in targets:
        frontier_result = minimize(
            lambda weights: weights @ annual_covariance @ weights, initial, method="SLSQP",
            bounds=[(0, 1)] * count,
            constraints=[
                {"type": "eq", "fun": lambda weights: weights.sum() - 1},
                {"type": "eq", "fun": lambda weights, target=target: weights @ annual_returns - target},
            ],
        )
        if frontier_result.success:
            frontier.append({"return_pct": target * 100, "volatility_pct": np.sqrt(frontier_result.fun) * 100})

    return {"weights": weights.sort_values("weight", ascending=False), "frontier": pd.DataFrame(frontier),
            "expected_return_pct": expected * 100, "volatility_pct": volatility * 100,
            "sharpe_ratio": sharpe, "prices": prices}


def fund_labels(codes):
    performance = pd.read_csv(PERFORMANCE_FILE)
    return performance.set_index("amfi_code").loc[list(codes), "scheme_name"].to_dict()