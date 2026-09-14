from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import DEFAULT_CODES, fund_labels, monte_carlo_projection, nav_matrix, optimize_portfolio


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
COLORS = ["#0f766e", "#f59e0b", "#2563eb", "#dc2626", "#7c3aed", "#0891b2"]


st.set_page_config(page_title="Bluestock MF Intelligence", page_icon="MF", layout="wide")


@st.cache_data
def load_data():
    return {
        "funds": pd.read_csv(RAW_DIR / "01_fund_master.csv"),
        "aum": pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"]),
        "sip": pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv", parse_dates=["month"]),
        "category_inflows": pd.read_csv(RAW_DIR / "05_category_inflows.csv", parse_dates=["month"]),
        "folios": pd.read_csv(RAW_DIR / "06_industry_folio_count.csv", parse_dates=["month"]),
        "performance": pd.read_csv(PROCESSED_DIR / "07_scheme_performance_clean.csv"),
        "scorecard": pd.read_csv(PROCESSED_DIR / "fund_scorecard.csv"),
        "transactions": pd.read_csv(PROCESSED_DIR / "08_investor_transactions_clean.csv", parse_dates=["transaction_date"]),
        "benchmark": pd.read_csv(RAW_DIR / "10_benchmark_indices.csv", parse_dates=["date"]),
    }


def money(value):
    return f"{value:,.0f} cr"


def metric_row(metrics):
    columns = st.columns(len(metrics))
    for column, (label, value, delta) in zip(columns, metrics):
        column.metric(label, value, delta)


def chart_layout(fig, height=360):
    fig.update_layout(height=height, margin={"l": 10, "r": 10, "t": 45, "b": 10}, hovermode="x unified")
    return fig


def industry_overview(data):
    st.header("Industry Overview")
    st.caption("AUM, flows, folios, and scheme scale across the mutual fund industry")
    aum = data["aum"]
    sip = data["sip"]
    folios = data["folios"]
    funds = data["funds"]
    latest_aum = aum[aum["date"] == aum["date"].max()]
    latest_sip = sip.sort_values("month").iloc[-1]
    latest_folios = folios.sort_values("month").iloc[-1]
    metric_row([
        ("Total AUM", money(latest_aum["fund_house_aum_crore"].sum()), "Latest reported"),
        ("Monthly SIP inflow", money(latest_sip["sip_inflow_crore"]), f"{latest_sip['yoy_growth_pct']:.1f}% YoY"),
        ("Total folios", f"{latest_folios['total_folios_crore']:.2f} cr", "Latest reported"),
        ("Number of schemes", f"{len(funds):,}", f"{funds['fund_house'].nunique()} fund houses"),
    ])
    left, right = st.columns(2)
    with left:
        latest_house = aum[aum["date"] == aum["date"].max()].sort_values("fund_house_aum_crore", ascending=False)
        st.plotly_chart(chart_layout(px.bar(latest_house, x="fund_house_aum_crore", y="fund_house", orientation="h", title="Fund-house AUM", color_discrete_sequence=[COLORS[0]])), width="stretch")
    with right:
        trend = aum.groupby("date", as_index=False)["fund_house_aum_crore"].sum()
        st.plotly_chart(chart_layout(px.line(trend, x="date", y="fund_house_aum_crore", title="Industry AUM trend", color_discrete_sequence=[COLORS[2]])), width="stretch")
    sip_trend = sip.sort_values("month")
    st.plotly_chart(chart_layout(px.line(sip_trend, x="month", y="sip_inflow_crore", title="SIP inflow trend", color_discrete_sequence=[COLORS[1]])), width="stretch")


