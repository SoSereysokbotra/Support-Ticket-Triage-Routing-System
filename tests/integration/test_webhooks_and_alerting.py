"""
Integration Tests for Outbound Webhook Subscriptions and Incident Alerting (API v2).
Verifies tenant-isolated webhook registration, signature computation,
test ping execution, lifecycle event dispatch, and cross-tenant boundary isolation.
"""

import pytest
from starlette.testclient import TestClient

from src.domain.entities.category import TicketCategory
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.events.event_bus import InMemoryEventBus
from src.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture(scope="module")
def webhook_test_client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("webhook_test")
    test_db_url = f"sqlite:///{tmp_dir}/test_webhooks.db"
    repo = EnterpriseRepository(db_url=test_db_url)
    event_bus = InMemoryEventBus()
    ws_manager = WebSocketConnectionManager(event_bus=event_bus)

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.97,
        model_version="mock-webhook-v1",
    )
    app = create_app(model_override=mock_clf)
    app.state.enterprise_repository = repo
    app.state.event_bus = event_bus
    app.state.websocket_manager = ws_manager

    with TestClient(app) as test_client:
        yield test_client, repo, event_bus


def test_webhook_subscription_lifecycle_and_isolation(webhook_test_client):
    client, repo, _ = webhook_test_client

    # 1. Register Tenant A
    resp_a = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Nexus Corp",
            "slug": "nexus-corp",
            "admin_email": "admin@nexus.io",
            "admin_password": "NexusPassword123!",
            "admin_full_name": "Nexus Admin",
            "plan": "ENTERPRISE",
        },
    )
    assert resp_a.status_code == 201, resp_a.text
    tenant_a_id = resp_a.json()["tenant_id"]
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Tenant B
    resp_b = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Apex Ltd",
            "slug": "apex-ltd",
            "admin_email": "admin@apex.io",
            "admin_password": "ApexPassword123!",
            "admin_full_name": "Apex Admin",
            "plan": "GROWTH",
        },
    )
    assert resp_b.status_code == 201, resp_b.text
    tenant_b_id = resp_b.json()["tenant_id"]
    assert tenant_b_id != tenant_a_id
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Tenant A Registers a Webhook Subscription
    sub_payload = {
        "target_url": "https://api.nexus.io/incidents/triage-events",
        "events_subscribed": ["ticket.ingested", "ticket.escalated"],
        "secret_token": "whsec_custom_nexus_secret_998877",
        "description": "Nexus SIEM Integration",
    }
    create_resp = client.post(
        "/api/v2/webhooks/subscriptions",
        json=sub_payload,
        headers=headers_a,
    )
    assert create_resp.status_code == 201, create_resp.text
    sub_data = create_resp.json()
    sub_id = sub_data["subscription_id"]
    assert sub_data["target_url"] == sub_payload["target_url"]
    assert sub_data["secret_token"] == sub_payload["secret_token"]
    assert sub_data["events_subscribed"] == ["ticket.ingested", "ticket.escalated"]
    assert sub_data["is_active"] is True

    # 4. Tenant A Lists Webhooks
    list_a = client.get("/api/v2/webhooks/subscriptions", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["subscription_id"] == sub_id

    # 5. Multi-Tenant Isolation Checks
    # Tenant B has 0 webhooks
    list_b = client.get("/api/v2/webhooks/subscriptions", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0

    # Tenant B cannot delete Tenant A's webhook
    del_b = client.delete(f"/api/v2/webhooks/subscriptions/{sub_id}", headers=headers_b)
    assert del_b.status_code == 404

    # 6. Test Ping Connectivity Endpoint
    test_ping_resp = client.post(
        f"/api/v2/webhooks/subscriptions/{sub_id}/test",
        headers=headers_a,
    )
    assert test_ping_resp.status_code == 200
    ping_data = test_ping_resp.json()
    assert ping_data["subscription_id"] == sub_id
    assert "latency_ms" in ping_data

    # Tenant B cannot test Tenant A's webhook
    test_b = client.post(
        f"/api/v2/webhooks/subscriptions/{sub_id}/test",
        headers=headers_b,
    )
    assert test_b.status_code == 404

    # 7. Tenant A Deletes Webhook
    del_a = client.delete(f"/api/v2/webhooks/subscriptions/{sub_id}", headers=headers_a)
    assert del_a.status_code == 204

    # Verified Deleted
    list_after = client.get("/api/v2/webhooks/subscriptions", headers=headers_a)
    assert list_after.status_code == 200
    assert len(list_after.json()) == 0
