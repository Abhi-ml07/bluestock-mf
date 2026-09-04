import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path("data/raw")

csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

print("=" * 70)
print("BLUESTOCK MUTUAL FUND - DATA INGESTION")
print("=" * 70)
print(f"\nFound {len(csv_files)} CSV files.\n")

datasets = {}

for file in csv_files:

    print("\n" + "=" * 70)
    print(f"FILE: {file.name}")
    print("=" * 70)

    try:
        df = pd.read_csv(file)
        datasets[file.stem] = df

        print(f"\nShape: {df.shape}")
        print("\nColumns:")
        print(df.columns.tolist())
        print("\nData Types:")
        print(df.dtypes)
        print("\nFirst 5 Rows:")
        print(df.head())
        print("\nMissing Values:")
        missing = df.isnull().sum()
        print(missing[missing > 0])
        print(f"\nDuplicate Rows: {df.duplicated().sum()}")
        
    except Exception as e:
        print(f"ERROR loading {file.name}: {e}")

print("\n" + "=" * 70)
print("DATA INGESTION SUMMARY")
print("=" * 70)

for name, df in datasets.items():
    print(f"{name}: {df.shape[0]:,} rows × {df.shape[1]} columns")

print("\nData ingestion inspection completed.")