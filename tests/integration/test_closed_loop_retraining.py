"""
Integration Tests for Closed-Loop Drift Retraining Trigger
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.infrastructure.monitoring.prediction_logger import PredictionLogger
from src.pipelines.monitoring.drift_monitoring_job import run_drift_monitoring_job


def test_drift_monitoring_job_triggers_retraining_on_drift(tmp_path):
    db_file = tmp_path / "closed_loop_logs.db"
    reports_dir = tmp_path / "reports"
    logger = PredictionLogger(db_path=db_file)

    # Ingest 25 severely drifted out-of-distribution records
    drifted_records = [
        {
            "ticket_id": f"DRIFT-{i:03d}",
            "text": "Extremely complex regulatory compliance securities and exchange litigation " * 10,
            "predicted_category": "Other",
            "confidence": 0.35,
            "latency_ms": 25.0,
            "customer_id": f"CUST-LEGAL-{i}",
        }
        for i in range(25)
    ]
    logger.log_batch(drifted_records)

    # Mock retraining_flow to verify dispatch
    mock_retraining_flow = MagicMock(return_value={"gate_decision": {"passed": True}})

    with patch("src.pipelines.monitoring.drift_monitoring_job.retraining_flow", mock_retraining_flow):
        result = run_drift_monitoring_job(
            window_size=25,
            drift_threshold=0.30,
            auto_trigger_retraining=True,
            epochs=1,
            db_path=db_file,
            reports_dir=reports_dir,
        )

    assert result["status"] == "completed"
    assert result["drift_detected"] is True
    assert result["retraining_triggered"] is True
    assert mock_retraining_flow.called


def test_drift_monitoring_job_skips_when_healthy(tmp_path):
    db_file = tmp_path / "healthy_logs.db"
    reports_dir = tmp_path / "reports"
    logger = PredictionLogger(db_path=db_file)

    # Ingest representative in-distribution sample
    from src.infrastructure.data.dataset_loader import DatasetLoader
    loader = DatasetLoader()
    base_df = loader.load_or_create_dataset(num_samples=100, random_state=42)

    healthy_records = [
        {
            "ticket_id": f"TICK-{i:03d}",
            "text": row["text"],
            "predicted_category": row["category"],
            "confidence": 0.94,
            "latency_ms": 15.0,
            "customer_id": f"CUST-{i}",
        }
        for i, row in base_df.iterrows()
    ]
    logger.log_batch(healthy_records)

    mock_retraining_flow = MagicMock()

    with patch("src.pipelines.monitoring.drift_monitoring_job.retraining_flow", mock_retraining_flow):
        result = run_drift_monitoring_job(
            window_size=100,
            drift_threshold=0.50,
            auto_trigger_retraining=True,
            epochs=1,
            db_path=db_file,
            reports_dir=reports_dir,
        )

    assert result["status"] == "completed"
    assert result["retraining_triggered"] is False
    assert not mock_retraining_flow.called
