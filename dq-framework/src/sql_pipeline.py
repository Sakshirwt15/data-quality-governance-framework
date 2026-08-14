"""
sql_pipeline.py
------------------
Loads the raw CSV into a SQLite database, executes the SQL quality-check
queries (sql/02_quality_check_queries.sql), then builds the cleaned table
using the logic in sql/03_create_cleaned_table.sql.

SQLite is used here purely so the whole project runs with zero external setup
(no Postgres/MySQL server needed). The .sql files are standard SQL and map
directly onto Postgres/Snowflake/BigQuery with trivial syntax tweaks
(e.g. swapping SQLite's window-function dedup for the same pattern in any
modern warehouse).
"""

import sqlite3
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "reports" / "dq_pipeline.db"
SQL_DIR = PROJECT_ROOT / "sql"


def load_staging_table(conn: sqlite3.Connection, raw_csv_path: Path):
    df = pd.read_csv(raw_csv_path)
    df.to_sql("staging_loan_applications", conn, if_exists="replace", index=False)
    return df


def run_query_file_get_results(conn: sqlite3.Connection, sql_path: Path) -> dict:
    """Runs every SELECT statement in a .sql file and returns {label: DataFrame}."""
    raw_sql = sql_path.read_text()
    statements = [s.strip() for s in raw_sql.split(";") if s.strip() and not s.strip().startswith("--")]

    results = {}
    for i, stmt in enumerate(statements, start=1):
        # strip leading comment lines within the statement block for a clean read
        clean_stmt = "\n".join(
            line for line in stmt.splitlines() if not line.strip().startswith("--")
        ).strip()
        if not clean_stmt:
            continue
        if clean_stmt.upper().startswith("SELECT"):
            try:
                results[f"query_{i}"] = pd.read_sql_query(clean_stmt + ";", conn)
            except Exception as e:
                results[f"query_{i}_error"] = str(e)
    return results


def build_cleaned_table(conn: sqlite3.Connection):
    ddl = (SQL_DIR / "03_create_cleaned_table.sql").read_text()
    # Execute as a script since it contains CREATE TABLE ... AS WITH ...
    conn.executescript(ddl)
    conn.commit()
    cleaned_df = pd.read_sql_query("SELECT * FROM cleaned_loan_applications;", conn)
    return cleaned_df


def run_sql_pipeline(raw_csv_path: Path, cleaned_csv_out: Path) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    load_staging_table(conn, raw_csv_path)
    check_results = run_query_file_get_results(conn, SQL_DIR / "02_quality_check_queries.sql")
    cleaned_df = build_cleaned_table(conn)

    cleaned_csv_out.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(cleaned_csv_out, index=False)

    conn.close()
    return {"check_results": check_results, "cleaned_rows": len(cleaned_df)}


if __name__ == "__main__":
    raw_path = PROJECT_ROOT / "data" / "raw" / "loan_applications_raw.csv"
    cleaned_path = PROJECT_ROOT / "data" / "cleaned" / "loan_applications_cleaned.csv"
    result = run_sql_pipeline(raw_path, cleaned_path)
    print(f"Cleaned table written with {result['cleaned_rows']} rows -> {cleaned_path}")
