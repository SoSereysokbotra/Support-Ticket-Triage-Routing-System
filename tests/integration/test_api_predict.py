import pytest
from fastapi.testclient import TestClient

from src.domain.entities.category import TicketCategory
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture
def client():
    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.91,
        model_version="mock-api-v1",
    )
    app = create_app(model_override=mock_clf)
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_version"] == "mock-api-v1"
    assert "uptime_seconds" in data


def test_predict_endpoint_success(client: TestClient):
    payload = {
        "text": "Cannot connect to the VPN gateway. TLS handshake failed continuously.",
        "title": "VPN Failure",
        "customer_id": "CUST-999",
        "urgency_hint": "Critical",
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_category"] == "Network"
    assert data["confidence"] == 0.91
    assert data["assigned_team"] == "Network Operations Center (NOC)"
    assert data["priority_level"] == "Critical"
    assert data["target_sla_hours"] == 1
    assert data["auto_routed"] is True


def test_predict_endpoint_validation_error(client: TestClient):
    # Empty / too short text
    payload = {"text": "hi"}
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_predict_batch_endpoint(client: TestClient):
    payload = {
        "tickets": [
            {"text": "VPN tunnel disconnected unexpectedly from remote server."},
            {"text": "Wi-Fi in boardroom dropouts during all client meetings."},
        ]
    }
    response = client.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["batch_size"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["predicted_category"] == "Network"
