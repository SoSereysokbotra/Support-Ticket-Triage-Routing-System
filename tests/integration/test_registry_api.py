from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.domain.entities.category import TicketCategory
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture
def registry_test_app(tmp_path: Path):
    db_file = tmp_path / "test_api_mlruns.db"
    tracking_uri = f"sqlite:///{db_file.as_posix()}"
    registry = MLflowModelRegistry(
        tracking_uri=tracking_uri,
        registry_uri=tracking_uri,
        project_root=tmp_path,
    )

    # Log 2 mock runs and register them
    dummy_dir = tmp_path / "model_art"
    dummy_dir.mkdir()
    (dummy_dir / "config.json").write_text('{"dummy": true}')

    run1 = registry.log_training_run(
        params={"lr": 3e-5},
        metrics={"macro_f1": 0.95},
        model_artifact_dir=dummy_dir,
        run_name="api_v1_run",
    )
    mv1 = registry.register_model_from_run(run1, "ticket-classifier", description="Model v1")
    registry.set_alias("ticket-classifier", "production", str(mv1.version))

    run2 = registry.log_training_run(
        params={"lr": 5e-5},
        metrics={"macro_f1": 0.91},
        model_artifact_dir=dummy_dir,
        run_name="api_v2_run",
    )
    mv2 = registry.register_model_from_run(run2, "ticket-classifier", description="Model v2")
    registry.set_alias("ticket-classifier", "staging", str(mv2.version))

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.SOFTWARE,
        confidence=0.96,
        model_version="ticket-classifier:1@production",
    )

    app = create_app(model_override=mock_clf, registry_override=registry)
    with TestClient(app) as client:
        yield client, registry


def test_registry_versions_endpoint(registry_test_app):
    client, _ = registry_test_app
    response = client.get("/api/v1/registry/versions")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "ticket-classifier"
    assert str(data["active_production_version"]) == "1"
    assert str(data["active_staging_version"]) == "2"
    assert len(data["versions"]) == 2


def test_registry_promote_endpoint(registry_test_app):
    client, registry = registry_test_app
    # Promote v2 to production
    payload = {"version": "2", "alias": "production"}
    response = client.post("/api/v1/registry/promote", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify via registry
    prod_v = registry.get_version_by_alias(alias="production")
    assert str(prod_v.version) == "2"


def test_registry_rollback_endpoint(registry_test_app):
    client, registry = registry_test_app
    # Promote v2 first
    registry.set_alias("ticket-classifier", "production", "2")
    assert str(registry.get_version_by_alias(alias="production").version) == "2"

    # Rollback to v1 via API
    payload = {"target_version": "1"}
    response = client.post("/api/v1/registry/rollback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["rollback_status"] == "success"
    assert str(data["previous_version"]) == "2"
    assert str(data["current_version"]) == "1"

    # Confirm registry metadata updated
    assert str(registry.get_version_by_alias(alias="production").version) == "1"
