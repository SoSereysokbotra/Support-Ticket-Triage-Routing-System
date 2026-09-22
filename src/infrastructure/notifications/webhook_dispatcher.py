"""
Outbound Webhook Dispatcher with Cryptographic HMAC-SHA256 Signatures.
Ensures external consumers can reliably authenticate ticket event authenticity and integrity.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from typing import Optional, Tuple

from src.domain.entities.event import EnterpriseEvent
from src.domain.entities.webhook import WebhookDeliveryRecord, WebhookSubscription

logger = logging.getLogger("webhook_dispatcher")


class WebhookDispatcher:
    """
    Computes cryptographic signatures and delivers JSON event payloads to registered webhooks.
    Includes replay prevention timestamps and delivery tracking IDs.
    """

    @classmethod
    def compute_signature(cls, secret_token: str, payload_bytes: bytes) -> str:
        """
        Generates HMAC-SHA256 signature for the given payload bytes.
        Format: sha256=<hex_digest>
        """
        digest = hmac.new(
            secret_token.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    @classmethod
    def verify_signature(
        cls,
        secret_token: str,
        payload_bytes: bytes,
        signature_header: str,
    ) -> bool:
        """
        Validates HMAC-SHA256 signature in constant time to prevent timing attacks.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected_sig = cls.compute_signature(secret_token, payload_bytes)
        return hmac.compare_digest(expected_sig, signature_header)

    @classmethod
    def dispatch(
        cls,
        subscription: WebhookSubscription,
        event: EnterpriseEvent,
        timeout: float = 5.0,
    ) -> WebhookDeliveryRecord:
        """
        Delivers an event to a registered webhook URL with HMAC-SHA256 signature headers.
        Returns a delivery record capturing HTTP status code and latency.
        """
        delivery_id = str(uuid.uuid4())
        timestamp_epoch = str(int(time.time()))

        event_type_str = (
            event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type)
        )

        envelope = {
            "event_id": event.event_id,
            "delivery_id": delivery_id,
            "event_type": event_type_str,
            "tenant_id": event.tenant_id,
            "ticket_id": event.ticket_id,
            "timestamp": event.timestamp,
            "payload": event.payload,
        }

        payload_bytes = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        signature = cls.compute_signature(subscription.secret_token, payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Enterprise-Ticket-Triage-Webhook/1.0",
            "X-Triage-Signature": signature,
            "X-Triage-Delivery-Id": delivery_id,
            "X-Triage-Timestamp": timestamp_epoch,
            "X-Triage-Event": event_type_str,
        }

        req = urllib.request.Request(
            subscription.target_url,
            data=payload_bytes,
            headers=headers,
            method="POST",
        )

        start_time = time.time()
        status_code: Optional[int] = None
        success = False
        error_msg: Optional[str] = None

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.getcode()
                success = 200 <= status_code < 300
        except urllib.error.HTTPError as e:
            status_code = e.code
            error_msg = f"HTTP error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            error_msg = f"Connection error: {e.reason}"
        except Exception as e:
            error_msg = f"Dispatch exception: {str(e)}"

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return WebhookDeliveryRecord(
            delivery_id=delivery_id,
            subscription_id=subscription.subscription_id,
            event_type=event_type_str,
            target_url=subscription.target_url,
            status_code=status_code,
            success=success,
            latency_ms=latency_ms,
            error_message=error_msg,
        )

    @classmethod
    def test_ping(
        cls,
        subscription: WebhookSubscription,
        timeout: float = 5.0,
    ) -> Tuple[bool, int, float, Optional[str]]:
        """
        Sends a test ping event to verify connectivity and receiver signature parsing.
        Returns: (success, status_code, latency_ms, error_message)
        """
        ping_event = EnterpriseEvent(
            event_type="test.ping",  # type: ignore
            tenant_id=subscription.tenant_id,
            ticket_id="TEST-PING",
            payload={
                "message": "Outbound webhook test ping from Enterprise Triage System.",
                "subscription_id": subscription.subscription_id,
                "target_url": subscription.target_url,
            },
        )
        record = cls.dispatch(subscription, ping_event, timeout=timeout)
        return record.success, record.status_code or 0, record.latency_ms, record.error_message
