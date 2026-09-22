"""
PagerDuty Events API v2 Dispatcher.
Dispatches high-urgency on-call incident notifications with deterministic deduplication keys.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType

logger = logging.getLogger("pagerduty_notifier")


class PagerDutyNotifier:
    """
    Integrates with PagerDuty Events API v2.
    Routes P1 Critical triage classifications and breached SLA deadlines to on-call schedules.
    """

    EVENTS_API_V2_URL = "https://events.pagerduty.com/v2/enqueue"

    SEVERITY_MAPPING: Dict[str, str] = {
        "P1_CRITICAL": "critical",
        "P2_HIGH": "error",
        "P3_MEDIUM": "warning",
        "P4_LOW": "info",
    }

    @classmethod
    def build_event_payload(
        cls,
        routing_key: str,
        event: EnterpriseEvent,
    ) -> Dict[str, Any]:
        """Constructs PagerDuty Events API v2 JSON payload."""
        payload_data = event.payload
        priority = payload_data.get("priority", "P1_CRITICAL")
        severity = cls.SEVERITY_MAPPING.get(priority, "critical")
        category = payload_data.get("predicted_category", payload_data.get("category", "General"))
        ticket_id = event.ticket_id
        tenant_id = event.tenant_id

        # Determine summary description
        if event.event_type == EnterpriseEventType.TICKET_ESCALATED:
            summary = f"[ESCALATION] Tier 3 Dispatch for Ticket #{ticket_id} ({category})"
            action = "trigger"
        elif event.event_type == EnterpriseEventType.TICKET_RESOLVED:
            summary = f"[RESOLVED] Ticket #{ticket_id} resolved by support agent."
            action = "resolve"
        else:
            summary = f"[{priority}] AI Auto-Triage: Ticket #{ticket_id} ({category})"
            action = "trigger"

        dedup_key = f"{tenant_id}:{ticket_id}"

        return {
            "routing_key": routing_key,
            "event_action": action,
            "dedup_key": dedup_key,
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": "ai-ticket-triage",
                "component": "triage-pipeline",
                "group": "support-tier-3",
                "custom_details": {
                    "ticket_id": ticket_id,
                    "tenant_id": tenant_id,
                    "priority": priority,
                    "category": category,
                    "assigned_team": payload_data.get("assigned_team", "Tier 1 Operations"),
                    "customer_id": payload_data.get("customer_id"),
                    "confidence": payload_data.get("confidence"),
                    "event_type": event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                },
            },
        }

    @classmethod
    def send_incident(
        cls,
        routing_key: str,
        event: EnterpriseEvent,
        api_url: str = EVENTS_API_V2_URL,
        timeout: float = 5.0,
    ) -> bool:
        """Sends an incident event to PagerDuty Events API v2."""
        if not routing_key:
            return False

        payload = cls.build_event_payload(routing_key=routing_key, event=event)
        encoded_data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                return 200 <= status_code < 300
        except Exception as e:
            logger.warning(f"Failed to dispatch PagerDuty alert for ticket '{event.ticket_id}': {e}")
            return False
