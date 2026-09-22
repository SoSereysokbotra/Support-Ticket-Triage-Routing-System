"""
Integration Tests for Real-Time WebSocket Triage Stream (API v2).
Verifies JWT query parameter authentication, ping/pong heartbeats,
real-time event dispatch upon ticket creation and escalation,
and strict cross-tenant notification isolation.
"""

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.domain.entities.category import TicketCategory
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.events.event_bus import InMemoryEventBus
from src.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture(scope="module")
def ws_test_client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("ws_test")
    test_db_url = f"sqlite:///{tmp_dir}/test_ws.db"
    repo = EnterpriseRepository(db_url=test_db_url)
    event_bus = InMemoryEventBus()
    ws_manager = WebSocketConnectionManager(event_bus=event_bus)

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.96,
        model_version="mock-ws-v1",
    )
    app = create_app(model_override=mock_clf)
    app.state.enterprise_repository = repo
    app.state.event_bus = event_bus
    app.state.websocket_manager = ws_manager

    with TestClient(app) as test_client:
        yield test_client, repo


def test_websocket_auth_rejection_without_token(ws_test_client):
    client, _ = ws_test_client
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v2/ws/triage") as ws:
            ws.receive_json()


def test_websocket_auth_rejection_with_invalid_token(ws_test_client):
    client, _ = ws_test_client
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v2/ws/triage?token=invalid.jwt.token") as ws:
            ws.receive_json()


def test_websocket_successful_handshake_and_ping_pong(ws_test_client):
    client, _ = ws_test_client

    # 1. Register Tenant
    resp = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "StreamLine Ops",
            "slug": "streamline-ops",
            "admin_email": "ops@streamline.com",
            "admin_password": "StreamPassword123!",
            "admin_full_name": "Stream Admin",
            "plan": "ENTERPRISE",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    tenant_id = resp.json()["tenant_id"]

    # 2. Connect via WebSocket with token
    with client.websocket_connect(f"/api/v2/ws/triage?token={token}") as ws:
        # Handshake confirmation
        handshake = ws.receive_json()
        assert handshake["type"] == "connection_established"
        assert handshake["tenant_id"] == tenant_id

        # Ping -> Pong heartbeat
        ws.send_text("ping")
        pong = ws.receive_json()
        assert pong["type"] == "pong"


def test_realtime_ticket_ingestion_and_escalation_broadcast(ws_test_client):
    client, _ = ws_test_client

    # Login to StreamLine Ops
    login_resp = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "streamline-ops",
            "email": "ops@streamline.com",
            "password": "StreamPassword123!",
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Open live agent WebSocket connection
    with client.websocket_connect(f"/api/v2/ws/triage?token={token}") as ws:
        handshake = ws.receive_json()
        assert handshake["type"] == "connection_established"

        # 1. Ingest a new ticket via HTTP POST while WebSocket is open
        create_resp = client.post(
            "/api/v2/tickets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "BGP Route Flapping in Region East",
                "description": "Primary border gateway protocol peering sessions flapping continuously.",
                "customer_id": "STREAM-CUST-88",
                "customer_tier": "VIP_ENTERPRISE",
                "priority_hint": "Critical",
            },
        )
        assert create_resp.status_code == 201
        created_ticket = create_resp.json()
        ticket_id = created_ticket["ticket_id"]

        # 2. WebSocket receives TICKET_INGESTED event
        ingested_event = ws.receive_json()
        assert ingested_event["event_type"] == "ticket.ingested"
        assert ingested_event["ticket_id"] == ticket_id
        assert ingested_event["payload"]["title"] == "BGP Route Flapping in Region East"
        assert ingested_event["payload"]["priority"] == "P1_CRITICAL"

        # 3. Escalate ticket via HTTP POST
        escalate_resp = client.post(
            f"/api/v2/tickets/{ticket_id}/escalate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reason": "Outage impacting multiple tier-1 customers",
                "new_team": "Tier-3 Senior Escalations",
            },
        )
        assert escalate_resp.status_code == 200

        # 4. WebSocket receives TICKET_ESCALATED event
        escalated_event = ws.receive_json()
        assert escalated_event["event_type"] == "ticket.escalated"
        assert escalated_event["ticket_id"] == ticket_id
        assert "Outage impacting" in escalated_event["payload"]["escalation_reason"]


def test_cross_tenant_websocket_isolation(ws_test_client):
    client, _ = ws_test_client

    # 1. Register Second Tenant: Nebula Cloud
    resp_b = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Nebula Cloud",
            "slug": "nebula-cloud",
            "admin_email": "admin@nebula.com",
            "admin_password": "NebulaPassword999!",
            "admin_full_name": "Nebula Admin",
            "plan": "GROWTH",
        },
    )
    assert resp_b.status_code == 201
    token_nebula = resp_b.json()["access_token"]

    token_stream = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "streamline-ops",
            "email": "ops@streamline.com",
            "password": "StreamPassword123!",
        },
    ).json()["access_token"]

    # 2. Open WebSockets for both tenants concurrently
    with (
        client.websocket_connect(f"/api/v2/ws/triage?token={token_stream}") as ws_stream,
        client.websocket_connect(f"/api/v2/ws/triage?token={token_nebula}") as ws_nebula,
    ):
        # Consume handshakes
        assert ws_stream.receive_json()["type"] == "connection_established"
        assert ws_nebula.receive_json()["type"] == "connection_established"

        # 3. Ingest ticket for StreamLine Ops
        ticket_resp = client.post(
            "/api/v2/tickets",
            headers={"Authorization": f"Bearer {token_stream}"},
            json={
                "title": "Private Tenant Incident",
                "description": "Tenant specific internal incident notification.",
                "customer_id": "STREAM-PRIV-01",
            },
        )
        assert ticket_resp.status_code == 201

        # StreamLine socket receives event
        event = ws_stream.receive_json()
        assert event["event_type"] == "ticket.ingested"
        assert event["ticket_id"] == ticket_resp.json()["ticket_id"]

        # Nebula socket sends ping/pong and receives only its pong, proving no event leaked
        ws_nebula.send_text("ping")
        pong = ws_nebula.receive_json()
        assert pong["type"] == "pong"


def test_websocket_stats_endpoint(ws_test_client):
    client, _ = ws_test_client

    token = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "streamline-ops",
            "email": "ops@streamline.com",
            "password": "StreamPassword123!",
        },
    ).json()["access_token"]

    stats_resp = client.get(
        "/api/v2/ws/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "active_agent_connections" in stats
    assert "cluster_total_connections" in stats
