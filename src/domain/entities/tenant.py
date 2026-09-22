"""
Pure Domain Entities and Value Objects for Multi-Tenancy & Enterprise RBAC.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TRIAGE_LEAD = "TRIAGE_LEAD"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    AUDITOR = "AUDITOR"
    BOT = "BOT"


class TenantPlan(str, Enum):
    STARTER = "STARTER"
    GROWTH = "GROWTH"
    ENTERPRISE = "ENTERPRISE"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    PENDING_AGENT = "PENDING_AGENT"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    BREACHED = "BREACHED"


class TicketPriority(str, Enum):
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"


class CustomerTier(str, Enum):
    FREE = "FREE"
    STANDARD = "STANDARD"
    BUSINESS = "BUSINESS"
    VIP_ENTERPRISE = "VIP_ENTERPRISE"


@dataclass
class Tenant:
    """Represents an isolated organization / company tenant in the platform."""
    company_name: str
    slug: str
    tenant_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan: TenantPlan = TenantPlan.GROWTH
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.company_name or not self.company_name.strip():
            raise ValueError("Company name cannot be empty.")
        if not self.slug or not re.match(r"^[a-z0-9-]+$", self.slug):
            raise ValueError("Tenant slug must contain only lowercase alphanumeric characters and hyphens.")


@dataclass
class User:
    """Represents a member with authenticated credentials and RBAC roles."""
    tenant_id: str
    email: str
    password_hash: str
    full_name: str
    role: UserRole = UserRole.SUPPORT_AGENT
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address.")
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Full name cannot be empty.")


@dataclass(frozen=True)
class TenantContext:
    """
    Immutable security context representing the authenticated actor and tenant.
    Injected into use cases and repositories to guarantee tenant boundaries.
    """
    tenant_id: str
    user_id: str
    role: UserRole
    email: str

    def has_role(self, *allowed_roles: UserRole) -> bool:
        """Returns True if the context user holds any of the specified roles."""
        if self.role == UserRole.SUPERADMIN:
            return True
        return self.role in allowed_roles


@dataclass
class EnterpriseTicket:
    """Represents a tenant-isolated support ticket with MLOps and SLA metadata."""
    tenant_id: str
    description: str
    customer_id: str
    predicted_category: str
    confidence: float
    probabilities: Dict[str, float]
    assigned_team: str
    priority: TicketPriority
    model_version: str
    latency_ms: float
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    customer_tier: CustomerTier = CustomerTier.STANDARD
    status: TicketStatus = TicketStatus.OPEN
    auto_routed: bool = True
    assigned_agent_id: Optional[str] = None
    sla_response_deadline: Optional[datetime] = None
    sla_resolution_deadline: Optional[datetime] = None
    sla_warning_emitted: bool = False
    escalated: bool = False
    escalation_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    copilot_suggested_response: Optional[str] = None
    copilot_confidence: Optional[float] = None
    copilot_sources: Optional[List[str]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def resolve(self, now: Optional[datetime] = None) -> None:
        """Transitions ticket to RESOLVED state."""
        self.status = TicketStatus.RESOLVED
        self.resolved_at = now or datetime.now(timezone.utc)

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValueError("Ticket description cannot be empty.")
        if not self.tenant_id:
            raise ValueError("Enterprise tickets must belong to a tenant_id.")

    def is_past_resolution_deadline(self, now: Optional[datetime] = None) -> bool:
        """Returns True if the ticket has passed its SLA resolution deadline."""
        if not self.sla_resolution_deadline:
            return False
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        deadline = self.sla_resolution_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        return current_time >= deadline

    def is_past_warning_threshold(self, now: Optional[datetime] = None, threshold_pct: float = 0.75) -> bool:
        """Returns True if the ticket has exceeded the specified SLA percentage window."""
        if not self.sla_resolution_deadline or not self.created_at:
            return False
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        deadline = self.sla_resolution_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        total_duration = (deadline - created).total_seconds()
        if total_duration <= 0:
            return True
        elapsed = (current_time - created).total_seconds()
        return (elapsed / total_duration) >= threshold_pct

    def escalate(self, reason: str, new_team: str = "Tier-3 Senior Escalations") -> None:
        """Escalates ticket to Tier 3 and logs reason."""
        self.escalated = True
        self.escalation_reason = reason
        self.assigned_team = new_team
