"""
Integration Tests for Copilot Resolution Drafting and HITL Agent Feedback (API v2).
Verifies end-to-end feedback capture, high-confidence error weighting, active retraining triggers,
SOP-grounded Copilot resolution drafts with PII sanitization, 1-click agent approval,
and strict multi-tenant boundary isolation.
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
def copilot_test_client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("copilot_test")
    test_db_url = f"sqlite:///{tmp_dir}/test_copilot.db"
    repo = EnterpriseRepository(db_url=test_db_url)
    event_bus = InMemoryEventBus()
    ws_manager = WebSocketConnectionManager(event_bus=event_bus)

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.95,
        model_version="mock-copilot-v1",
    )
    app = create_app(model_override=mock_clf)
    app.state.enterprise_repository = repo
    app.state.event_bus = event_bus
    app.state.websocket_manager = ws_manager

    with TestClient(app) as test_client:
        yield test_client, repo, event_bus


def test_copilot_and_feedback_lifecycle(copilot_test_client):
    client, repo, event_bus = copilot_test_client

    # 1. Register Tenant A
    resp = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Acme Global",
            "slug": "acme-global",
            "admin_email": "admin@acme.com",
            "admin_password": "AcmePassword123!",
            "admin_full_name": "Acme Admin",
            "plan": "ENTERPRISE",
        },
    )
    assert resp.status_code == 201, resp.text
    tenant_a_id = resp.json()["tenant_id"]
    token_a = resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Tenant B (for cross-tenant checks)
    resp_b = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Beta Corp",
            "slug": "beta-corp",
            "admin_email": "admin@beta.com",
            "admin_password": "BetaPassword123!",
            "admin_full_name": "Beta Admin",
            "plan": "GROWTH",
        },
    )
    assert resp_b.status_code == 201, resp_b.text
    token_b = resp_b.json()["access_token"]
    tenant_b_id = resp_b.json()["tenant_id"]
    assert tenant_b_id != tenant_a_id
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create a Ticket in Tenant A with sensitive telemetry (PII)
    ticket_payload = {
        "title": "VPN Gateway TLS Handshake Timeout",
        "description": "AnyConnect VPN keeps dropping for user contact@acme.com, card on file 4111-2222-3333-4444.",
        "customer_id": "cust-acme-001",
    }
    t_resp = client.post("/api/v2/tickets", json=ticket_payload, headers=headers_a)
    assert t_resp.status_code == 201, t_resp.text
    ticket_a = t_resp.json()
    ticket_id = ticket_a["ticket_id"]
    assert ticket_a["predicted_category"] == "Network"
    assert ticket_a["confidence"] >= 0.90

    # 4. Generate Grounded Copilot Resolution Draft (RAG)
    gen_resp = client.post(f"/api/v2/tickets/{ticket_id}/copilot/generate", headers=headers_a)
    assert gen_resp.status_code == 200, gen_resp.text
    draft_data = gen_resp.json()
    assert draft_data["ticket_id"] == ticket_id
    assert draft_data["is_skipped"] is False
    assert draft_data["suggested_response"] is not None
    assert "Grounded in Standard Operating Procedure" in draft_data["suggested_response"]
    assert "SOP-NET-001" in draft_data["suggested_response"]
    # Verify raw PII was sanitized before RAG processing
    assert "4111-2222-3333-4444" not in draft_data["suggested_response"]
    assert draft_data["copilot_confidence"] > 0.80
    assert len(draft_data["sources"]) > 0

    # 5. Cross-Tenant Check: Tenant B cannot generate copilot draft for Tenant A's ticket
    b_gen = client.post(f"/api/v2/tickets/{ticket_id}/copilot/generate", headers=headers_b)
    assert b_gen.status_code == 404

    # 6. Submit Agent Ground-Truth Reclassification Feedback (HITL)
    # Agent reclassifies Network -> Security (High confidence false positive: 0.95 conf, error weight = 3x)
    fb_payload = {
        "corrected_category": "Security",
        "corrected_priority": "CRITICAL",
        "reclassification_reason": "Repeated tunnel drops indicate a brute force attack on the gateway.",
    }
    fb_resp = client.post(f"/api/v2/tickets/{ticket_id}/feedback", json=fb_payload, headers=headers_a)
    assert fb_resp.status_code == 201, fb_resp.text
    fb_data = fb_resp.json()
    assert fb_data["original_category"] == "Network"
    assert fb_data["corrected_category"] == "Security"
    assert fb_data["is_high_confidence_error"] is True
    assert fb_data["sample_weight"] == 3.0
    assert fb_data["reclassification_reason"] == fb_payload["reclassification_reason"]

    # 7. Check Feedback Statistics for Tenant A
    stats_resp = client.get("/api/v2/tickets/feedback/stats", headers=headers_a)
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["total_annotations"] == 1
    assert stats_data["unprocessed_annotations"] == 1
    assert stats_data["high_confidence_false_positives"] == 1
    assert stats_data["retraining_threshold_reached"] is False

    # 8. Multi-Tenant Check: Tenant B has 0 annotations
    stats_b = client.get("/api/v2/tickets/feedback/stats", headers=headers_b)
    assert stats_b.status_code == 200
    assert stats_b.json()["total_annotations"] == 0

    # Tenant B cannot submit feedback on Tenant A's ticket
    fb_b = client.post(f"/api/v2/tickets/{ticket_id}/feedback", json=fb_payload, headers=headers_b)
    assert fb_b.status_code == 404

    # 9. 1-Click Copilot Approval (Resolves Ticket)
    approve_resp = client.post(f"/api/v2/tickets/{ticket_id}/copilot/approve", headers=headers_a)
    assert approve_resp.status_code == 200, approve_resp.text
    resolved_ticket = approve_resp.json()
    assert resolved_ticket["status"] == "RESOLVED"
    assert resolved_ticket["resolved_at"] is not None
    assert resolved_ticket["copilot_suggested_response"] is not None
    assert "Grounded in Standard Operating Procedure" in resolved_ticket["copilot_suggested_response"]

    # Tenant B cannot approve Tenant A's ticket
    b_approve = client.post(f"/api/v2/tickets/{ticket_id}/copilot/approve", headers=headers_b)
    assert b_approve.status_code == 404


def test_copilot_low_confidence_gate(copilot_test_client):
    client, repo, _ = copilot_test_client

    # 1. Login or register tenant
    resp = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "LowConf Corp",
            "slug": "lowconf-corp",
            "admin_email": "admin@lowconf.com",
            "admin_password": "LowConfPassword123!",
            "admin_full_name": "Low Conf Admin",
            "plan": "STARTER",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    tenant_id = resp.json()["tenant_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Directly create a low-confidence ticket in repository (< 0.60 floor)
    from src.domain.entities.tenant import EnterpriseTicket, TicketPriority, TicketStatus
    low_conf_ticket = EnterpriseTicket(
        ticket_id="tick-low-conf-test-999",
        tenant_id=tenant_id,
        title="Ambiguous system message",
        description="Something is weird with the widget",
        customer_id="user-999",
        predicted_category="Software",
        confidence=0.42,  # Low confidence
        probabilities={"Software": 0.42, "Hardware": 0.30},
        assigned_team="Tier 1 Support",
        latency_ms=10.0,
        model_version="mock-v1",
        priority=TicketPriority.P4_LOW,
        status=TicketStatus.OPEN,
    )
    repo.save_ticket(low_conf_ticket)

    # 3. Call Copilot generate
    resp_gate = client.post(f"/api/v2/tickets/{low_conf_ticket.ticket_id}/copilot/generate", headers=headers)
    assert resp_gate.status_code == 200
    gate_data = resp_gate.json()
    assert gate_data["is_skipped"] is True
    assert gate_data["suggested_response"] is None
    assert gate_data["copilot_confidence"] == 0.0
    assert "below the safety threshold" in gate_data["skip_reason"]
