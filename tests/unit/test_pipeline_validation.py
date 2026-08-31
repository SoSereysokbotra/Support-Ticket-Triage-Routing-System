import pandas as pd
import pytest

from src.pipelines.orchestration.tasks.validate import DataValidationError, validate_data_task


def test_validate_data_success():
    valid_df = pd.DataFrame({
        "text": ["My laptop broke", "Cannot access VPN", "Need software license", "Router offline", "Billing question"] * 20,
        "category": ["Hardware", "Access & Security", "Software", "Network", "Billing & Admin"] * 20,
    })
    # Task functions in Prefect can be executed directly or with .fn()
    res = validate_data_task.fn(valid_df, min_samples=10)
    assert len(res) == 100


def test_validate_data_fails_on_small_sample_size():
    small_df = pd.DataFrame({
        "text": ["Laptop broken"],
        "category": ["Hardware"],
    })
    with pytest.raises(DataValidationError, match="below required minimum threshold"):
        validate_data_task.fn(small_df, min_samples=50)


def test_validate_data_fails_on_null_text():
    null_df = pd.DataFrame({
        "text": [None, "Laptop broken", "VPN down"] * 20,
        "category": ["Hardware", "Hardware", "Network"] * 20,
    })
    with pytest.raises(DataValidationError, match="null values in 'text' column"):
        validate_data_task.fn(null_df, min_samples=10)


def test_validate_data_fails_on_empty_string_text():
    empty_df = pd.DataFrame({
        "text": ["   ", "Laptop broken", "VPN down"] * 20,
        "category": ["Hardware", "Hardware", "Network"] * 20,
    })
    with pytest.raises(DataValidationError, match="empty string values in 'text' column"):
        validate_data_task.fn(empty_df, min_samples=10)


def test_validate_data_fails_on_invalid_category_labels():
    invalid_cat_df = pd.DataFrame({
        "text": ["Laptop broken", "VPN down", "Salary question"] * 20,
        "category": ["Hardware", "Network", "INVALID_UNKNOWN_CATEGORY"] * 20,
    })
    with pytest.raises(DataValidationError, match="Found unrecognized categories"):
        validate_data_task.fn(invalid_cat_df, min_samples=10)


def test_validate_data_fails_on_catastrophic_imbalance():
    imbalanced_df = pd.DataFrame({
        "text": ["Laptop broken"] * 95 + ["VPN down"] * 5,
        "category": ["Hardware"] * 95 + ["Network"] * 5,
    })
    with pytest.raises(DataValidationError, match="Catastrophic class imbalance detected"):
        validate_data_task.fn(imbalanced_df, min_samples=50, max_class_imbalance_ratio=0.80)
