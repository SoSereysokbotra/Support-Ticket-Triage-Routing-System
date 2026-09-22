"""
Integration Tests for SLA Breach Watchdog & Automated Escalation Engine (API v2).
Verifies deadline persistence, at-risk queries, manual escalation, on-demand evaluation,
and strict multi-tenant boundary compliance for SLA operations.
"""

from datetime import datetime, timedelta, timezone

import pytest
from starlette.testclient import TestClient

from src.domain.entities.category import TicketCategory
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.workers.sla_watchdog_worker import SLAWatchdogWorker
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture(scope="module")
def client_and_repo(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("sla_test")
    test_db_url = f"sqlite:///{tmp_dir}/test_sla.db"
    repo = EnterpriseRepository(db_url=test_db_url)

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.95,
        model_version="mock-sla-v1",
    )
    app = create_app(model_override=mock_clf)
    app.state.enterprise_repository = repo
    watchdog = SLAWatchdogWorker(repository=repo, poll_interval_seconds=60)
    app.state.sla_watchdog = watchdog

    with TestClient(app) as test_client:
        yield test_client, repo


def test_sla_ticket_creation_and_deadlines(client_and_repo):
    client, repo = client_and_repo

    # 1. Register Tenant
    resp = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Apex Finance",
            "slug": "apex-fin",
            "admin_email": "ops@apex.com",
            "admin_password": "SecureApexPassword999!",
            "admin_full_name": "Sarah Connor",
            "plan": "ENTERPRISE",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    # 2. Ingest Ticket with VIP tier
    create_resp = client.post(
        "/api/v2/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Core Trading Gateway Timeout",
            "description": "Critical database deadlock detected on trade settlement pipelines.",
            "customer_id": "APEX-VIP-01",
            "customer_tier": "VIP_ENTERPRISE",
            "priority_hint": "Critical",
        },
    )
    assert create_resp.status_code == 201
    ticket = create_resp.json()
    assert ticket["sla_response_deadline"] is not None
    assert ticket["sla_resolution_deadline"] is not None
    assert ticket["escalated"] is False

    # 3. Verify deadlines are in the future
    res_deadline = datetime.fromisoformat(ticket["sla_resolution_deadline"])
    assert res_deadline > datetime.now(timezone.utc)


def test_sla_at_risk_query(client_and_repo):
    client, repo = client_and_repo

    # Login to Apex Finance
    login_resp = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "apex-fin",
            "email": "ops@apex.com",
            "password": "SecureApexPassword999!",
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Current tickets are brand new, so 0 at-risk
    at_risk_resp = client.get(
        "/api/v2/sla/at-risk",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert at_risk_resp.status_code == 200
    at_risk = at_risk_resp.json()
    assert isinstance(at_risk, list)
    assert len(at_risk) == 0


def test_manual_ticket_escalation(client_and_repo):
    client, repo = client_and_repo

    token = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "apex-fin",
            "email": "ops@apex.com",
            "password": "SecureApexPassword999!",
        },
    ).json()["access_token"]

    # Ingest a ticket
    ticket_data = client.post(
        "/api/v2/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Payment Settlement Interruption",
            "description": "Credit card batch processing stuck in processing queue.",
            "customer_id": "APEX-VIP-02",
            "customer_tier": "VIP_ENTERPRISE",
        },
    ).json()
    ticket_id = ticket_data["ticket_id"]

    # Escalate ticket
    escalate_resp = client.post(
        f"/api/v2/tickets/{ticket_id}/escalate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "reason": "Executive intervention requested by VP of Engineering.",
            "new_team": "Tier-3 Senior Escalations",
        },
    )
    assert escalate_resp.status_code == 200
    escalated = escalate_resp.json()
    assert escalated["escalated"] is True
    assert escalated["escalation_reason"] == "Executive intervention requested by VP of Engineering."
    assert escalated["assigned_team"] == "Tier-3 Senior Escalations"

    # Confirm persistence
    fetch_resp = client.get(
        f"/api/v2/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fetch_resp.status_code == 200
    fetched = fetch_resp.json()
    assert fetched["escalated"] is True


def test_sla_watchdog_evaluate_endpoint(client_and_repo):
    client, repo = client_and_repo

    token = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "apex-fin",
            "email": "ops@apex.com",
            "password": "SecureApexPassword999!",
        },
    ).json()["access_token"]

    # Evaluate SLA on-demand
    eval_resp = client.post(
        "/api/v2/sla/evaluate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert eval_resp.status_code == 200
    report = eval_resp.json()
    assert "scanned_count" in report
    assert "warnings_emitted" in report
    assert "breached_and_escalated" in report
    assert report["scanned_count"] >= 2


def test_cross_tenant_escalation_isolation(client_and_repo):
    client, repo = client_and_repo

    # Register second tenant: Beta Corp
    resp_beta = client.post(
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
    assert resp_beta.status_code == 201
    token_beta = resp_beta.json()["access_token"]

    # Apex token
    token_apex = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "apex-fin",
            "email": "ops@apex.com",
            "password": "SecureApexPassword999!",
        },
    ).json()["access_token"]

    # Create ticket under Apex
    apex_ticket = client.post(
        "/api/v2/tickets",
        headers={"Authorization": f"Bearer {token_apex}"},
        json={
            "title": "Private Security Incident",
            "description": "Suspicious login attempt reported on admin portal.",
            "customer_id": "APEX-SEC-01",
        },
    ).json()
    apex_ticket_id = apex_ticket["ticket_id"]

    # Beta attempts to escalate Apex's ticket -> 404 Not Found (Cross-tenant leak rejected)
    bad_escalate = client.post(
        f"/api/v2/tickets/{apex_ticket_id}/escalate",
        headers={"Authorization": f"Bearer {token_beta}"},
        json={
            "reason": "Hostile takeover attempt",
        },
    )
    assert bad_escalate.status_code == 404
