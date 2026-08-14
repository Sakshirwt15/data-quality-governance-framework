-- 01_create_staging_table.sql
-- Raw data lands here exactly as received from the source, no transformation.
-- (In this project, sql_pipeline.py loads the CSV into this table via pandas.to_sql,
--  but this DDL documents the intended schema for a real warehouse setup.)

DROP TABLE IF EXISTS staging_loan_applications;

CREATE TABLE staging_loan_applications (
    customer_id         INTEGER,
    age                  REAL,
    annual_income        REAL,
    credit_score         REAL,
    loan_amount          REAL,
    existing_loans       INTEGER,
    region               TEXT,
    employment_status    TEXT,
    gender               TEXT,
    marital_status       TEXT,
    application_date     TEXT,      -- kept as TEXT deliberately: raw dates are inconsistent
    default_flag         INTEGER
);
