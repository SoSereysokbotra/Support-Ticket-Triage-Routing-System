"""
Slack Interactive Block Kit Alert Dispatcher.
Formats and transmits high-visibility incident notification cards for critical tickets and SLA breaches.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any, Dict

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType

logger = logging.getLogger("slack_notifier")


class SlackBlockKitNotifier:
    """
    Renders and delivers rich, interactive Slack messages matching Enterprise Block Kit specifications.
    Enables support leads and on-call engineers to claim or escalate incidents in 1-click.
    """

    @classmethod
    def build_block_kit_payload(
        cls,
        event: EnterpriseEvent,
        channel: str = "#incident-response",
    ) -> Dict[str, Any]:
        """Constructs an interactive Slack Block Kit JSON payload from a domain event."""
        payload_data = event.payload
        ticket_id = event.ticket_id
        priority = payload_data.get("priority", "UNKNOWN")
        category = payload_data.get("predicted_category", payload_data.get("category", "General"))
        assigned_team = payload_data.get("assigned_team", "Tier 1 Operations")
        confidence = payload_data.get("confidence", 0.0)
        customer_id = payload_data.get("customer_id", "Anonymous")
        customer_tier = payload_data.get("customer_tier", "STANDARD")
        description = payload_data.get("description", payload_data.get("title", "No details provided."))
        summary_snippet = (description[:180] + "...") if len(description) > 180 else description

        # Determine header icon and title based on event type
        if event.event_type == EnterpriseEventType.TICKET_ESCALATED:
            header_text = "🚨 CRITICAL INCIDENT ESCALATED TO TIER 3"
        elif event.event_type == EnterpriseEventType.SLA_WARNING:
            header_text = "⚠️ SLA BREACH COUNTDOWN WARNING (75% ELAPSED)"
        else:
            header_text = "🚨 CRITICAL INCIDENT AUTO-TRIAGED"

        confidence_pct = f"{confidence:.1%}" if isinstance(confidence, (int, float)) and confidence > 0 else "N/A"

        return {
            "channel": channel,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": header_text, "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Ticket ID:*\n#{ticket_id}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{priority}"},
                        {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                        {"type": "mrkdwn", "text": f"*Assigned Team:*\n{assigned_team}"},
                        {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence_pct} (ONNX DistilBERT)"},
                        {"type": "mrkdwn", "text": f"*Customer Tier:*\n{customer_tier}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Customer:* `{customer_id}`\n*Telemetry:* {summary_snippet}",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Acknowledge Incident", "emoji": True},
                            "style": "primary",
                            "action_id": "ack_ticket",
                            "value": ticket_id,
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Reassign to Tier 3", "emoji": True},
                            "style": "danger",
                            "action_id": "escalate_ticket",
                            "value": ticket_id,
                        },
                    ],
                },
            ],
        }

    @classmethod
    def send_alert(
        cls,
        webhook_url: str,
        event: EnterpriseEvent,
        channel: str = "#incident-response",
        timeout: float = 5.0,
    ) -> bool:
        """Transmits the Block Kit notification to the designated Slack webhook URL."""
        if not webhook_url:
            return False

        payload = cls.build_block_kit_payload(event=event, channel=channel)
        encoded_data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            webhook_url,
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                return 200 <= status_code < 300
        except Exception as e:
            logger.warning(f"Failed to deliver Slack Block Kit alert for ticket '{event.ticket_id}': {e}")
            return False
