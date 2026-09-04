import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Project paths
# --------------------------------------------------

RAW_DATA_DIR = Path("data/raw")

# --------------------------------------------------
# Find all CSV files
# --------------------------------------------------

csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

print("=" * 70)
print("BLUESTOCK MUTUAL FUND - DATA INGESTION")
print("=" * 70)

print(f"\nFound {len(csv_files)} CSV files.\n")

# --------------------------------------------------
# Load and inspect every CSV
# --------------------------------------------------

datasets = {}

for file in csv_files:

    print("\n" + "=" * 70)
    print(f"FILE: {file.name}")
    print("=" * 70)

    try:
        df = pd.read_csv(file)

        # Store dataframe
        datasets[file.stem] = df

        # Shape
        print(f"\nShape: {df.shape}")

        # Column names
        print("\nColumns:")
        print(df.columns.tolist())

        # Data types
        print("\nData Types:")
        print(df.dtypes)

        # First 5 rows
        print("\nFirst 5 Rows:")
        print(df.head())

        # Missing values
        print("\nMissing Values:")
        missing = df.isnull().sum()
        print(missing[missing > 0])

        # Duplicate rows
        print(f"\nDuplicate Rows: {df.duplicated().sum()}")

    except Exception as e:
        print(f"ERROR loading {file.name}: {e}")


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\n" + "=" * 70)
print("DATA INGESTION SUMMARY")
print("=" * 70)

for name, df in datasets.items():
    print(f"{name}: {df.shape[0]:,} rows × {df.shape[1]} columns")

print("\nData ingestion inspection completed.")