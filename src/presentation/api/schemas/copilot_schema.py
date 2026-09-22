"""
Pydantic Schemas for Agent Copilot and Human-in-the-Loop Feedback (API v2).
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class AgentFeedbackRequest(BaseModel):
    corrected_category: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Human verified ground-truth category",
        json_schema_extra={"example": "Network"},
    )
    corrected_priority: Optional[str] = Field(
        None,
        description="Optional human corrected priority level (P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW)",
        json_schema_extra={"example": "P1_CRITICAL"},
    )
    reclassification_reason: Optional[str] = Field(
        None,
        max_length=512,
        description="Agent audit rationale for reclassifying the ticket",
        json_schema_extra={"example": "Customer reported VPN gateway drop, misclassified as Software."},
    )


class AgentFeedbackResponse(BaseModel):
    feedback_id: str
    tenant_id: str
    ticket_id: str
    agent_id: str
    original_category: str
    corrected_category: str
    original_priority: str
    corrected_priority: str
    model_version: str
    original_confidence: float
    reclassification_reason: Optional[str]
    is_high_confidence_error: bool
    sample_weight: float
    retraining_threshold_reached: bool
    created_at: str


class FeedbackStatsResponse(BaseModel):
    tenant_id: str
    total_annotations: int
    unprocessed_annotations: int
    high_confidence_false_positives: int
    retraining_threshold_reached: bool


class CopilotDraftResponse(BaseModel):
    ticket_id: str
    suggested_response: Optional[str]
    copilot_confidence: float
    sources: List[str]
    is_skipped: bool
    skip_reason: Optional[str] = None
