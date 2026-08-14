# Building the Data Quality Scorecard Dashboard

After running `python run_pipeline.py`, three files appear in `reports/`:

| File | Contains |
|---|---|
| `column_health_scorecard.csv` | One row per column: completeness, uniqueness, validity, consistency scores + overall health score + status (Good/Warning/Critical) |
| `overall_summary.json` | Single-number KPIs: overall health score, row/column counts, count of critical/warning/good columns |
| `issues_log.csv` | Row-level sample of exactly which records tripped which rule (drill-down detail) |

## Power BI

1. **Get Data → Text/CSV** → import `column_health_scorecard.csv` and `issues_log.csv`.
   (For `overall_summary.json`, use **Get Data → JSON**.)
2. Build these visuals:
   - **KPI cards** (top row): Overall Health Score, Total Rows, Columns Critical/Warning/Good
     — bind these to `overall_summary.json`.
   - **Bar chart**: `column` (axis) vs `health_score` (value), colored by `status`
     (Good = green, Warning = amber, Critical = red). This is the main scorecard visual.
   - **Stacked bar**: `column` vs each dimension score (`completeness_score`, `uniqueness_score`,
     `validity_score`, `consistency_score`) — shows WHICH dimension is dragging a column down.
   - **Table/matrix**: `issues_log.csv` filtered by the column selected in the bar chart above
     (use a Power BI slicer / cross-filter) — this is your drill-down: click a red bar, see the
     actual flagged rows.
3. Add a **status color rule**: conditional formatting on `health_score`
   (≥90 green, 75–89 amber, <75 red) to match the `status` column.

## Tableau

1. Connect to `column_health_scorecard.csv` as the primary data source.
2. Build a **horizontal bar chart**: Rows = `column`, Columns = `health_score`, Color = `status`.
3. Add `overall_summary.json` (or manually compute) as **BANs (Big Ass Numbers)** text tiles
   for the top KPI row.
4. Blend in `issues_log.csv` on `column` for a detail table with a dashboard action:
   clicking a bar filters the issues table to that column.

## Suggested Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  Overall Health: 87/100   Rows: 2,030   Critical Cols: 2 │   <- KPI header
├─────────────────────────────────────────────────────────┤
│  Column Health Score (bar chart, colored by status)      │
│  ██████████████████████████████░░  credit_score          │
│  ████████████████████████░░░░░░░░  annual_income          │
│  ████████████████████████████████  region                 │
├─────────────────────────────────────────────────────────┤
│  Dimension Breakdown (stacked bar per column)             │
├─────────────────────────────────────────────────────────┤
│  Issue Drill-down Table (filtered by selected column)     │
└─────────────────────────────────────────────────────────┘
```

## Simulating "quality over time"

To show a trend line (a nice extra for interviews), re-run `run_pipeline.py` on a few different
synthetic batches (change the seed in `generate_sample_data.py`), save each `overall_summary.json`
with a batch date in the filename, and append them into one `quality_trend.csv` with columns
`batch_date, overall_health_score`. Plot that as a line chart to show quality improving/degrading
over time — this is exactly the kind of trend a real data governance dashboard tracks.
