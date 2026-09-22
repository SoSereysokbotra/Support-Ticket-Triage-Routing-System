"""
Pydantic Schemas for Outbound Webhook Subscriptions and Delivery Testing.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CreateWebhookSubscriptionRequest(BaseModel):
    target_url: str = Field(
        ...,
        min_length=8,
        max_length=1024,
        json_schema_extra={"example": "https://api.corporate-gateway.io/webhooks/triage"},
    )
    events_subscribed: List[str] = Field(
        default=["*"],
        json_schema_extra={"example": ["ticket.ingested", "ticket.sla_warning", "ticket.escalated", "ticket.resolved"]},
    )
    secret_token: Optional[str] = Field(
        None,
        min_length=16,
        max_length=255,
        json_schema_extra={"example": "whsec_custom_secret_key_12345"},
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        json_schema_extra={"example": "Corporate SIEM & Incident Response ingestion hook"},
    )


class WebhookSubscriptionResponse(BaseModel):
    subscription_id: str
    tenant_id: str
    target_url: str
    secret_token: str
    events_subscribed: List[str]
    description: Optional[str] = None
    is_active: bool
    created_at: str


class TestWebhookDeliveryResponse(BaseModel):
    subscription_id: str
    success: bool
    status_code: int
    latency_ms: float
    error_message: Optional[str] = None
