from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent

def run_notebook(notebook):
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                str(PROJECT_ROOT / "notebooks" / notebook)
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Notebook execution failed: {notebook}") from e

def run_script(script):
    try:
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / script)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Script execution failed: {script}") from e

def main():
    run_script("live_nav_fetch.py")
    run_notebook("01_data_ingestion.ipynb")
    run_notebook("02_data_cleaning.ipynb")
    run_script("load_database.py")

if __name__ == "__main__":
    main()