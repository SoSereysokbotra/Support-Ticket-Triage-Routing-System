"""
Integration Tests for Monitoring API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.models.baseline_classifier import BaselineTfidfClassifier
from src.infrastructure.monitoring.prediction_logger import PredictionLogger
from src.presentation.api.app import create_app


@pytest.fixture
def client_with_monitoring(tmp_path):
    clf = BaselineTfidfClassifier()
    clf.fit(["Password reset needed", "Billing invoice error"], ["Account Access", "Billing"])

    logger = PredictionLogger(db_path=tmp_path / "api_test_logs.db")
    app = create_app(model_override=clf, logger_override=logger)

    with TestClient(app) as test_client:
        yield test_client


def test_monitoring_metrics_and_logs_endpoints(client_with_monitoring):
    # 1. Send prediction request
    predict_resp = client_with_monitoring.post(
        "/api/v1/predict",
        json={"text": "I forgot my account password and cannot log in."},
    )
    assert predict_resp.status_code == 200

    # 2. Query metrics endpoint
    metrics_resp = client_with_monitoring.get("/api/v1/monitoring/metrics")
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()
    assert metrics_data["total_requests"] == 1
    assert metrics_data["avg_confidence"] > 0.0

    # 3. Query logs endpoint
    logs_resp = client_with_monitoring.get("/api/v1/monitoring/logs?limit=10")
    assert logs_resp.status_code == 200
    logs_data = logs_resp.json()
    assert len(logs_data) == 1
    assert logs_data[0]["predicted_category"] in ["Account Access", "Other"]
    assert "password" in logs_data[0]["text"].lower()


def test_monitoring_drift_analyze_endpoint(client_with_monitoring):
    # Batch log 10 predictions
    batch_tickets = [{"text": f"Billing issue number {i}"} for i in range(10)]
    batch_resp = client_with_monitoring.post(
        "/api/v1/predict/batch",
        json={"tickets": batch_tickets},
    )
    assert batch_resp.status_code == 200

    # Trigger drift analysis
    drift_resp = client_with_monitoring.post("/api/v1/monitoring/drift/analyze?window_size=10")
    assert drift_resp.status_code == 200
    drift_data = drift_resp.json()
    assert "drift_detected" in drift_data
    assert "share_drifted_features" in drift_data