def fund_performance(data):
    st.header("Fund Performance")
    st.caption("Filter the universe, compare risk-adjusted returns, and inspect the scorecard")
    performance = data["performance"].copy()
    scorecard = data["scorecard"]
    filters = st.columns(3)
    house = filters[0].selectbox("Fund house", ["All"] + sorted(performance["fund_house"].dropna().unique()))
    category = filters[1].selectbox("Category", ["All"] + sorted(performance["category"].dropna().unique()))
    schemes = ["All"] + sorted(performance["scheme_name"].dropna().unique())
    scheme = filters[2].selectbox("Scheme", schemes)
    filtered = performance.copy()
    if house != "All":
        filtered = filtered[filtered["fund_house"] == house]
    if category != "All":
        filtered = filtered[filtered["category"] == category]
    if scheme != "All":
        filtered = filtered[filtered["scheme_name"] == scheme]
    if filtered.empty:
        st.warning("No schemes match the selected filters.")
        return
    top = filtered.sort_values("sharpe_ratio", ascending=False).iloc[0]
    metric_row([
        ("3-year CAGR", f"{top['return_3yr_pct']:.2f}%", top["scheme_name"][:28]),
        ("Sharpe ratio", f"{top['sharpe_ratio']:.2f}", "Top filtered scheme"),
        ("Alpha", f"{top['alpha']:.2f}", "Percentage points"),
        ("Maximum drawdown", f"{top['max_drawdown_pct']:.2f}%", "Top filtered scheme"),
    ])
    left, right = st.columns(2)
    with left:
        scatter = px.scatter(filtered, x="std_dev_ann_pct", y="return_3yr_pct", size="scheme_aum_crore", color="risk_grade", hover_name="scheme_name", title="Return vs risk", labels={"std_dev_ann_pct": "Annualized volatility %", "return_3yr_pct": "3-year return %"}, color_discrete_sequence=COLORS)
        st.plotly_chart(chart_layout(scatter), width="stretch")
    with right:
        score_view = scorecard[scorecard["amfi_code"].isin(filtered["amfi_code"])] if "amfi_code" in scorecard else scorecard
        score_view = score_view.sort_values("overall_rank").head(10)
        st.plotly_chart(chart_layout(px.bar(score_view, x="overall_score", y="scheme_name", orientation="h", title="Top fund scorecard", color="overall_score", color_continuous_scale="Tealgrn")), width="stretch")
    st.dataframe(filtered[["scheme_name", "fund_house", "category", "return_3yr_pct", "sharpe_ratio", "alpha", "max_drawdown_pct", "risk_grade"]].sort_values("sharpe_ratio", ascending=False), hide_index=True, width="stretch")


def investor_analytics(data):
    st.header("Investor Analytics")
    st.caption("Transaction volumes, investor segments, geography, and payment behavior")
    transactions = data["transactions"].copy()
    total = transactions["amount_inr"].sum()
    sip_rows = transactions[transactions["transaction_type"].astype(str).str.contains("SIP", case=False, na=False)]
    metric_row([
        ("Total transactions", f"{len(transactions):,}", "All records"),
        ("Invested amount", f"₹{total / 1e7:,.2f} cr", "All transaction types"),
        ("SIP transactions", f"{len(sip_rows):,}", f"{len(sip_rows) / len(transactions):.1%} of records"),
        ("Unique investors", f"{transactions['investor_id'].nunique():,}", "Distinct investor IDs"),
    ])
    left, right = st.columns(2)
    with left:
        state = transactions.groupby("state", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=False).head(12)
        st.plotly_chart(chart_layout(px.bar(state, x="amount_inr", y="state", orientation="h", title="State-wise investment", color_discrete_sequence=[COLORS[2]])), width="stretch")
    with right:
        age = transactions.groupby("age_group", as_index=False)["amount_inr"].sum()
        st.plotly_chart(chart_layout(px.bar(age, x="age_group", y="amount_inr", title="Investment by age group", color_discrete_sequence=[COLORS[4]])), width="stretch")
    left, right = st.columns(2)
    with left:
        types = transactions["transaction_type"].value_counts().reset_index(name="transactions")
        st.plotly_chart(chart_layout(px.pie(types, names="transaction_type", values="transactions", title="Transaction types", color_discrete_sequence=COLORS)), width="stretch")
    with right:
        monthly = transactions.set_index("transaction_date").resample("ME")["amount_inr"].sum().reset_index()
        st.plotly_chart(chart_layout(px.line(monthly, x="transaction_date", y="amount_inr", title="Monthly investment value", color_discrete_sequence=[COLORS[0]])), width="stretch")


