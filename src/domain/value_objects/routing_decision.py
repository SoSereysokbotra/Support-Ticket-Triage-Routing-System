from dataclasses import dataclass

from src.domain.entities.category import TicketCategory, TicketUrgency


@dataclass(frozen=True)
class RoutingDecision:
    """
    Immutable Value Object representing business routing decision.
    """
    ticket_id: str
    assigned_team: str
    priority_level: TicketUrgency
    target_sla_hours: int
    category: TicketCategory
    confidence: float
    auto_routed: bool
    routing_reason: str
    fallback_applied: bool = False
