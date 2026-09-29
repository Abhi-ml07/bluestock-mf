from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PALETTE = ["#0f766e", "#2563eb", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"]


st.set_page_config(page_title="Mutual Fund Dashboard", page_icon="MF", layout="wide")


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
		"nav": pd.read_csv(PROCESSED_DIR / "02_nav_history_clean.csv", parse_dates=["date"]),
	}


def money_crore(value):
	return f"₹{value:,.0f} Cr"


def metrics(items):
	columns = st.columns(len(items))
	for column, (label, value, note) in zip(columns, items):
		column.metric(label, value, note)


def chart(fig, height=360):
	fig.update_layout(height=height, margin={"l": 10, "r": 10, "t": 50, "b": 10}, hovermode="x unified")
	st.plotly_chart(fig, use_container_width=True)


def industry_overview(data):
	st.header("Industry Overview")
	st.caption("AUM, flows, folio growth, and scheme scale")
	latest_aum = data["aum"].loc[data["aum"]["date"].idxmax()]
	latest_aum_rows = data["aum"][data["aum"]["date"] == data["aum"]["date"].max()]
	latest_sip = data["sip"].sort_values("month").iloc[-1]
	latest_folios = data["folios"].sort_values("month").iloc[-1]
	metrics([
		("Total AUM", money_crore(latest_aum_rows["fund_house_aum_crore"].sum()), "Latest reported"),
		("SIP inflows", money_crore(latest_sip["sip_inflow_crore"]), f"{latest_sip['yoy_growth_pct']:.1f}% YoY"),
		("Folios", f"{latest_folios['total_folios_crore']:.2f} Cr", "Latest reported"),
		("Schemes", f"{len(data['funds']):,}", f"{data['funds']['fund_house'].nunique()} fund houses"),
	])
	left, right = st.columns(2)
	with left:
		latest_house = latest_aum_rows.sort_values("fund_house_aum_crore", ascending=False)
		chart(px.bar(latest_house, x="fund_house_aum_crore", y="fund_house", orientation="h", title="Fund-house AUM", color_discrete_sequence=[PALETTE[0]]))
	with right:
		trend = data["aum"].groupby("date", as_index=False)["fund_house_aum_crore"].sum()
		chart(px.line(trend, x="date", y="fund_house_aum_crore", title="Industry AUM trend", color_discrete_sequence=[PALETTE[1]]))
	chart(px.line(data["folios"].sort_values("month"), x="month", y=["total_folios_crore", "equity_folios_crore", "debt_folios_crore"], title="Industry folio trends"))


def fund_performance(data):
	st.header("Fund Performance")
	st.caption("Compare schemes by fund house, category, return, and risk")
	performance = data["performance"]
	filters = st.columns(3)
	house = filters[0].selectbox("Fund house", ["All"] + sorted(performance["fund_house"].unique()))
	category = filters[1].selectbox("Category", ["All"] + sorted(performance["category"].unique()))
	scheme = filters[2].selectbox("Scheme", ["All"] + sorted(performance["scheme_name"].unique()))
	filtered = performance.copy()
	if house != "All":
		filtered = filtered[filtered["fund_house"] == house]
	if category != "All":
		filtered = filtered[filtered["category"] == category]
	if scheme != "All":
		filtered = filtered[filtered["scheme_name"] == scheme]
	if filtered.empty:
		st.warning("No funds match these filters.")
		return
	top = filtered.sort_values("sharpe_ratio", ascending=False).iloc[0]
	metrics([
		("3-year CAGR", f"{top['return_3yr_pct']:.2f}%", top["scheme_name"][:25]),
		("Sharpe ratio", f"{top['sharpe_ratio']:.2f}", "Highest in selection"),
		("Alpha", f"{top['alpha']:.2f}", "Percentage points"),
		("Maximum drawdown", f"{top['max_drawdown_pct']:.2f}%", "Highest-ranked selection"),
	])
	left, right = st.columns(2)
	with left:
		chart(px.scatter(filtered, x="std_dev_ann_pct", y="return_3yr_pct", color="risk_grade", size="scheme_aum_crore", hover_name="scheme_name", title="Return vs risk", labels={"std_dev_ann_pct": "Volatility %", "return_3yr_pct": "3-year return %"}, color_discrete_sequence=PALETTE))
	with right:
		scorecard = data["scorecard"]
		scorecard = scorecard[scorecard["amfi_code"].isin(filtered["amfi_code"])].sort_values("overall_rank").head(10)
		chart(px.bar(scorecard, x="overall_score", y="scheme_name", orientation="h", color="overall_score", title="Fund scorecard", color_continuous_scale="Tealgrn"))
	st.dataframe(filtered[["scheme_name", "fund_house", "category", "return_3yr_pct", "sharpe_ratio", "alpha", "max_drawdown_pct", "risk_grade"]].sort_values("sharpe_ratio", ascending=False), hide_index=True, use_container_width=True)


