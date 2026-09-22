"""
Unit Tests for Slack Block Kit Notifier, PagerDuty Events API v2, and HMAC-SHA256 Webhooks.
"""

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.domain.entities.webhook import WebhookSubscription
from src.infrastructure.notifications.pagerduty_notifier import PagerDutyNotifier
from src.infrastructure.notifications.slack_notifier import SlackBlockKitNotifier
from src.infrastructure.notifications.webhook_dispatcher import WebhookDispatcher

# ==============================================================================
# 1. Slack Block Kit Alert Tests
# ==============================================================================

def test_slack_block_kit_critical_incident_payload():
    event = EnterpriseEvent(
        event_type=EnterpriseEventType.TICKET_INGESTED,
        tenant_id="tenant-alpha",
        ticket_id="TCK-9402",
        payload={
            "priority": "P1_CRITICAL",
            "predicted_category": "Access & Security",
            "assigned_team": "Security Operations Center (SOC)",
            "confidence": 0.948,
            "customer_id": "cust-acme-global",
            "customer_tier": "VIP_ENTERPRISE",
            "description": "Production database credentials compromised in git push.",
        },
    )

    payload = SlackBlockKitNotifier.build_block_kit_payload(event, channel="#critical-ops")

    assert payload["channel"] == "#critical-ops"
    blocks = payload["blocks"]
    assert len(blocks) >= 4

    # Header check
    assert blocks[0]["type"] == "header"
    assert "CRITICAL INCIDENT AUTO-TRIAGED" in blocks[0]["text"]["text"]

    # Fields check
    fields_block = blocks[1]
    assert fields_block["type"] == "section"
    field_texts = [f["text"] for f in fields_block["fields"]]
    assert any("#TCK-9402" in t for t in field_texts)
    assert any("P1_CRITICAL" in t for t in field_texts)
    assert any("Security Operations Center (SOC)" in t for t in field_texts)
    assert any("94.8%" in t for t in field_texts)

    # Actions check
    actions_block = blocks[3]
    assert actions_block["type"] == "actions"
    action_ids = [el["action_id"] for el in actions_block["elements"]]
    assert "ack_ticket" in action_ids
    assert "escalate_ticket" in action_ids


def test_slack_block_kit_escalation_and_warning_headers():
    # Escalated
    esc_event = EnterpriseEvent(
        event_type=EnterpriseEventType.TICKET_ESCALATED,
        tenant_id="tenant-1",
        ticket_id="TCK-111",
        payload={"priority": "P1_CRITICAL", "description": "Escalated to Tier 3"},
    )
    esc_payload = SlackBlockKitNotifier.build_block_kit_payload(esc_event)
    assert "ESCALATED TO TIER 3" in esc_payload["blocks"][0]["text"]["text"]

    # SLA Warning
    warn_event = EnterpriseEvent(
        event_type=EnterpriseEventType.SLA_WARNING,
        tenant_id="tenant-1",
        ticket_id="TCK-222",
        payload={"priority": "P2_HIGH", "description": "Warning 75% elapsed"},
    )
    warn_payload = SlackBlockKitNotifier.build_block_kit_payload(warn_event)
    assert "SLA BREACH COUNTDOWN WARNING" in warn_payload["blocks"][0]["text"]["text"]


# ==============================================================================
# 2. PagerDuty Events API v2 Tests
# ==============================================================================

def test_pagerduty_payload_critical_trigger():
    event = EnterpriseEvent(
        event_type=EnterpriseEventType.TICKET_INGESTED,
        tenant_id="tenant-alpha",
        ticket_id="TCK-9402",
        payload={
            "priority": "P1_CRITICAL",
            "predicted_category": "Network",
            "assigned_team": "Network NOC",
            "confidence": 0.96,
            "customer_id": "cust-001",
        },
    )

    pd_payload = PagerDutyNotifier.build_event_payload(
        routing_key="pd-sec-service-key-xyz",
        event=event,
    )

    assert pd_payload["routing_key"] == "pd-sec-service-key-xyz"
    assert pd_payload["event_action"] == "trigger"
    assert pd_payload["dedup_key"] == "tenant-alpha:TCK-9402"
    assert pd_payload["payload"]["severity"] == "critical"
    assert "P1_CRITICAL" in pd_payload["payload"]["summary"]
    assert pd_payload["payload"]["custom_details"]["assigned_team"] == "Network NOC"


