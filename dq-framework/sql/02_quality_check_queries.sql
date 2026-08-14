-- 02_quality_check_queries.sql
-- Read-only diagnostic queries run against the staging table.
-- These mirror the Python checks in data_quality_checks.py but show the SQL-native
-- way a data steward / analyst would investigate the same issues directly in a warehouse.

-- 1. COMPLETENESS: missing value counts per column
SELECT
    SUM(CASE WHEN annual_income IS NULL THEN 1 ELSE 0 END)      AS missing_annual_income,
    SUM(CASE WHEN credit_score  IS NULL THEN 1 ELSE 0 END)      AS missing_credit_score,
    SUM(CASE WHEN employment_status IS NULL THEN 1 ELSE 0 END)  AS missing_employment_status,
    SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END)                AS missing_age,
    COUNT(*)                                                     AS total_rows
FROM staging_loan_applications;


-- 2. UNIQUENESS: duplicate customer_id values
SELECT
    customer_id,
    COUNT(*) AS occurrence_count
FROM staging_loan_applications
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;


-- 3. UNIQUENESS: fully duplicated rows (every column identical)
SELECT
    customer_id, age, annual_income, credit_score, loan_amount,
    existing_loans, region, employment_status, gender, marital_status,
    application_date, default_flag,
    COUNT(*) AS dup_count
FROM staging_loan_applications
GROUP BY customer_id, age, annual_income, credit_score, loan_amount,
         existing_loans, region, employment_status, gender, marital_status,
         application_date, default_flag
HAVING COUNT(*) > 1;


-- 4. VALIDITY: out-of-range / impossible values
SELECT customer_id, age, annual_income, credit_score
FROM staging_loan_applications
WHERE age < 18 OR age > 100
   OR annual_income < 0
   OR credit_score < 300 OR credit_score > 900;


-- 5. VALIDITY: category values outside the allowed list
SELECT DISTINCT employment_status
FROM staging_loan_applications
WHERE LOWER(TRIM(employment_status)) NOT IN
      ('employed', 'self-employed', 'unemployed', 'retired');


-- 6. CONSISTENCY: inconsistent casing/whitespace in categorical fields (example: region)
SELECT DISTINCT region
FROM staging_loan_applications
WHERE region != TRIM(region);


-- 7. High-level dataset health snapshot (rolled up counts for a scorecard)
SELECT
    (SELECT COUNT(*) FROM staging_loan_applications)                                   AS total_rows,
    (SELECT COUNT(*) FROM (SELECT customer_id FROM staging_loan_applications
                            GROUP BY customer_id HAVING COUNT(*) > 1))                  AS duplicate_customer_ids,
    (SELECT COUNT(*) FROM staging_loan_applications
        WHERE age < 18 OR age > 100 OR credit_score < 300 OR credit_score > 900)       AS invalid_value_rows,
    (SELECT COUNT(*) FROM staging_loan_applications
        WHERE annual_income IS NULL OR credit_score IS NULL)                           AS incomplete_rows;
