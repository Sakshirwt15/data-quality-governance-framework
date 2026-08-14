# Data Quality & Governance Framework

An end-to-end, reusable **Data Quality Monitoring System** built for financial / lending datasets.
It inspects any CSV, scores it across the four core data-quality dimensions
(**Completeness, Uniqueness, Validity, Consistency**), pushes the raw data through a
**SQL staging → cleaned pipeline**, and outputs a live **Power BI dashboard** for monitoring.

This mirrors how a real Data Stewardship function operates: raw data lands, gets profiled,
issues get scored and logged, a cleaned/trusted version is produced, and business users get a
scorecard to monitor quality over time.

**Tech stack:** Python (pandas, numpy) · SQL (SQLite) · Power BI

---

## Why this project

Most data/analytics portfolios jump straight to modeling. This project focuses instead on
**Data Stewardship** — the layer that comes *before* modeling: is the data even trustworthy?
It answers that with a quantified, auditable Health Score instead of a gut feeling.

---

## Dashboard

![Dashboard Screenshot](dashboard/dashboard_screenshot.png)

The dashboard gives a data governance lead three things at a glance:
1. **Header KPIs** — overall health score, row/column counts, columns needing attention
2. **Column-level scorecard** — which columns are healthy vs. flagged, color-coded
3. **Dimension breakdown** — *why* a column scored low (missing data? invalid values? formatting?)
4. **Issue drill-down log** — the exact rows behind each flagged issue

*(Built in Power BI — see [`dashboard/README.md`](dashboard/README.md) to reproduce it from the generated CSVs.)*

---

## Results (on the synthetic sample dataset)

Running the pipeline on the included 2,030-row synthetic loan-application dataset produced:

| Metric | Value |
|---|---|
| Overall Health Score | **98.48 / 100** |
| Total columns profiled | 12 |
| Columns flagged (Warning) | 1 — `gender` (inconsistent casing: "Male" / "male" / "MALE") |
| Columns flagged (Critical) | 0 |
| Total row-level issues logged | 238,569* |

*\*cumulative across all issue types (missing values, invalid values, duplicate keys) — see `reports/issues_log.csv` for the full breakdown by column and issue type.*

This confirms the engine correctly catches both **numeric validity issues** (e.g. negative ages, out-of-range credit scores) and **subtler formatting issues** (e.g. inconsistent text casing) that a manual review would likely miss.

---

## Folder Structure

dq-framework/
│
├── README.md
├── requirements.txt
├── run_pipeline.py # ONE COMMAND to run the entire project end-to-end
│
├── data/
│ ├── raw/loan_applications_raw.csv
│ └── cleaned/loan_applications_cleaned.csv
│
├── src/
│ ├── generate_sample_data.py # Creates a realistic, intentionally messy loan dataset
│ ├── data_quality_checks.py # Core DQ engine: completeness/uniqueness/validity/consistency
│ ├── sql_pipeline.py # Loads data into SQLite, runs SQL-based checks, builds cleaned table
│ └── report_generator.py # Turns check results into dashboard-ready CSV/JSON
│
├── sql/
│ ├── 01_create_staging_table.sql
│ ├── 02_quality_check_queries.sql
│ └── 03_create_cleaned_table.sql
│
├── reports/ # AUTO-GENERATED after running the pipeline
│ ├── column_health_scorecard.csv
│ ├── overall_summary.json
│ └── issues_log.csv
│
├── dashboard/
│ ├── README.md # Step-by-step guide to build the Power BI dashboard
│ ├── dq-dashboard.pbix # The Power BI file
│ └── dashboard_screenshot.png # Screenshot used above
│
└── notebook/
└── data_quality_walkthrough.ipynb


---

## How it works (pipeline stages)

1. **Generate / ingest raw data** — `generate_sample_data.py` creates a synthetic loan-application
   dataset with realistic issues intentionally injected: missing values, duplicate IDs, negative
   ages/incomes, out-of-range credit scores, inconsistent categorical casing, and mixed date formats.
2. **Python DQ engine** — `data_quality_checks.py` runs four dimension checks per column and
   computes a weighted **Health Score (0–100)**.
3. **SQL pipeline** — `sql_pipeline.py` loads the raw CSV into a SQLite `staging` table, runs the
   SQL checks in `sql/02_quality_check_queries.sql`, and builds a `cleaned` table using the logic
   in `sql/03_create_cleaned_table.sql`.
4. **Report generation** — `report_generator.py` writes three dashboard-ready files to `reports/`.
5. **Dashboard** — the reports feed a Power BI dashboard (see above).

---

## Quick Start

```bash
pip install -r requirements.txt
python run_pipeline.py
```

This single command generates the data, runs every check, builds the cleaned table, and writes
all reports to `reports/`.

To re-run on your OWN dataset instead of the synthetic one:

```bash
python run_pipeline.py --input data/raw/your_file.csv --key-column your_id_column
```

---

## Data Quality Dimensions Measured

| Dimension     | What it checks                                          | Example issue caught                     |
|---------------|-----------------------------------------------------------|-------------------------------------------|
| Completeness  | % of missing / null values per column                    | `annual_income` missing in ~6% of rows    |
| Uniqueness    | Duplicate primary keys / duplicate full rows              | Same `customer_id` appears twice          |
| Validity      | Business-rule conformity (ranges, allowed categories)     | `age` = -5, `credit_score` = 1200         |
| Consistency   | Formatting consistency (case, whitespace, date formats)   | "Male" / "male" / "MALE " in same column  |

Each dimension feeds into a weighted **Health Score** per column, rolled up into an overall
dataset health score.

---

## Possible Extensions (interview talking points)

- Schedule the pipeline (cron / Airflow) to monitor a live data feed batch-by-batch
- Add a data drift check (compare today's health score vs. last week's) and plot the trend
- Wire up email/Slack alerts when health score drops below a threshold
- Swap SQLite for a real warehouse (Postgres/Snowflake) — the SQL is portable with minimal changes

---

## Author

Built by sakshi rawat as part of a Credit & Fraud Risk analytics portfolio.
