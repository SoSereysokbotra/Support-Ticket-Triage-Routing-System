"""
Domain Entities for Human-in-the-Loop (HITL) Feedback and Ground-Truth Annotations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class AgentFeedbackAnnotation:
    """
    Immutable ground-truth annotation provided by a human support agent.
    Used for active learning, error analysis, and automated retraining triggers.
    """
    tenant_id: str
    ticket_id: str
    agent_id: str
    original_category: str
    corrected_category: str
    original_priority: str
    corrected_priority: str
    model_version: str
    original_confidence: float
    reclassification_reason: Optional[str] = None
    is_used_in_retraining: bool = False
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def is_high_confidence_error(self) -> bool:
        """
        Flags whether the model was confidently wrong (>= 0.85 confidence),
        indicating severe concept drift or false positive bias.
        High-confidence errors receive 3x sample weight during active retraining.
        """
        is_category_corrected = self.original_category != self.corrected_category
        return self.original_confidence >= 0.85 and is_category_corrected

    @property
    def sample_weight(self) -> float:
        """Sample weight multiplier for active learning retraining loops."""
        return 3.0 if self.is_high_confidence_error else 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes annotation to JSON-compatible dictionary."""
        return {
            "feedback_id": self.feedback_id,
            "tenant_id": self.tenant_id,
            "ticket_id": self.ticket_id,
            "agent_id": self.agent_id,
            "original_category": self.original_category,
            "corrected_category": self.corrected_category,
            "original_priority": self.original_priority,
            "corrected_priority": self.corrected_priority,
            "model_version": self.model_version,
            "original_confidence": self.original_confidence,
            "reclassification_reason": self.reclassification_reason,
            "is_high_confidence_error": self.is_high_confidence_error,
            "sample_weight": self.sample_weight,
            "is_used_in_retraining": self.is_used_in_retraining,
            "created_at": self.created_at.isoformat(),
        }
