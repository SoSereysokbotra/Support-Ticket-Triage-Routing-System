"""
Unit Tests for SQLAlchemy-backed PredictionLogger with Database URL
"""

import pytest

from src.infrastructure.monitoring.prediction_logger import PredictionLogger


def test_prediction_logger_with_in_memory_db_url():
    """Verifies PredictionLogger works with a database URL."""
    logger = PredictionLogger(db_url="sqlite:///:memory:")

    assert logger.db_url == "sqlite:///:memory:"
    assert not logger.is_postgres

    logger.log_prediction(
        ticket_id="URL-001",
        text="Testing database URL logging.",
        predicted_category="Network",
        confidence=0.92,
        latency_ms=10.5,
        probabilities={"Network": 0.92, "Software": 0.08},
        customer_id="CUST-999",
        customer_tier="Enterprise",
        is_vip=True,
        model_version="v1.0",
    )

    df = logger.get_recent_logs(limit=5)
    assert len(df) == 1
    assert df.iloc[0]["ticket_id"] == "URL-001"
    assert df.iloc[0]["predicted_category"] == "Network"
    assert df.iloc[0]["confidence"] == pytest.approx(0.92)
    assert df.iloc[0]["is_vip"] == 1

    metrics = logger.get_summary_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["avg_confidence"] == pytest.approx(0.92)
    assert metrics["category_distribution"] == {"Network": 1}

    logger.clear_logs()
    metrics_empty = logger.get_summary_metrics()
    assert metrics_empty["total_requests"] == 0