def sip_market_trends(data):
    st.header("SIP & Market Trends")
    st.caption("Monthly flows, category allocation, and benchmark context")
    sip = data["sip"].sort_values("month")
    categories = data["category_inflows"].sort_values("month")
    benchmark = data["benchmark"].copy()
    metric_row([
        ("Latest SIP inflow", money(sip.iloc[-1]["sip_inflow_crore"]), f"{sip.iloc[-1]['yoy_growth_pct']:.1f}% YoY"),
        ("Active SIP accounts", f"{sip.iloc[-1]['active_sip_accounts_crore']:.2f} cr", "Latest month"),
        ("Category inflow", money(categories.groupby("category").tail(1)["net_inflow_crore"].sum()), "Latest month total"),
        ("Benchmark series", f"{benchmark['index_name'].nunique():,}", "Indices available"),
    ])
    st.plotly_chart(chart_layout(px.line(sip, x="month", y=["sip_inflow_crore", "sip_aum_lakh_crore"], title="SIP inflow and SIP AUM trends")), width="stretch")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(chart_layout(px.area(categories, x="month", y="net_inflow_crore", color="category", title="Category inflows", color_discrete_sequence=COLORS)), width="stretch")
    with right:
        selected_index = st.selectbox("Benchmark", sorted(benchmark["index_name"].unique()))
        benchmark_view = benchmark[benchmark["index_name"] == selected_index].sort_values("date")
        st.plotly_chart(chart_layout(px.line(benchmark_view, x="date", y="close_value", title=f"{selected_index} monthly trend", color_discrete_sequence=[COLORS[2]])), width="stretch")


def nav_detail(data, selected_codes):
    st.header("NAV Detail")
    st.caption("Historical NAV, five-year Monte Carlo projection, and portfolio optimization")
    labels = data["performance"].set_index("amfi_code")["scheme_name"].to_dict()
    fund_code = st.selectbox("Select a mutual fund", selected_codes, format_func=lambda code: labels.get(code, str(code)))
    prices = nav_matrix(selected_codes)
    prices.index = pd.to_datetime(prices.index, errors="coerce")
    prices = prices.loc[prices.index.notna()].sort_index()
    history = prices[fund_code].loc["2022-07-01":"2026-08-31"]
    projection = monte_carlo_projection(history)
    performance = data["performance"].set_index("amfi_code").loc[fund_code]
    metric_row([
        ("1-year return", f"{performance['return_1yr_pct']:.2f}%", "Fund performance"),
        ("3-year return", f"{performance['return_3yr_pct']:.2f}%", "Fund performance"),
        ("Sharpe ratio", f"{performance['sharpe_ratio']:.2f}", "Risk adjusted"),
        ("Risk grade", str(performance["risk_grade"]), "Fund classification"),
    ])
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=history.index, y=history, name="Actual NAV", line={"color": COLORS[1], "width": 2}))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["upper_95"], line={"width": 0}, showlegend=False))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["lower_5"], fill="tonexty", line={"width": 0}, name="90% uncertainty band"))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["median"], name="Median projection", line={"color": COLORS[0], "width": 2}))
    st.plotly_chart(chart_layout(chart, 500), width="stretch")
    st.subheader("Efficient frontier for selected funds")
    result = optimize_portfolio(selected_codes)
    left, right = st.columns(2)
    left.metric("Expected annual return", f"{result['expected_return_pct']:.2f}%")
    right.metric("Portfolio Sharpe", f"{result['sharpe_ratio']:.2f}")
    weights = result["weights"].copy()
    weights["fund"] = weights["amfi_code"].map(labels)
    st.dataframe(weights[["fund", "weight_pct", "expected_return_pct"]].rename(columns={"weight_pct": "Weight %", "expected_return_pct": "Expected return %"}), hide_index=True, width="stretch")
    frontier = result["frontier"]
    st.plotly_chart(chart_layout(px.line(frontier, x="volatility_pct", y="return_pct", markers=True, title="Efficient frontier", labels={"volatility_pct": "Annualized volatility %", "return_pct": "Annualized return %"})), width="stretch")