def test_pagerduty_payload_resolution_action():
    event = EnterpriseEvent(
        event_type=EnterpriseEventType.TICKET_RESOLVED,
        tenant_id="tenant-alpha",
        ticket_id="TCK-9402",
        payload={"priority": "P1_CRITICAL"},
    )

    pd_payload = PagerDutyNotifier.build_event_payload(
        routing_key="pd-key",
        event=event,
    )

    assert pd_payload["event_action"] == "resolve"
    assert pd_payload["dedup_key"] == "tenant-alpha:TCK-9402"
    assert "resolved by support agent" in pd_payload["payload"]["summary"]


# ==============================================================================
# 3. HMAC-SHA256 Webhook Signature & Verification Tests
# ==============================================================================

def test_webhook_hmac_signature_generation():
    secret = "whsec_super_secret_test_token_12345"
    payload = b'{"event":"ticket.ingested","ticket_id":"123"}'

    signature = WebhookDispatcher.compute_signature(secret, payload)
    assert signature.startswith("sha256=")
    assert len(signature) == 7 + 64  # 'sha256=' + 64 hex characters

    # Deterministic check
    signature2 = WebhookDispatcher.compute_signature(secret, payload)
    assert signature == signature2


def test_webhook_hmac_signature_verification():
    secret = "whsec_super_secret_test_token_12345"
    payload = b'{"event":"ticket.ingested","ticket_id":"123"}'
    valid_signature = WebhookDispatcher.compute_signature(secret, payload)

    # Valid
    assert WebhookDispatcher.verify_signature(secret, payload, valid_signature) is True

    # Tampered payload
    tampered_payload = b'{"event":"ticket.ingested","ticket_id":"999"}'
    assert WebhookDispatcher.verify_signature(secret, tampered_payload, valid_signature) is False

    # Wrong secret
    wrong_secret = "whsec_different_token_99999"
    assert WebhookDispatcher.verify_signature(wrong_secret, payload, valid_signature) is False

    # Invalid header format
    assert WebhookDispatcher.verify_signature(secret, payload, "invalid_sig") is False
    assert WebhookDispatcher.verify_signature(secret, payload, "") is False


# ==============================================================================
# 4. Webhook Subscription Domain Entity Tests
# ==============================================================================

def test_webhook_subscription_filtering():
    # Wildcard subscription
    sub_wildcard = WebhookSubscription(
        tenant_id="tenant-1",
        target_url="https://api.gateway.io/all-events",
        secret_token="secret-1",
        events_subscribed=["*"],
    )
    assert sub_wildcard.is_subscribed_to("ticket.ingested") is True
    assert sub_wildcard.is_subscribed_to("ticket.escalated") is True

    # Specific subscription
    sub_specific = WebhookSubscription(
        tenant_id="tenant-1",
        target_url="https://api.gateway.io/escalations",
        secret_token="secret-2",
        events_subscribed=["ticket.escalated", "ticket.sla_warning"],
    )
    assert sub_specific.is_subscribed_to("ticket.escalated") is True
    assert sub_specific.is_subscribed_to("ticket.sla_warning") is True
    assert sub_specific.is_subscribed_to("ticket.ingested") is False

    # Inactive subscription
    sub_inactive = WebhookSubscription(
        tenant_id="tenant-1",
        target_url="https://api.gateway.io/disabled",
        secret_token="secret-3",
        events_subscribed=["*"],
        is_active=False,
    )
    assert sub_inactive.is_subscribed_to("ticket.ingested") is False
