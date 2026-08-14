-- 03_create_cleaned_table.sql
-- Builds the trusted "cleaned" table from staging:
--   - drops fully duplicated rows
--   - keeps only the first occurrence of each customer_id
--   - trims whitespace and standardizes casing on text fields
--   - flags (does NOT silently delete) rows with invalid numeric values,
--     so downstream consumers can choose to exclude or investigate them

DROP TABLE IF EXISTS cleaned_loan_applications;

CREATE TABLE cleaned_loan_applications AS
WITH deduped AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_id) AS rn
    FROM staging_loan_applications
),
distinct_customers AS (
    SELECT * FROM deduped WHERE rn = 1
)
SELECT
    customer_id,
    age,
    annual_income,
    credit_score,
    loan_amount,
    existing_loans,
    TRIM(region)                                   AS region,
    -- standardize casing: Title Case for readability
    (UPPER(SUBSTR(TRIM(employment_status), 1, 1)) || LOWER(SUBSTR(TRIM(employment_status), 2)))
                                                     AS employment_status,
    TRIM(marital_status)                            AS marital_status,
    application_date,
    default_flag,
    CASE
        WHEN age < 18 OR age > 100 THEN 1
        WHEN credit_score < 300 OR credit_score > 900 THEN 1
        WHEN annual_income < 0 THEN 1
        ELSE 0
    END                                              AS is_flagged_invalid
FROM distinct_customers;
