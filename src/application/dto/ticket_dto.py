from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TicketInputDTO:
    text: str
    ticket_id: Optional[str] = None
    title: Optional[str] = None
    customer_id: Optional[str] = None
    urgency_hint: Optional[str] = None


@dataclass
class TriageResponseDTO:
    ticket_id: str
    predicted_category: str
    confidence: float
    probabilities: Dict[str, float]
    assigned_team: str
    priority_level: str
    target_sla_hours: int
    auto_routed: bool
    routing_reason: str
    model_version: str
    latency_ms: float
    customer_features: Optional[Dict[str, Any]] = None
