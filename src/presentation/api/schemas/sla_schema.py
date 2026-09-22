"""
Pydantic Schemas for SLA Watchdog, At-Risk Queries, and Escalations.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SLAScanReportResponse(BaseModel):
    scanned_count: int
    warnings_emitted: int
    breached_and_escalated: int
    evaluation_timestamp: str


class EscalateTicketRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=512, json_schema_extra={"example": "Customer executive escalation requested on critical outage."})
    new_team: Optional[str] = Field("Tier-3 Senior Escalations", json_schema_extra={"example": "Tier-3 Senior Escalations"})
