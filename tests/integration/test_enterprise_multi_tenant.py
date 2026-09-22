"""
Integration Tests for Enterprise Multi-Tenancy & Data Isolation (API v2).
Verifies tenant onboarding, JWT authentication, and strict cross-tenant data isolation.
"""

import pytest
from starlette.testclient import TestClient

from src.domain.entities.category import TicketCategory
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.presentation.api.app import create_app
from tests.conftest import MockTicketClassifier


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("enterprise_test")
    test_db_url = f"sqlite:///{tmp_dir}/test_multi_tenant.db"
    repo = EnterpriseRepository(db_url=test_db_url)

    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.NETWORK,
        confidence=0.95,
        model_version="mock-tenant-v1",
    )
    app = create_app(model_override=mock_clf)
    app.state.enterprise_repository = repo

    with TestClient(app) as test_client:
        yield test_client


def test_tenant_registration_and_jwt_issuance(client):
    # Register Tenant A
    resp_a = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Acme Industries",
            "slug": "acme-ind",
            "admin_email": "admin@acme.com",
            "admin_password": "StrongPassword123!",
            "admin_full_name": "Alice Admin",
            "plan": "ENTERPRISE",
        },
    )
    assert resp_a.status_code == 201
    data_a = resp_a.json()
    assert "access_token" in data_a
    assert data_a["company_name"] == "Acme Industries"
    assert data_a["role"] == "TENANT_ADMIN"

    # Register Tenant B
    resp_b = client.post(
        "/api/v2/auth/register-tenant",
        json={
            "company_name": "Globex Corporation",
            "slug": "globex-corp",
            "admin_email": "admin@globex.com",
            "admin_password": "GlobexPassword456!",
            "admin_full_name": "Bob Admin",
            "plan": "GROWTH",
        },
    )
    assert resp_b.status_code == 201
    data_b = resp_b.json()
    assert "access_token" in data_b
    assert data_b["company_name"] == "Globex Corporation"
    assert data_b["tenant_id"] != data_a["tenant_id"]


def test_auth_me_and_token_validation(client):
    # 1. Login to get fresh token
    login_resp = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "acme-ind",
            "email": "admin@acme.com",
            "password": "StrongPassword123!",
        },
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 2. Inspect profile
    me_resp = client.get("/api/v2/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["email"] == "admin@acme.com"
    assert profile["role"] == "TENANT_ADMIN"

    # 3. Reject unauthenticated request
    no_auth_resp = client.get("/api/v2/auth/me")
    assert no_auth_resp.status_code == 422 or no_auth_resp.status_code == 401

    # 4. Reject invalid password
    bad_login = client.post(
        "/api/v2/auth/login",
        json={
            "tenant_slug": "acme-ind",
            "email": "admin@acme.com",
            "password": "WrongPassword!",
        },
    )
    assert bad_login.status_code == 401


def test_strict_tenant_ticket_isolation(client):
    # 1. Obtain Tokens for Acme and Globex
    token_acme = client.post(
        "/api/v2/auth/login",
        json={"tenant_slug": "acme-ind", "email": "admin@acme.com", "password": "StrongPassword123!"},
    ).json()["access_token"]

    token_globex = client.post(
        "/api/v2/auth/login",
        json={"tenant_slug": "globex-corp", "email": "admin@globex.com", "password": "GlobexPassword456!"},
    ).json()["access_token"]

    # 2. Ingest Ticket under Tenant Acme
    create_ticket_resp = client.post(
        "/api/v2/tickets",
        headers={"Authorization": f"Bearer {token_acme}"},
        json={
            "title": "VPN Authentication Drop",
            "description": "I cannot connect to the corporate VPN from the home office network.",
            "customer_id": "ACME-EMP-104",
            "customer_tier": "VIP_ENTERPRISE",
            "priority_hint": "High",
        },
    )
    assert create_ticket_resp.status_code == 201
    acme_ticket = create_ticket_resp.json()
    ticket_id = acme_ticket["ticket_id"]
    assert acme_ticket["predicted_category"] == "Network"
    assert acme_ticket["assigned_team"] in ["Network Operations Center (NOC)", "Tier-1 Human Triage Queue"]
    assert acme_ticket["priority"] in ["P1_CRITICAL", "P2_HIGH"]

    # 3. Tenant Acme lists tickets -> Sees the ticket
    acme_list = client.get("/api/v2/tickets", headers={"Authorization": f"Bearer {token_acme}"})
    assert acme_list.status_code == 200
    acme_tickets = acme_list.json()
    assert len(acme_tickets) >= 1
    assert any(t["ticket_id"] == ticket_id for t in acme_tickets)

    # 4. Tenant Globex lists tickets -> Strict Isolation: Sees 0 tickets
    globex_list = client.get("/api/v2/tickets", headers={"Authorization": f"Bearer {token_globex}"})
    assert globex_list.status_code == 200
    globex_tickets = globex_list.json()
    assert len(globex_tickets) == 0

    # 5. Tenant Globex directly requests Acme's ticket_id -> 404 Not Found
    leak_attempt = client.get(
        f"/api/v2/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token_globex}"},
    )
    assert leak_attempt.status_code == 404
    assert "not found in current tenant" in leak_attempt.json()["detail"].lower()

    # 6. Tenant Acme directly requests its own ticket_id -> 200 OK
    valid_fetch = client.get(
        f"/api/v2/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token_acme}"},
    )
    assert valid_fetch.status_code == 200
    assert valid_fetch.json()["ticket_id"] == ticket_id
