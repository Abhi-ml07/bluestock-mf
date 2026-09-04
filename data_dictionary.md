# Data Dictionary

This project contains 10 datasets related to mutual funds, investors, fund performance, AUM, SIPs, and market benchmarks.

## 1. Fund Master

- Contains basic information about all mutual fund schemes.
- amfi_code – Unique identification code for each mutual fund scheme.
- fund_house – Name of the company managing the fund.
- scheme_name – Name of the mutual fund scheme.
- category – Main fund category such as Equity or Debt.
- sub_category – Detailed category such as Large Cap, Mid Cap, Small Cap, etc.
- plan – Shows whether the fund is Direct or Regular.
- launch_date – Date when the scheme was launched.
- benchmark – Index used to compare the fund's performance.
- expense_ratio_pct – Annual expense charged by the fund.
- risk_category – Risk level associated with the fund.

## 2. NAV History

- Contains historical daily NAV information for mutual fund schemes.
- amfi_code – Identifies the mutual fund scheme.
- date – Date of the NAV value.
- nav – Net Asset Value of the fund on that date.

## 3. AUM by Fund House

- Shows how much money is managed by different fund houses.
- date – Date of the AUM record.
- fund_house – Name of the fund house.
- aum_lakh_crore – Total AUM expressed in lakh crore.
- aum_crore – Total AUM expressed in crore.
- num_schemes – Number of schemes managed by the fund house.

## 4. Monthly SIP Inflows

- Contains monthly information about SIP investments.
- month – Month for which the data is recorded.
- sip_inflow_crore – Total SIP money received during the month.
- active_sip_accounts_crore – Number of active SIP accounts.
- new_sip_accounts_lakh – Number of new SIP accounts.
- sip_aum_lakh_crore – AUM generated through SIPs.
- yoy_growth_pct – SIP growth compared with the same period of the previous year.

## 5. Category Inflows

- Shows monthly investment inflows for different mutual fund categories.
- month – Month of the record.
- category – Mutual fund category.
- net_inflow_crore – Net money invested into the category.

## 6. Industry Folio Count

- Shows the number of mutual fund folios across different categories.
- month – Month of the record.
- total_folios_crore – Total number of folios.
- equity_folios_crore – Number of equity folios.
- debt_folios_crore – Number of debt folios.
- hybrid_folios_crore – Number of hybrid folios.
- others_folios_crore – Number of folios in other categories.

## 7. Scheme Performance

- Contains return and risk information for each mutual fund.
- amfi_code – Identifies the fund.
- scheme_name – Name of the fund.
- return_1yr_pct – Fund return over one year.
- return_3yr_pct – Fund return over three years.
- return_5yr_pct – Fund return over five years.
- benchmark_3yr_pct – Benchmark return over three years.
- alpha – Shows the fund's excess performance.
- beta – Shows how much the fund moves compared with the market.
- sharpe_ratio – Measures return compared with the risk taken.
- sortino_ratio – Measures return compared with downside risk.
- std_dev_ann_pct – Measures the volatility of the fund.
- max_drawdown_pct – Largest fall in fund value from a previous peak.
- aum_crore – Assets managed by the fund in crore.
- expense_ratio_pct – Annual expense ratio of the fund.
- morningstar_rating – Rating given to the fund.
- risk_grade – Risk grade of the fund.
- anomaly_flag – Used to identify unusually high performance metrics.

## 8. Investor Transactions

- Contains transaction-level information about investors.
- investor_id – Unique identifier for an investor.
- transaction_date – Date of the transaction.
- amfi_code – Identifies the mutual fund involved.
- transaction_type – Type of transaction such as SIP, Lumpsum, or Redemption.
- amount_inr – Transaction amount in Indian rupees.
- state – Investor's state.
- city – Investor's city.
- city_tier – Tier classification of the city.
- age_group – Age group of the investor.
- gender – Gender information.
- annual_income_lakh – Annual income in lakh rupees.
- payment_mode – Method used for the transaction.
- kyc_status – KYC verification status.

## 9. Portfolio Holdings

- Shows the stocks held inside different mutual fund schemes.
- amfi_code – Identifies the mutual fund.
- stock_symbol – Stock market symbol.
- stock_name – Name of the stock.
- sector – Sector in which the stock operates.
- weight_pct – Percentage of the portfolio invested in the stock.
- market_value_cr – Value of the holding in crore.
- current_price_inr – Current price of the stock.
- portfolio_date – Date of the portfolio data.

## 10. Benchmark Indices

- Contains historical values of market benchmark indices.
- date – Date of the index value.
- index_name – Name of the benchmark index.
- close_value – Closing value of the index.

## Database Tables

- dim_fund – Stores information about mutual fund schemes.
- dim_date – Stores calendar and date-related information.
- dim_fund_house – Stores fund house information.
- fact_nav – Stores daily NAV records.
- fact_transactions – Stores investor transactions.
- fact_performance – Stores fund returns and risk metrics.
- fact_aum – Stores fund house AUM information.
- fact_sip – Stores monthly SIP statistics.

## Data Cleaning Done

- Converted date columns into proper date format.
- Checked missing values and duplicate records.
- Checked NAV values to make sure they were positive.
- Checked transaction amounts for invalid values.
- Verified transaction types and KYC statuses.
- Checked expense ratios for unusual values.
- Added an anomaly flag for unusual Sharpe and Sortino ratios.
- Kept the original source values unchanged wherever possible.