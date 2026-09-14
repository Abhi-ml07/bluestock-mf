from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

def load_datasets():
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    datasets = {}

    for file in csv_files:
        try:
            datasets[file.stem] = pd.read_csv(file)
        except Exception as e:
            raise RuntimeError(f"Failed to load {file.name}") from e

    return datasets

def main():
    datasets = load_datasets()

    for name, df in datasets.items():
        print(f"{name}: {df.shape[0]:,} rows × {df.shape[1]} columns")

if __name__ == "__main__":
    main()