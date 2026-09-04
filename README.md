# Day 1 — Data Quality Summary
* Fund master contains **40 schemes** across **10 fund houses**.
* **34 schemes are Equity** and **6 are Debt**.
* **Large Cap** is the largest sub-category with 14 schemes.
* **Moderate** is the largest risk category with 16 schemes.
* All **40 AMFI codes** in the fund master are present in the NAV history. No missing or extra codes were found.
* Live MFAPI data was successfully fetched, but **5 of 6 codes returned different scheme details** from the supplied fund master. The original project data was kept unchanged.