def investor_analytics(data):
	st.header("Investor Analytics")
	st.caption("Transaction activity, investor geography, and age segments")
	transactions = data["transactions"]
	sip = transactions[transactions["transaction_type"].str.contains("SIP", case=False, na=False)]
	metrics([
		("Total transactions", f"{len(transactions):,}", "All records"),
		("SIP transactions", f"{len(sip):,}", f"{len(sip) / len(transactions):.1%} of total"),
		("Invested amount", f"₹{transactions['amount_inr'].sum() / 1e7:,.2f} Cr", "All transactions"),
		("Unique investors", f"{transactions['investor_id'].nunique():,}", "Distinct IDs"),
	])
	left, right = st.columns(2)
	with left:
		state = transactions.groupby("state", as_index=False)["amount_inr"].sum().nlargest(12, "amount_inr")
		chart(px.bar(state, x="amount_inr", y="state", orientation="h", title="State-wise investment", color_discrete_sequence=[PALETTE[1]]))
	with right:
		age = transactions.groupby("age_group", as_index=False)["amount_inr"].sum()
		chart(px.bar(age, x="age_group", y="amount_inr", title="Age-group analysis", color_discrete_sequence=[PALETTE[4]]))
	left, right = st.columns(2)
	with left:
		types = transactions["transaction_type"].value_counts().rename_axis("transaction_type").reset_index(name="count")
		chart(px.pie(types, names="transaction_type", values="count", title="Transaction types", color_discrete_sequence=PALETTE))
	with right:
		monthly = transactions.set_index("transaction_date").resample("ME")["amount_inr"].sum().reset_index()
		chart(px.line(monthly, x="transaction_date", y="amount_inr", title="Monthly investment value", color_discrete_sequence=[PALETTE[0]]))


def sip_market_trends(data):
	st.header("SIP & Market Trends")
	st.caption("SIP momentum, category flows, and NIFTY benchmark context")
	sip = data["sip"].sort_values("month")
	categories = data["category_inflows"].sort_values("month")
	benchmark = data["benchmark"]
	indices = sorted(benchmark["index_name"].unique())
	nifty = next((name for name in indices if "NIFTY" in name.upper()), indices[0])
	latest = sip.iloc[-1]
	metrics([
		("Latest SIP inflow", money_crore(latest["sip_inflow_crore"]), f"{latest['yoy_growth_pct']:.1f}% YoY"),
		("Active SIP accounts", f"{latest['active_sip_accounts_crore']:.2f} Cr", "Latest month"),
		("Category net inflow", money_crore(categories.groupby("category").tail(1)["net_inflow_crore"].sum()), "Latest month"),
		("NIFTY series", nifty, "Selected by default"),
	])
	chart(px.line(sip, x="month", y=["sip_inflow_crore", "sip_aum_lakh_crore"], title="SIP inflow and AUM trends"))
	left, right = st.columns(2)
	with left:
		chart(px.area(categories, x="month", y="net_inflow_crore", color="category", title="Category inflows", color_discrete_sequence=PALETTE))
	with right:
		selected = st.selectbox("Benchmark index", indices, index=indices.index(nifty))
		view = benchmark[benchmark["index_name"] == selected].sort_values("date")
		chart(px.line(view, x="date", y="close_value", title=f"{selected} monthly trend", color_discrete_sequence=[PALETTE[1]]))


def nav_detail(data):
	st.header("NAV Detail")
	st.caption("Select a mutual fund to inspect historical NAV and performance metrics")
	performance = data["performance"]
	labels = performance.set_index("amfi_code")["scheme_name"].to_dict()
	codes = sorted(performance["amfi_code"].unique())
	selected = st.selectbox("Select a mutual fund", codes, format_func=lambda code: labels.get(code, str(code)))
	history = data["nav"][data["nav"]["amfi_code"] == selected].sort_values("date")
	selected_metrics = performance.set_index("amfi_code").loc[selected]
	metrics([
		("1-year return", f"{selected_metrics['return_1yr_pct']:.2f}%", "Fund performance"),
		("3-year CAGR", f"{selected_metrics['return_3yr_pct']:.2f}%", "Fund performance"),
		("Sharpe ratio", f"{selected_metrics['sharpe_ratio']:.2f}", "Risk adjusted"),
		("Maximum drawdown", f"{selected_metrics['max_drawdown_pct']:.2f}%", "Historical"),
	])
	chart(px.line(history, x="date", y="nav", title=f"NAV history: {labels.get(selected, selected)}", labels={"nav": "NAV", "date": "Date"}, color_discrete_sequence=[PALETTE[0]]), 500)
	st.dataframe(history.tail(20).sort_values("date", ascending=False), hide_index=True, use_container_width=True)


data = load_data()
st.sidebar.title("Mutual Fund Dashboard")
page = st.sidebar.radio("Dashboard section", ["Industry Overview", "Fund Performance", "Investor Analytics", "SIP & Market Trends", "NAV Detail"])
st.sidebar.caption("Power BI companion built from the project data model")

if page == "Industry Overview":
	industry_overview(data)
elif page == "Fund Performance":
	fund_performance(data)
elif page == "Investor Analytics":
	investor_analytics(data)
elif page == "SIP & Market Trends":
	sip_market_trends(data)
else:
	nav_detail(data)
