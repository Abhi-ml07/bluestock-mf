SELECT scheme_name, fund_house, aum_crore FROM fact_performance
ORDER BY aum_crore DESC LIMIT 5;

SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(nav), 2) AS average_nav FROM fact_nav
GROUP BY strftime('%Y-%m', date) ORDER BY month;

SELECT month, sip_inflow_crore, yoy_growth_pct FROM fact_sip ORDER BY month;

SELECT state,COUNT(*) AS transaction_count, ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions GROUP BY state ORDER BY transaction_count DESC;

SELECT dim_fund.scheme_name, dim_fund.fund_house, dim_fund.category, dim_fund.expense_ratio_pct, fact_performance.aum_crore
FROM dim_fund JOIN fact_performance ON dim_fund.amfi_code = fact_performance.amfi_code
WHERE dim_fund.expense_ratio_pct < 1.0 ORDER BY dim_fund.expense_ratio_pct DESC;

SELECT scheme_name, fund_house, return_3yr_pct, benchmark_3yr_pct, alpha FROM fact_performance
WHERE return_3yr_pct > benchmark_3yr_pct ORDER BY alpha DESC LIMIT 10;

SELECT scheme_name, fund_house, sharpe_ratio, risk_grade FROM fact_performance
ORDER BY sharpe_ratio DESC LIMIT 10;

SELECT transaction_type, COUNT(*) AS transaction_count, ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions GROUP BY transaction_type ORDER BY total_amount_inr DESC;

SELECT risk_category, COUNT(*) AS fund_count, SUM(aum_crore) AS total_aum_crore FROM dim_fund JOIN fact_performance ON dim_fund.amfi_code = fact_performance.amfi_code
GROUP BY risk_category ORDER BY total_aum_crore DESC;


SELECT dim_fund.fund_house, COUNT(*) AS scheme_count, ROUND(SUM(fact_performance.aum_crore), 2) AS total_aum_crore
FROM dim_fund JOIN fact_performance ON dim_fund.amfi_code = fact_performance.amfi_code GROUP BY dim_fund.fund_house
ORDER BY total_aum_crore DESC;