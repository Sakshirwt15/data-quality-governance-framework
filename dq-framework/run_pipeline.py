"""
run_pipeline.py
------------------
ONE COMMAND to run the entire Data Quality & Governance Framework end-to-end:

    python run_pipeline.py

Steps:
    1. Generate (or load) the raw dataset
    2. Run the Python-based Data Quality checks (4 dimensions -> health score)
    3. Run the SQL pipeline (staging -> cleaned table) via SQLite
    4. Write dashboard-ready reports to reports/
    5. Print a console summary

Optional: point it at your own CSV instead of the synthetic sample:
    python run_pipeline.py --input path/to/your_file.csv --key-column id
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generate_sample_data import generate_raw_dataset, main as generate_main  # noqa: E402
from data_quality_checks import DataQualityChecker, DEFAULT_LOAN_VALIDITY_RULES  # noqa: E402
from sql_pipeline import run_sql_pipeline  # noqa: E402
from report_generator import generate_reports, print_console_report  # noqa: E402

import pandas as pd  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run the Data Quality & Governance pipeline")
    parser.add_argument("--input", type=str, default=None,
                         help="Path to your own CSV. If omitted, a synthetic sample dataset is generated.")
    parser.add_argument("--key-column", type=str, default="customer_id",
                         help="Primary key column used for duplicate-key checks.")
    args = parser.parse_args()

    raw_path = PROJECT_ROOT / "data" / "raw" / "loan_applications_raw.csv"
    cleaned_path = PROJECT_ROOT / "data" / "cleaned" / "loan_applications_cleaned.csv"
    reports_dir = PROJECT_ROOT / "reports"

    # ---- Step 1: get raw data ----
    if args.input:
        raw_path = Path(args.input)
        print(f"[1/4] Using provided dataset: {raw_path}")
    else:
        print("[1/4] Generating synthetic raw dataset...")
        generate_main()

    df = pd.read_csv(raw_path)

    # ---- Step 2: Python DQ checks ----
    print("[2/4] Running Python data quality checks (completeness, uniqueness, validity, consistency)...")
    checker = DataQualityChecker(
        df=df,
        key_column=args.key_column if args.key_column in df.columns else None,
        validity_rules=DEFAULT_LOAN_VALIDITY_RULES,
    ).run()

    # ---- Step 3: SQL pipeline ----
    print("[3/4] Running SQL staging -> cleaned pipeline (SQLite)...")
    sql_result = run_sql_pipeline(raw_path, cleaned_path)
    print(f"        Cleaned table written: {sql_result['cleaned_rows']} rows -> {cleaned_path}")

    # ---- Step 4: Reports ----
    print("[4/4] Writing dashboard-ready reports...")
    report_result = generate_reports(checker, reports_dir)
    print_console_report(report_result, checker.column_scores_)

    print(f"Reports saved to: {reports_dir}")
    print(f"  - {report_result['scorecard_path'].name}")
    print(f"  - {report_result['summary_path'].name}")
    print(f"  - {report_result['issues_path'].name}")
    print("\nNext step: import these CSVs into Power BI / Tableau -> see dashboard/README.md")


if __name__ == "__main__":
    main()