data = load_data()
st.sidebar.title("Bluestock MF")
st.sidebar.caption("Mutual fund intelligence workspace")
page = st.sidebar.radio("Navigate", ["Industry Overview", "Fund Performance", "Investor Analytics", "SIP & Market Trends", "NAV Detail"])
selected_codes = st.sidebar.multiselect("Funds for NAV and portfolio", DEFAULT_CODES, default=DEFAULT_CODES[:5], max_selections=5)
if len(selected_codes) < 2:
    st.sidebar.warning("Select at least two funds for portfolio analytics.")
    selected_codes = DEFAULT_CODES[:2]

if page == "Industry Overview":
    industry_overview(data)
elif page == "Fund Performance":
    fund_performance(data)
elif page == "Investor Analytics":
    investor_analytics(data)
elif page == "SIP & Market Trends":
    sip_market_trends(data)
else:
    nav_detail(data, selected_codes)


st.set_page_config(page_title="Bluestock MF Analytics", page_icon="MF", layout="wide")
st.title("Bluestock MF Analytics")
st.caption("Live NAV intelligence, five-year projections, and portfolio construction")

labels = fund_labels(DEFAULT_CODES)
code_options = {f"{code} | {labels.get(code, code)}": code for code in DEFAULT_CODES}
selected_labels = st.sidebar.multiselect("Funds for analysis", list(code_options), default=list(code_options)[:5], max_selections=5)
selected_codes = [code_options[label] for label in selected_labels]

if len(selected_codes) < 2:
    st.info("Select at least two funds to view portfolio analytics.")
    st.stop()

prices = nav_matrix(selected_codes)
prices.index = pd.to_datetime(prices.index, errors="coerce")
prices = prices.loc[prices.index.notna()].sort_index()
tab_projection, tab_portfolio = st.tabs(["NAV projection", "Efficient frontier"])

with tab_projection:
    fund_code = st.selectbox("Fund to project", selected_codes, format_func=lambda code: labels.get(code, str(code)))
    history_start = pd.Timestamp("2022-07-01")
    history_end = pd.Timestamp("2026-08-31")
    fund_history = prices[fund_code].loc[history_start:history_end]
    projection = monte_carlo_projection(fund_history)
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=fund_history.index, y=fund_history, line={"color": "#f59e0b", "width": 2}, name="Actual NAV"))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["upper_95"], line={"width": 0}, showlegend=False))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["lower_5"], fill="tonexty", line={"width": 0}, name="90% uncertainty band"))
    chart.add_trace(go.Scatter(x=projection["date"], y=projection["median"], line={"color": "#0f766e", "width": 2}, name="Median projection"))
    chart.update_layout(height=500, xaxis_title="Date", yaxis_title="Projected NAV", hovermode="x unified")
    st.plotly_chart(chart, width="stretch")

with tab_portfolio:
    result = optimize_portfolio(selected_codes)
    left, right = st.columns(2)
    left.metric("Expected annual return", f"{result['expected_return_pct']:.2f}%")
    right.metric("Portfolio Sharpe", f"{result['sharpe_ratio']:.2f}")
    st.subheader("Maximum-Sharpe allocation")
    weights = result["weights"].copy()
    weights["fund"] = weights["amfi_code"].map(labels)
    st.dataframe(weights[["fund", "weight_pct", "expected_return_pct"]].rename(columns={"weight_pct": "Weight %", "expected_return_pct": "Expected return %"}), hide_index=True, width="stretch")
    frontier = result["frontier"]
    frontier_chart = go.Figure(go.Scatter(x=frontier["volatility_pct"], y=frontier["return_pct"], mode="lines+markers", name="Efficient frontier"))
    frontier_chart.update_layout(height=420, xaxis_title="Annualized volatility %", yaxis_title="Annualized return %")
    st.plotly_chart(frontier_chart, width="stretch")