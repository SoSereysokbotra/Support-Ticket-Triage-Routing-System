"""
Unit Tests for DriftDetector Engine
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.infrastructure.monitoring.drift_detector import DriftDetector


@pytest.fixture
def sample_reference_df():
    np.random.seed(42)
    return pd.DataFrame({
        "text": ["Short IT support ticket"] * 100,
        "text_length": np.random.normal(loc=120, scale=20, size=100),
        "word_count": np.random.normal(loc=18, scale=4, size=100),
        "predicted_category": ["Technical Issue"] * 40 + ["Billing"] * 30 + ["Account Access"] * 30,
        "confidence": np.random.uniform(0.90, 0.99, size=100),
    })


def test_in_distribution_data_has_no_drift(sample_reference_df, tmp_path):
    detector = DriftDetector(reference_df=sample_reference_df, reports_dir=tmp_path)

    # Current batch sampled from same distribution
    np.random.seed(123)
    current_df = pd.DataFrame({
        "text": ["Short IT support ticket"] * 50,
        "text_length": np.random.normal(loc=120, scale=20, size=50),
        "word_count": np.random.normal(loc=18, scale=4, size=50),
        "predicted_category": ["Technical Issue"] * 20 + ["Billing"] * 15 + ["Account Access"] * 15,
        "confidence": np.random.uniform(0.90, 0.99, size=50),
    })

    result = detector.analyze_drift(current_df, generate_html=False)
    assert result.drift_detected is False
    assert result.share_drifted_features < 0.40


def test_out_of_distribution_data_triggers_drift(sample_reference_df, tmp_path):
    detector = DriftDetector(reference_df=sample_reference_df, reports_dir=tmp_path)

    # Current batch severely shifted (huge legal texts, low confidence, all 'Other')
    np.random.seed(999)
    drifted_df = pd.DataFrame({
        "text": ["A" * 1500] * 50,
        "text_length": np.random.normal(loc=1500, scale=100, size=50),  # Massive length shift
        "word_count": np.random.normal(loc=250, scale=25, size=50),     # Massive word count shift
        "predicted_category": ["Other"] * 50,                           # Category shift
        "confidence": np.random.uniform(0.30, 0.50, size=50),           # Confidence collapse
    })

    result = detector.analyze_drift(drifted_df, generate_html=True)
    assert result.drift_detected is True
    assert result.share_drifted_features >= 0.50
    assert result.html_report_path is not None
    assert Path(result.html_report_path).exists()
    assert Path(result.json_report_path).exists()


def test_empty_dataframe_returns_clean_result(sample_reference_df, tmp_path):
    detector = DriftDetector(reference_df=sample_reference_df, reports_dir=tmp_path)
    result = detector.analyze_drift(pd.DataFrame(), generate_html=False)
    assert result.drift_detected is False
    assert result.current_sample_size == 0
