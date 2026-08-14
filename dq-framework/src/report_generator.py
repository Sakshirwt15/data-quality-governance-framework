"""
report_generator.py
----------------------
Takes the output of DataQualityChecker and writes three dashboard-ready
files into reports/:

    1. column_health_scorecard.csv  -> one row per column, all 4 dimension
                                        scores + overall health score + status
    2. overall_summary.json         -> single-number KPIs for a dashboard header
    3. issues_log.csv               -> row-level sample of exactly which
                                        records tripped which rule

These three files are all Power BI / Tableau needs to build the scorecard
dashboard described in dashboard/README.md.
"""

import json
from pathlib import Path
import pandas as pd

from data_quality_checks import DataQualityChecker


def generate_reports(checker: DataQualityChecker, reports_dir: Path):
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Column health scorecard
    scorecard_path = reports_dir / "column_health_scorecard.csv"
    checker.column_scores_.to_csv(scorecard_path, index=False)

    # 2. Overall summary (dashboard header KPIs)
    summary = checker.summary()
    summary_path = reports_dir / "overall_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # 3. Issues log (row-level drill-down)
    issues_path = reports_dir / "issues_log.csv"
    checker.issues_log_.to_csv(issues_path, index=False)

    return {
        "scorecard_path": scorecard_path,
        "summary_path": summary_path,
        "issues_path": issues_path,
        "summary": summary,
    }


def print_console_report(result: dict, column_scores: pd.DataFrame):
    summary = result["summary"]
    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)
    print(f"Overall Health Score : {summary['overall_health_score']} / 100")
    print(f"Total Rows           : {summary['total_rows']}")
    print(f"Total Columns        : {summary['total_columns']}")
    print(f"Columns - Good       : {summary['columns_good']}")
    print(f"Columns - Warning    : {summary['columns_warning']}")
    print(f"Columns - Critical   : {summary['columns_critical']}")
    print("-" * 60)
    print(column_scores[["column", "health_score", "status"]].to_string(index=False))
    print("=" * 60 + "\n")
