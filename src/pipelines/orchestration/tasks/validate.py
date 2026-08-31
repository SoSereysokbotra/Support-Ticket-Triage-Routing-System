from typing import List

import pandas as pd
from prefect import task

from src.domain.entities.category import TicketCategory


class DataValidationError(ValueError):
    """Raised when incoming retraining data fails quality or integrity constraints."""
    pass


@task(name="validate_ticket_data")
def validate_data_task(
    df: pd.DataFrame,
    min_samples: int = 50,
    max_class_imbalance_ratio: float = 0.85,
    min_class_ratio: float = 0.005,
) -> pd.DataFrame:
    """
    Validates data quality, schema integrity, and distribution balance before training.
    Halts the DAG if any validation check fails.
    """
    print(f"[ValidateTask] Starting validation checks on {len(df)} records...")

    # 1. Check Row Count
    if len(df) < min_samples:
        raise DataValidationError(
            f"Dataset size ({len(df)}) is below required minimum threshold of {min_samples} samples."
        )

    # 2. Check Required Columns
    required_cols = {"text", "category"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise DataValidationError(f"Missing required columns in dataset: {missing_cols}")

    # 3. Check for Nulls or Empty Strings in Text
    null_texts = df["text"].isna().sum()
    if null_texts > 0:
        raise DataValidationError(f"Found {null_texts} null values in 'text' column.")

    empty_texts = (df["text"].str.strip() == "").sum()
    if empty_texts > 0:
        raise DataValidationError(f"Found {empty_texts} empty string values in 'text' column.")

    # 4. Check for Valid Categories
    valid_categories = set(TicketCategory.list_categories())
    unique_categories = set(df["category"].dropna().unique())
    invalid_categories = unique_categories - valid_categories
    if invalid_categories:
        raise DataValidationError(
            f"Found unrecognized categories: {invalid_categories}. Valid options are: {valid_categories}"
        )

    # 5. Check Class Distribution Balance
    category_counts = df["category"].value_counts(normalize=True)
    for cat, ratio in category_counts.items():
        if ratio > max_class_imbalance_ratio:
            raise DataValidationError(
                f"Catastrophic class imbalance detected: '{cat}' represents {ratio:.1%} "
                f"(max allowed is {max_class_imbalance_ratio:.1%})."
            )
        if ratio < min_class_ratio:
            raise DataValidationError(
                f"Severe class under-representation: '{cat}' represents only {ratio:.1%} "
                f"(min required is {min_class_ratio:.1%})."
            )

    print("[ValidateTask] All data validation checks passed successfully:")
    for cat, count in df["category"].value_counts().items():
        print(f"  • {cat}: {count} ({count/len(df):.1%})")

    return df
