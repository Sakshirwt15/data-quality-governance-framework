# Data Quality & Governance Framework

An end-to-end, reusable **Data Quality Monitoring System** built for financial / lending datasets.
It inspects any CSV, scores it across the four core data-quality dimensions
(**Completeness, Uniqueness, Validity, Consistency**), pushes the raw data through a
**SQL staging → cleaned pipeline**, and outputs dashboard-ready files for **Power BI / Tableau**.

This mirrors how a real Data Stewardship function operates: raw data lands, gets profiled,
issues get scored and logged, a cleaned/trusted version is produced, and business users get a
scorecard to monitor quality over time.

---

## Why this project

Built to demonstrate the **Data Stewardship** pillar of Credit & Fraud Risk analytics — a part of
the workflow that's often skipped in portfolio projects (most people jump straight to modeling).
Here, data quality itself is the product.

---

## Folder Structure

```
dq-framework/
│
├── README.md                     # This file
├── requirements.txt               # Python dependencies
├── run_pipeline.py                # ONE COMMAND to run the entire project end-to-end
│
├── data/
│   ├── raw/
│   │   └── loan_applications_raw.csv       # Synthetic messy dataset (auto-generated)
│   └── cleaned/
│       └── loan_applications_cleaned.csv   # Output: cleaned, trusted dataset
│
├── src/
│   ├── generate_sample_data.py    # Creates a realistic, intentionally messy loan dataset
│   ├── data_quality_checks.py     # Core DQ engine: completeness/uniqueness/validity/consistency
│   ├── sql_pipeline.py            # Loads data into SQLite, runs SQL-based checks, builds cleaned table
│   └── report_generator.py        # Turns check results into dashboard-ready CSV/JSON
│
├── sql/
│   ├── 01_create_staging_table.sql
│   ├── 02_quality_check_queries.sql
│   └── 03_create_cleaned_table.sql
│
├── reports/                        # AUTO-GENERATED after running the pipeline
│   ├── column_health_scorecard.csv
│   ├── overall_summary.json
│   └── issues_log.csv
│
├── dashboard/
│   └── README.md                   # Step-by-step guide to build the Power BI / Tableau dashboard
│
└── notebook/
    └── data_quality_walkthrough.ipynb   # Optional interactive walkthrough
```

---

## How it works (pipeline stages)

1. **Generate / ingest raw data** — `generate_sample_data.py` creates a synthetic loan-application
   dataset (2,000 rows) with realistic issues intentionally injected: missing values, duplicate
   IDs, negative ages/incomes, out-of-range credit scores, inconsistent categorical casing, and
   mixed date formats.
2. **Python DQ engine** — `data_quality_checks.py` runs four dimension checks per column and
   computes a weighted **Health Score (0–100)**.
3. **SQL pipeline** — `sql_pipeline.py` loads the raw CSV into a SQLite `staging` table, runs the
   SQL checks in `sql/02_quality_check_queries.sql`, and builds a `cleaned` table using the logic
   in `sql/03_create_cleaned_table.sql`.
4. **Report generation** — `report_generator.py` writes three dashboard-ready files to `reports/`.
5. **Dashboard** — import the `reports/*.csv` files into Power BI or Tableau using the guide in
   `dashboard/README.md`.

---

## Quick Start

```bash
pip install -r requirements.txt
python run_pipeline.py
```

That's it — this single command generates the data, runs every check, builds the cleaned table,
and writes all reports to `reports/`.

To re-run on your OWN dataset instead of the synthetic one, just drop your CSV into
`data/raw/` and pass its path:

```bash
python run_pipeline.py --input data/raw/your_file.csv
```

---

## Data Quality Dimensions Measured

| Dimension     | What it checks                                              | Example issue caught                     |
|---------------|---------------------------------------------------------------|-------------------------------------------|
| Completeness  | % of missing / null values per column                        | `annual_income` missing in 8% of rows     |
| Uniqueness    | Duplicate primary keys / duplicate full rows                 | Same `customer_id` appears twice          |
| Validity      | Business-rule conformity (ranges, allowed categories)         | `age` = -5, `credit_score` = 1200         |
| Consistency   | Formatting consistency (case, whitespace, date formats)      | "Male" / "male" / "MALE " in same column  |

Each dimension contributes to a weighted **Health Score** per column, rolled up into an
**overall dataset health score** — the single number a risk/data-governance lead would look at
first.

---

## Tech Stack
- Python (pandas, numpy)
- SQLite (via Python's built-in `sqlite3` — no external DB setup needed)
- Power BI / Tableau (for the dashboard layer — instructions included)

---

## Possible Extensions (good talking points in interviews)
- Schedule the pipeline (cron / Airflow) to monitor a live data feed batch-by-batch
- Add a data drift check (compare today's health score vs last week's)
- Wire up email/Slack alerts when health score drops below a threshold
- Swap SQLite for a real warehouse (Postgres/Snowflake) with minimal code change
