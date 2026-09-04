import requests
import pandas as pd
from pathlib import Path


RAW_DATA_DIR = Path("data/raw")

SCHEMES = [
    125497,
    119551,
    120503,
    118632,
    119092,
    120841,
]


def fetch_nav(amfi_code):
    url = f"https://api.mfapi.in/mf/{amfi_code}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    meta = data["meta"]
    nav_data = data["data"]

    scheme_name = meta.get("scheme_name", "unknown_scheme")

    print("\n" + "=" * 70)
    print(f"Requested AMFI Code : {amfi_code}")
    print(f"API Scheme Name     : {scheme_name}")
    print(f"Fund House          : {meta.get('fund_house')}")
    print(f"Records             : {len(nav_data)}")

    df = pd.DataFrame(nav_data)

    if not df.empty:
        df["date"] = pd.to_datetime(
            df["date"],
            format="%d-%m-%Y"
        )

        df["nav"] = pd.to_numeric(df["nav"])

    # Create a safe filename using the ACTUAL API scheme name
    safe_name = (
        scheme_name.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )

    output_file = RAW_DATA_DIR / f"{amfi_code}_{safe_name}_live_nav.csv"

    df.to_csv(output_file, index=False)

    print(f"Saved to            : {output_file}")


for amfi_code in SCHEMES:
    try:
        fetch_nav(amfi_code)
    except Exception as e:
        print(f"\nERROR for AMFI code {amfi_code}: {e}")