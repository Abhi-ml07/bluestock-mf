import requests
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SCHEMES = [
    125497,
    119551,
    120503,
    118632,
    119092,
    120841,
]

def fetch_nav(amfi_code):
    try:
        url = f"https://api.mfapi.in/mf/{amfi_code}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        meta = data["meta"]
        nav_data = data["data"]
        scheme_name = meta.get("scheme_name", "unknown_scheme")

        df = pd.DataFrame(nav_data)

        if not df.empty:
            df["date"] = pd.to_datetime(
                df["date"],
                format="%d-%m-%Y"
            )
            df["nav"] = pd.to_numeric(df["nav"])

        safe_name = (
            scheme_name.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
        )

        output_file = RAW_DATA_DIR / f"{amfi_code}_{safe_name}_live_nav.csv"
        df.to_csv(output_file, index=False)

    except Exception as e:
        raise RuntimeError(f"Failed to fetch NAV for AMFI code {amfi_code}") from e

def main():
    for amfi_code in SCHEMES:
        fetch_nav(amfi_code)

if __name__ == "__main__":
    main()