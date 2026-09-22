"""
Pydantic Schemas for Multi-Tenant Auth, User Management, and Enterprise Tickets.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class RegisterTenantRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Acme Corporation"})
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$", json_schema_extra={"example": "acme-corp"})
    admin_email: str = Field(..., min_length=5, max_length=255, json_schema_extra={"example": "admin@acme.com"})
    admin_password: str = Field(..., min_length=8, max_length=128, json_schema_extra={"example": "SuperSecret123!"})
    admin_full_name: str = Field(..., min_length=2, max_length=255, json_schema_extra={"example": "Alice Smith"})
    plan: Optional[str] = Field("GROWTH", json_schema_extra={"example": "GROWTH"})


class LoginRequest(BaseModel):
    tenant_slug: str = Field(..., json_schema_extra={"example": "acme-corp"})
    email: str = Field(..., json_schema_extra={"example": "admin@acme.com"})
    password: str = Field(..., json_schema_extra={"example": "SuperSecret123!"})


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    role: str
    email: str
    full_name: str
    company_name: str


class UserProfileResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    role: str


class CreateEnterpriseTicketRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=10000, json_schema_extra={"example": "VPN client refuses connection from remote office."})
    customer_id: str = Field(..., json_schema_extra={"example": "CUST-1049"})
    title: Optional[str] = Field(None, json_schema_extra={"example": "VPN Connection Failure"})
    customer_tier: Optional[str] = Field("STANDARD", json_schema_extra={"example": "VIP_ENTERPRISE"})
    priority_hint: Optional[str] = Field(None, json_schema_extra={"example": "High"})


class EnterpriseTicketResponse(BaseModel):
    ticket_id: str
    tenant_id: str
    title: Optional[str] = None
    description: str
    customer_id: str
    customer_tier: str
    status: str
    predicted_category: str
    confidence: float
    probabilities: Dict[str, float]
    assigned_team: str
    priority: str
    auto_routed: bool
    model_version: str
    latency_ms: float
    created_at: str
