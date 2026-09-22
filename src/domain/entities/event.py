"""
Domain Entities and Value Objects for Enterprise Event-Driven Architecture.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


class EnterpriseEventType(str, Enum):
    """Types of real-time events emitted within the multi-tenant ITSM platform."""
    TICKET_INGESTED = "ticket.ingested"
    SLA_WARNING = "ticket.sla_warning"
    TICKET_ESCALATED = "ticket.escalated"
    TICKET_RESOLVED = "ticket.resolved"


@dataclass(frozen=True)
class EnterpriseEvent:
    """
    Immutable domain event representing a significant state change in the ticket lifecycle.
    Cryptographically and logically scoped to a specific tenant.
    """
    event_type: EnterpriseEventType
    tenant_id: str
    ticket_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes domain event to JSON-compatible dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tenant_id": self.tenant_id,
            "ticket_id": self.ticket_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EnterpriseEvent:
        """Hydrates domain event from JSON-compatible dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EnterpriseEventType(data["event_type"]),
            tenant_id=data["tenant_id"],
            ticket_id=data["ticket_id"],
            timestamp=data["timestamp"],
            payload=data.get("payload", {}),
        )
