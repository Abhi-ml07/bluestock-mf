import pandas as pd

def recommend_funds(performance, risk_appetite):
    recommended_funds = performance[
        performance["risk_grade"] == risk_appetite
    ].copy()

    recommended_funds = recommended_funds.sort_values(
        "sharpe_ratio",
        ascending=False
    )

    return recommended_funds.head(3)[
        ["scheme_name", "fund_house", "risk_grade", "sharpe_ratio"]
    ]

if __name__ == "__main__":
    performance = pd.read_csv("data/processed/07_scheme_performance_clean.csv")

    risk_appetite = "Moderate"

    recommendation_table = recommend_funds(
        performance,
        risk_appetite
    )

    print("Risk Appetite:", risk_appetite)
    print(recommendation_table.to_string(index=False))