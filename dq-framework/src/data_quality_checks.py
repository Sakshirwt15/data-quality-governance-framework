"""
data_quality_checks.py
------------------------
Core reusable Data Quality engine.

Given ANY pandas DataFrame + a small rules config, this computes scores across
four dimensions per column:
    1. Completeness  - % non-null
    2. Uniqueness    - duplicate rows / duplicate key values
    3. Validity      - business-rule conformity (ranges, allowed categories)
    4. Consistency   - formatting consistency (case, whitespace, date formats)

and rolls them up into a 0-100 Health Score per column and for the dataset
overall. This class is dataset-agnostic — pass in your own `validity_rules`
for any new dataset.
"""

from __future__ import annotations
import re
import pandas as pd
import numpy as np
from dataclasses import dataclass, field


# Weights used to combine the 4 dimensions into one Health Score.
# Tunable — a real governance team would set these based on business priority.
DIMENSION_WEIGHTS = {
    "completeness": 0.35,
    "uniqueness": 0.15,
    "validity": 0.35,
    "consistency": 0.15,
}


@dataclass
class DataQualityChecker:
    df: pd.DataFrame
    key_column: str | None = None                 # e.g. "customer_id" for duplicate-key checks
    validity_rules: dict = field(default_factory=dict)   # column -> rule dict (see below)

    # populated after .run() is called
    column_scores_: pd.DataFrame | None = None
    overall_score_: float | None = None
    issues_log_: pd.DataFrame | None = None

    # ------------------------------------------------------------------ #
    # Dimension 1: Completeness
    # ------------------------------------------------------------------ #
    def _completeness(self) -> dict:
        total = len(self.df)
        result = {}
        for col in self.df.columns:
            missing = self.df[col].isna().sum()
            pct_missing = round(100 * missing / total, 2) if total else 0.0
            score = round(100 - pct_missing, 2)
            result[col] = {
                "missing_count": int(missing),
                "missing_pct": pct_missing,
                "completeness_score": score,
            }
        return result

    # ------------------------------------------------------------------ #
    # Dimension 2: Uniqueness
    # ------------------------------------------------------------------ #
    def _uniqueness(self) -> dict:
        total = len(self.df)
        full_dupe_rows = int(self.df.duplicated().sum())

        result = {"__dataset__": {
            "duplicate_rows": full_dupe_rows,
            "duplicate_rows_pct": round(100 * full_dupe_rows / total, 2) if total else 0.0,
        }}

        if self.key_column and self.key_column in self.df.columns:
            dupe_keys = int(self.df[self.key_column].duplicated().sum())
            key_score = round(100 - (100 * dupe_keys / total), 2) if total else 100.0
            result[self.key_column] = {
                "duplicate_key_count": dupe_keys,
                "uniqueness_score": key_score,
            }
        return result

    # ------------------------------------------------------------------ #
    # Dimension 3: Validity
    # ------------------------------------------------------------------ #
    # validity_rules format, per column:
    #   {"min": 0, "max": 100}                       -> numeric range rule
    #   {"allowed": ["A", "B", "C"]}                  -> categorical allow-list
    def _validity(self) -> dict:
        total = len(self.df)
        result = {}
        for col, rule in self.validity_rules.items():
            if col not in self.df.columns:
                continue
            invalid_mask = pd.Series(False, index=self.df.index)

            if "min" in rule or "max" in rule:
                numeric_col = pd.to_numeric(self.df[col], errors="coerce")
                if "min" in rule:
                    invalid_mask |= numeric_col < rule["min"]
                if "max" in rule:
                    invalid_mask |= numeric_col > rule["max"]

            if "allowed" in rule:
                normalized = self.df[col].astype(str).str.strip().str.lower()
                allowed_lower = [str(a).strip().lower() for a in rule["allowed"]]
                invalid_mask |= ~normalized.isin(allowed_lower) & self.df[col].notna()

            invalid_count = int(invalid_mask.sum())
            score = round(100 - (100 * invalid_count / total), 2) if total else 100.0
            result[col] = {
                "invalid_count": invalid_count,
                "invalid_pct": round(100 * invalid_count / total, 2) if total else 0.0,
                "validity_score": score,
            }
        return result

    # ------------------------------------------------------------------ #
    # Dimension 4: Consistency
    # ------------------------------------------------------------------ #
    def _consistency(self) -> dict:
        total = len(self.df)
        result = {}
        for col in self.df.select_dtypes(include="object").columns:
            series = self.df[col].dropna().astype(str)
            if series.empty:
                continue

            has_whitespace_issue = series != series.str.strip()
            # crude case-consistency check: same value appears in multiple casings
            case_variants = series.str.strip().str.lower().groupby(series.str.strip().str.lower()).transform("count")
            distinct_casing = series.str.strip().groupby(series.str.strip().str.lower()).transform(lambda x: x.nunique())
            case_issue_mask = distinct_casing > 1

            issue_count = int((has_whitespace_issue | case_issue_mask).sum())
            score = round(100 - (100 * issue_count / total), 2) if total else 100.0
            result[col] = {
                "formatting_issue_count": issue_count,
                "consistency_score": score,
            }
        return result

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    def run(self) -> "DataQualityChecker":
        completeness = self._completeness()
        uniqueness = self._uniqueness()
        validity = self._validity()
        consistency = self._consistency()

        rows = []
        for col in self.df.columns:
            comp_score = completeness.get(col, {}).get("completeness_score", 100.0)
            uniq_score = uniqueness.get(col, {}).get("uniqueness_score", 100.0)
            valid_score = validity.get(col, {}).get("validity_score", 100.0)
            cons_score = consistency.get(col, {}).get("consistency_score", 100.0)

            health_score = round(
                comp_score * DIMENSION_WEIGHTS["completeness"] +
                uniq_score * DIMENSION_WEIGHTS["uniqueness"] +
                valid_score * DIMENSION_WEIGHTS["validity"] +
                cons_score * DIMENSION_WEIGHTS["consistency"],
                2,
            )

            status = "Good" if health_score >= 90 else ("Warning" if health_score >= 75 else "Critical")

            rows.append({
                "column": col,
                "completeness_score": comp_score,
                "missing_pct": completeness.get(col, {}).get("missing_pct", 0.0),
                "uniqueness_score": uniq_score,
                "validity_score": valid_score,
                "invalid_pct": validity.get(col, {}).get("invalid_pct", 0.0),
                "consistency_score": cons_score,
                "health_score": health_score,
                "status": status,
            })

        self.column_scores_ = pd.DataFrame(rows).sort_values("health_score")
        self.overall_score_ = round(self.column_scores_["health_score"].mean(), 2)

        self.issues_log_ = self._build_issues_log()
        return self

    def _build_issues_log(self) -> pd.DataFrame:
        """Row-level log of exactly which records tripped which rule — useful for
        drilling into the dashboard ('show me the rows behind this issue')."""
        issues = []

        # missing value issues
        for col in self.df.columns:
            missing_rows = self.df[self.df[col].isna()]
            for idx in missing_rows.index[:50]:  # cap sample size
                issues.append({"row_index": idx, "column": col, "issue_type": "missing_value"})

        # duplicate key issues
        if self.key_column and self.key_column in self.df.columns:
            dupe_rows = self.df[self.df[self.key_column].duplicated(keep=False)]
            for idx in dupe_rows.index[:50]:
                issues.append({"row_index": idx, "column": self.key_column, "issue_type": "duplicate_key"})

        # validity issues
        for col, rule in self.validity_rules.items():
            if col not in self.df.columns:
                continue
            numeric_col = pd.to_numeric(self.df[col], errors="coerce")
            invalid_mask = pd.Series(False, index=self.df.index)
            if "min" in rule:
                invalid_mask |= numeric_col < rule["min"]
            if "max" in rule:
                invalid_mask |= numeric_col > rule["max"]
            for idx in self.df[invalid_mask].index[:50]:
                issues.append({"row_index": idx, "column": col, "issue_type": "invalid_value"})

        return pd.DataFrame(issues) if issues else pd.DataFrame(
            columns=["row_index", "column", "issue_type"]
        )

    def summary(self) -> dict:
        if self.column_scores_ is None:
            raise RuntimeError("Call .run() before .summary()")
        return {
            "overall_health_score": self.overall_score_,
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "columns_critical": int((self.column_scores_["status"] == "Critical").sum()),
            "columns_warning": int((self.column_scores_["status"] == "Warning").sum()),
            "columns_good": int((self.column_scores_["status"] == "Good").sum()),
        }


# Default validity rules for the sample loan dataset — edit/extend for your own data
DEFAULT_LOAN_VALIDITY_RULES = {
    "age": {"min": 18, "max": 100},
    "annual_income": {"min": 0, "max": 1e8},
    "credit_score": {"min": 300, "max": 900},
    "loan_amount": {"min": 0, "max": 1e8},
    "employment_status": {"allowed": ["Employed", "Self-Employed", "Unemployed", "Retired"]},
    "marital_status": {"allowed": ["Single", "Married", "Divorced", "Widowed"]},
}
