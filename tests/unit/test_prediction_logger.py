"""
Unit Tests for PredictionLogger
"""

from pathlib import Path

import pandas as pd
import pytest

from src.infrastructure.monitoring.prediction_logger import PredictionLogger


@pytest.fixture
def temp_logger(tmp_path):
    db_file = tmp_path / "test_logs.db"
    return PredictionLogger(db_path=db_file)


def test_log_single_prediction(temp_logger):
    temp_logger.log_prediction(
        ticket_id="TICKET-001",
        text="My database connection is failing with timeout error.",
        predicted_category="Technical Issue",
        confidence=0.985,
        latency_ms=18.4,
        probabilities={"Technical Issue": 0.985, "Billing": 0.015},
        customer_id="CUST-100",
        customer_tier="Enterprise",
        is_vip=True,
        model_version="v1",
    )

    df = temp_logger.get_recent_logs(limit=10)
    assert len(df) == 1
    assert df.iloc[0]["ticket_id"] == "TICKET-001"
    assert df.iloc[0]["predicted_category"] == "Technical Issue"
    assert df.iloc[0]["confidence"] == pytest.approx(0.985)
    assert df.iloc[0]["text_length"] == len("My database connection is failing with timeout error.")
    assert df.iloc[0]["word_count"] == 8
    assert df.iloc[0]["is_vip"] == 1


def test_log_batch_predictions(temp_logger):
    records = [
        {
            "ticket_id": f"TICK-{i}",
            "text": f"Sample ticket text number {i}",
            "predicted_category": "Billing" if i % 2 == 0 else "Account Access",
            "confidence": 0.80 + (i * 0.01),
            "latency_ms": 12.0 + i,
            "customer_id": f"CUST-{i}",
        }
        for i in range(15)
    ]

    temp_logger.log_batch(records)
    df = temp_logger.get_recent_logs(limit=20)
    assert len(df) == 15

    metrics = temp_logger.get_summary_metrics()
    assert metrics["total_requests"] == 15
    assert metrics["avg_confidence"] > 0.80
    assert "Billing" in metrics["category_distribution"]
    assert "Account Access" in metrics["category_distribution"]


def test_empty_logs_summary_metrics(temp_logger):
    metrics = temp_logger.get_summary_metrics()
    assert metrics["total_requests"] == 0
    assert metrics["avg_confidence"] == 0.0
    assert metrics["avg_latency_ms"] == 0.0
    assert metrics["category_distribution"] == {}
