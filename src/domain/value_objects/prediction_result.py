from dataclasses import dataclass, field
from typing import Dict

from src.domain.entities.category import TicketCategory


@dataclass(frozen=True)
class PredictionResult:
    """
    Immutable Value Object representing the output of a model inference.
    """
    predicted_category: TicketCategory
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    model_version: str = "baseline"
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.latency_ms < 0.0:
            raise ValueError("Latency cannot be negative.")
