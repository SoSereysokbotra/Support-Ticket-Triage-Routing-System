"""
Urgency Prediction Result Value Object
"""

from dataclasses import dataclass
from typing import Dict

from src.domain.entities.category import TicketUrgency


@dataclass(frozen=True)
class UrgencyPredictionResult:
    predicted_urgency: TicketUrgency
    confidence: float
    probabilities: Dict[str, float]
    model_version: str
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence score must be in range [0.0, 1.0], got {self.confidence}")
        if self.latency_ms < 0:
            raise ValueError("Latency cannot be negative")
