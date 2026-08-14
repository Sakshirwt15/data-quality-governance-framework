"""
generate_sample_data.py
------------------------
Creates a synthetic loan-application dataset that mimics real-world messiness
often seen in financial data: missing values, duplicates, invalid values,
and inconsistent formatting.

This stands in for "raw data landing from an upstream source" — in a real
company this would instead be a data pull from a warehouse / API.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RANDOM_SEED = 42
N_ROWS = 2000

REGIONS = ["North", "South", "East", "West", "Central"]
EMPLOYMENT_STATUS = ["Employed", "Self-Employed", "Unemployed", "Retired"]
GENDER_VARIANTS = ["Male", "male", "MALE ", "Female", "female", "FEMALE", "F", "M"]
MARITAL_STATUS = ["Single", "Married", "Divorced", "Widowed"]


def generate_raw_dataset(n_rows: int = N_ROWS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    customer_id = np.arange(100000, 100000 + n_rows)

    age = rng.integers(18, 75, size=n_rows).astype(float)
    annual_income = rng.normal(650000, 250000, size=n_rows).round(2)  # INR
    credit_score = rng.integers(300, 900, size=n_rows).astype(float)
    loan_amount = rng.normal(400000, 150000, size=n_rows).round(2)
    existing_loans = rng.integers(0, 5, size=n_rows)
    region = rng.choice(REGIONS, size=n_rows)
    employment_status = rng.choice(EMPLOYMENT_STATUS, size=n_rows)
    gender = rng.choice(GENDER_VARIANTS, size=n_rows)
    marital_status = rng.choice(MARITAL_STATUS, size=n_rows)
    default_flag = rng.choice([0, 1], size=n_rows, p=[0.85, 0.15])

    # Mixed date formats (a classic consistency problem)
    base_dates = pd.date_range("2023-01-01", "2024-12-31", periods=n_rows)
    date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%m/%d/%Y"]
    application_date = [
        d.strftime(date_formats[i % len(date_formats)]) for i, d in enumerate(base_dates)
    ]

    df = pd.DataFrame({
        "customer_id": customer_id,
        "age": age,
        "annual_income": annual_income,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "existing_loans": existing_loans,
        "region": region,
        "employment_status": employment_status,
        "gender": gender,
        "marital_status": marital_status,
        "application_date": application_date,
        "default_flag": default_flag,
    })

    # ---- Inject realistic data quality issues ----

    # 1. Missing values (completeness issue)
    for col, frac in [("annual_income", 0.06), ("credit_score", 0.04),
                       ("employment_status", 0.03), ("age", 0.02)]:
        idx = rng.choice(df.index, size=int(frac * n_rows), replace=False)
        df.loc[idx, col] = np.nan

    # 2. Duplicate rows (uniqueness issue) — repeat ~1.5% of customer_ids
    dup_idx = rng.choice(df.index, size=int(0.015 * n_rows), replace=False)
    dup_rows = df.loc[dup_idx].copy()
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 3. Invalid values (validity issue)
    invalid_age_idx = rng.choice(df.index, size=15, replace=False)
    df.loc[invalid_age_idx, "age"] = -5  # negative age

    invalid_score_idx = rng.choice(df.index, size=15, replace=False)
    df.loc[invalid_score_idx, "credit_score"] = 1200  # out of valid 300-900 range

    invalid_income_idx = rng.choice(df.index, size=10, replace=False)
    df.loc[invalid_income_idx, "annual_income"] = -100000  # negative income

    # 4. Consistency issues — stray whitespace in region
    whitespace_idx = rng.choice(df.index, size=20, replace=False)
    df.loc[whitespace_idx, "region"] = df.loc[whitespace_idx, "region"] + "  "

    # Shuffle so injected issues aren't clustered at the end
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


def main():
    out_path = Path(__file__).resolve().parent.parent / "data" / "raw" / "loan_applications_raw.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_raw_dataset()
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")


if __name__ == "__main__":
    main()
