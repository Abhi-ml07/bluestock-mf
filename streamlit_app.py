import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from analytics import DEFAULT_CODES, fund_labels, monte_carlo_projection, nav_matrix, optimize_portfolio


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