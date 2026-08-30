from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TicketPredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=5,
        max_length=10000,
        description="The content of the support ticket",
        json_schema_extra={"example": "My monitor is flickering constantly and going black when I move the hinge."},
    )
    title: Optional[str] = Field(
        None,
        description="Optional subject line or summary",
        json_schema_extra={"example": "Flickering external monitor"},
    )
    customer_id: Optional[str] = Field(
        None,
        description="Optional identifier of the customer or employee submitting ticket",
        json_schema_extra={"example": "CUST-4912"},
    )
    urgency_hint: Optional[str] = Field(
        None,
        description="Optional customer-provided urgency hint (Low, Medium, High, Critical)",
        json_schema_extra={"example": "High"},
    )


class TicketPredictBatchRequest(BaseModel):
    tickets: List[TicketPredictRequest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of tickets to triage in batch",
    )


class TicketPredictResponse(BaseModel):
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


class TicketPredictBatchResponse(BaseModel):
    results: List[TicketPredictResponse]
    total_latency_ms: float
    batch_size: int


class HealthResponse(BaseModel):
    status: str
    model_version: str
    device: str
    uptime_seconds: float
