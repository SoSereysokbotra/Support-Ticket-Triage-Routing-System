"""
Domain Entities and Value Objects for Outbound Webhook Subscriptions and Delivery Telemetry.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class WebhookSubscription:
    """
    Represents an external system's registration to receive real-time ticket lifecycle events.
    Cryptographically tied to a tenant with HMAC-SHA256 signature verification.
    """
    tenant_id: str
    target_url: str
    secret_token: str
    events_subscribed: List[str]
    description: Optional[str] = None
    is_active: bool = True
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_subscribed_to(self, event_type: str) -> bool:
        """Determines if the subscription is active and listens for the given event type."""
        if not self.is_active:
            return False
        if "*" in self.events_subscribed:
            return True
        return event_type in self.events_subscribed

    def to_dict(self) -> Dict[str, Any]:
        """Serializes subscription to JSON-compatible dictionary."""
        return {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "target_url": self.target_url,
            "events_subscribed": self.events_subscribed,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class WebhookDeliveryRecord:
    """
    Immutable audit record representing an outbound webhook HTTP dispatch attempt.
    """
    subscription_id: str
    event_type: str
    target_url: str
    status_code: Optional[int]
    success: bool
    latency_ms: float
    delivery_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_message: Optional[str] = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "target_url": self.target_url,
            "status_code": self.status_code,
            "success": self.success,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }
