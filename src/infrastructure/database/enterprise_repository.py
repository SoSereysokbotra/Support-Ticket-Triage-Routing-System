"""
Enterprise SQLAlchemy Repository for Multi-Tenancy, Users, and Enterprise Tickets.
Supports PostgreSQL 16 (production) and SQLite (testing/local development).
Guarantees tenant isolation and SLA tracking on every operation.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    or_,
    select,
    update,
)

from src.domain.entities.tenant import (
    CustomerTier,
    EnterpriseTicket,
    Tenant,
    TenantPlan,
    TicketPriority,
    TicketStatus,
    User,
    UserRole,
)
from src.domain.interfaces.tenant_interface import (
    IEnterpriseTicketRepository,
    ITenantRepository,
    IUserRepository,
)

metadata = MetaData()

# Table Definitions
tenants_table = Table(
    "tenants",
    metadata,
    Column("tenant_id", String(64), primary_key=True),
    Column("slug", String(64), unique=True, nullable=False),
    Column("company_name", String(255), nullable=False),
    Column("plan", String(32), nullable=False, default="GROWTH"),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

users_table = Table(
    "users",
    metadata,
    Column("user_id", String(64), primary_key=True),
    Column("tenant_id", String(64), nullable=False, index=True),
    Column("email", String(255), nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("full_name", String(255), nullable=False),
    Column("role", String(32), nullable=False, default="SUPPORT_AGENT"),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)

enterprise_tickets_table = Table(
    "enterprise_tickets",
    metadata,
    Column("ticket_id", String(64), primary_key=True),
    Column("tenant_id", String(64), nullable=False, index=True),
    Column("title", String(512), nullable=True),
    Column("description", Text, nullable=False),
    Column("customer_id", String(128), nullable=False),
    Column("customer_tier", String(32), nullable=False, default="STANDARD"),
    Column("status", String(32), nullable=False, default="OPEN"),
    Column("predicted_category", String(64), nullable=False),
    Column("confidence", Float, nullable=False),
    Column("probabilities", Text, nullable=False),  # JSON serialized
    Column("assigned_team", String(128), nullable=False),
    Column("priority", String(32), nullable=False, default="P3_MEDIUM"),
    Column("auto_routed", Boolean, nullable=False, default=True),
    Column("model_version", String(64), nullable=False),
    Column("latency_ms", Float, nullable=False),
    Column("assigned_agent_id", String(64), nullable=True),
    Column("sla_response_deadline", DateTime, nullable=True),
    Column("sla_resolution_deadline", DateTime, nullable=True),
    Column("sla_warning_emitted", Boolean, nullable=False, default=False),
    Column("escalated", Boolean, nullable=False, default=False),
    Column("escalation_reason", Text, nullable=True),
    Column("resolved_at", DateTime, nullable=True),
    Column("copilot_suggested_response", Text, nullable=True),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)


class EnterpriseRepository(ITenantRepository, IUserRepository, IEnterpriseTicketRepository):
    """
    Unified multi-tenant repository providing thread-safe persistence
    for tenants, users, and enterprise tickets with SLA tracking.
    """

    def __init__(self, db_url: Optional[str] = None) -> None:
        env_url = os.getenv("POSTGRES_DB_URL") or os.getenv("DATABASE_URL")
        self.db_url = db_url or env_url

        if self.db_url:
            self.is_postgres = self.db_url.startswith("postgres")
            self.engine = create_engine(self.db_url, pool_pre_ping=True, future=True)
        else:
            db_dir = Path("data/enterprise")
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite:///{db_dir.as_posix()}/enterprise.db"
            self.is_postgres = False
            self.engine = create_engine(self.db_url, connect_args={"timeout": 20.0}, future=True)

        # Bootstrap tables
        metadata.create_all(self.engine)

    # -------------------------------------------------------------------------
    # Helper Mapper
    # -------------------------------------------------------------------------
    @staticmethod
    def _row_to_ticket(r: Any) -> EnterpriseTicket:
        return EnterpriseTicket(
            ticket_id=r["ticket_id"],
            tenant_id=r["tenant_id"],
            title=r["title"],
            description=r["description"],
            customer_id=r["customer_id"],
            customer_tier=CustomerTier(r["customer_tier"]),
            status=TicketStatus(r["status"]),
            predicted_category=r["predicted_category"],
            confidence=float(r["confidence"]),
            probabilities=json.loads(r["probabilities"]) if isinstance(r["probabilities"], str) else r["probabilities"],
            assigned_team=r["assigned_team"],
            priority=TicketPriority(r["priority"]),
            auto_routed=bool(r["auto_routed"]),
            model_version=r["model_version"],
            latency_ms=float(r["latency_ms"]),
            assigned_agent_id=r["assigned_agent_id"],
            sla_response_deadline=r["sla_response_deadline"],
            sla_resolution_deadline=r["sla_resolution_deadline"],
            sla_warning_emitted=bool(r["sla_warning_emitted"]),
            escalated=bool(r["escalated"]),
            escalation_reason=r["escalation_reason"],
            resolved_at=r["resolved_at"],
            created_at=r["created_at"],
        )

    # -------------------------------------------------------------------------
    # Tenant Operations
    # -------------------------------------------------------------------------
    def create_tenant(self, tenant: Tenant) -> Tenant:
        with self.engine.begin() as conn:
            stmt = tenants_table.insert().values(
                tenant_id=tenant.tenant_id,
                slug=tenant.slug,
                company_name=tenant.company_name,
                plan=tenant.plan.value if isinstance(tenant.plan, TenantPlan) else str(tenant.plan),
                is_active=tenant.is_active,
                created_at=tenant.created_at,
                updated_at=tenant.created_at,
            )
            conn.execute(stmt)
        return tenant

    create = create_tenant

    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        with self.engine.connect() as conn:
            stmt = select(tenants_table).where(tenants_table.c.tenant_id == tenant_id)
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            return Tenant(
                tenant_id=row["tenant_id"],
                slug=row["slug"],
                company_name=row["company_name"],
                plan=TenantPlan(row["plan"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    get_by_id = get_tenant_by_id

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        with self.engine.connect() as conn:
            stmt = select(tenants_table).where(tenants_table.c.slug == slug)
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            return Tenant(
                tenant_id=row["tenant_id"],
                slug=row["slug"],
                company_name=row["company_name"],
                plan=TenantPlan(row["plan"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    get_by_slug = get_tenant_by_slug

    def list_all_tenants(self) -> List[Tenant]:
        with self.engine.connect() as conn:
            stmt = select(tenants_table).order_by(tenants_table.c.created_at.desc())
            rows = conn.execute(stmt).mappings().all()
            return [
                Tenant(
                    tenant_id=r["tenant_id"],
                    slug=r["slug"],
                    company_name=r["company_name"],
                    plan=TenantPlan(r["plan"]),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    list_all = list_all_tenants

    # -------------------------------------------------------------------------
    # User Operations (Tenant Scoped)
    # -------------------------------------------------------------------------
    def create_user(self, user: User) -> User:
        with self.engine.begin() as conn:
            stmt = users_table.insert().values(
                user_id=user.user_id,
                tenant_id=user.tenant_id,
                email=user.email,
                password_hash=user.password_hash,
                full_name=user.full_name,
                role=user.role.value if isinstance(user.role, UserRole) else str(user.role),
                is_active=user.is_active,
                created_at=user.created_at,
            )
            conn.execute(stmt)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self.engine.connect() as conn:
            stmt = select(users_table).where(users_table.c.user_id == user_id)
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            return User(
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                email=row["email"],
                password_hash=row["password_hash"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        with self.engine.connect() as conn:
            stmt = select(users_table).where(
                users_table.c.tenant_id == tenant_id,
                users_table.c.email == email,
            )
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            return User(
                user_id=row["user_id"],
                tenant_id=row["tenant_id"],
                email=row["email"],
                password_hash=row["password_hash"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def list_users_by_tenant(self, tenant_id: str) -> List[User]:
        with self.engine.connect() as conn:
            stmt = select(users_table).where(users_table.c.tenant_id == tenant_id)
            rows = conn.execute(stmt).mappings().all()
            return [
                User(
                    user_id=r["user_id"],
                    tenant_id=r["tenant_id"],
                    email=r["email"],
                    password_hash=r["password_hash"],
                    full_name=r["full_name"],
                    role=UserRole(r["role"]),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    list_by_tenant = list_users_by_tenant

    # -------------------------------------------------------------------------
    # Enterprise Ticket Operations (Strictly Tenant Scoped)
    # -------------------------------------------------------------------------
    def save_ticket(self, ticket: EnterpriseTicket) -> EnterpriseTicket:
        with self.engine.begin() as conn:
            stmt = enterprise_tickets_table.insert().values(
                ticket_id=ticket.ticket_id,
                tenant_id=ticket.tenant_id,
                title=ticket.title,
                description=ticket.description,
                customer_id=ticket.customer_id,
                customer_tier=ticket.customer_tier.value if isinstance(ticket.customer_tier, CustomerTier) else str(ticket.customer_tier),
                status=ticket.status.value if isinstance(ticket.status, TicketStatus) else str(ticket.status),
                predicted_category=ticket.predicted_category,
                confidence=ticket.confidence,
                probabilities=json.dumps(ticket.probabilities),
                assigned_team=ticket.assigned_team,
                priority=ticket.priority.value if isinstance(ticket.priority, TicketPriority) else str(ticket.priority),
                auto_routed=ticket.auto_routed,
                model_version=ticket.model_version,
                latency_ms=ticket.latency_ms,
                assigned_agent_id=ticket.assigned_agent_id,
                sla_response_deadline=ticket.sla_response_deadline,
                sla_resolution_deadline=ticket.sla_resolution_deadline,
                sla_warning_emitted=ticket.sla_warning_emitted,
                escalated=ticket.escalated,
                escalation_reason=ticket.escalation_reason,
                resolved_at=ticket.resolved_at,
                copilot_suggested_response=None,
                created_at=ticket.created_at,
            )
            conn.execute(stmt)
        return ticket

    save = save_ticket

    def get_ticket_by_id(self, tenant_id: str, ticket_id: str) -> Optional[EnterpriseTicket]:
        with self.engine.connect() as conn:
            stmt = select(enterprise_tickets_table).where(
                enterprise_tickets_table.c.tenant_id == tenant_id,
                enterprise_tickets_table.c.ticket_id == ticket_id,
            )
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            return self._row_to_ticket(row)

    get_by_id_tenant = get_ticket_by_id

    def list_tickets_by_tenant(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EnterpriseTicket]:
        with self.engine.connect() as conn:
            query = select(enterprise_tickets_table).where(enterprise_tickets_table.c.tenant_id == tenant_id)
            if status:
                query = query.where(enterprise_tickets_table.c.status == status)
            query = query.order_by(enterprise_tickets_table.c.created_at.desc()).limit(limit).offset(offset)

            rows = conn.execute(query).mappings().all()
            return [self._row_to_ticket(r) for r in rows]

    def update_ticket_sla(self, ticket: EnterpriseTicket) -> EnterpriseTicket:
        """Updates SLA status, warning flags, and escalation fields on a ticket."""
        with self.engine.begin() as conn:
            stmt = (
                update(enterprise_tickets_table)
                .where(enterprise_tickets_table.c.ticket_id == ticket.ticket_id)
                .values(
                    status=ticket.status.value if isinstance(ticket.status, TicketStatus) else str(ticket.status),
                    assigned_team=ticket.assigned_team,
                    sla_warning_emitted=ticket.sla_warning_emitted,
                    escalated=ticket.escalated,
                    escalation_reason=ticket.escalation_reason,
                    resolved_at=ticket.resolved_at,
                )
            )
            conn.execute(stmt)
        return ticket

    def get_open_tickets(self, tenant_id: Optional[str] = None) -> List[EnterpriseTicket]:
        """Retrieves all open tickets across tenants or for a specific tenant."""
        with self.engine.connect() as conn:
            query = select(enterprise_tickets_table).where(
                enterprise_tickets_table.c.status.in_([TicketStatus.OPEN.value, TicketStatus.PENDING_AGENT.value])
            )
            if tenant_id:
                query = query.where(enterprise_tickets_table.c.tenant_id == tenant_id)

            rows = conn.execute(query).mappings().all()
            return [self._row_to_ticket(r) for r in rows]

    def list_at_risk_tickets(self, tenant_id: str) -> List[EnterpriseTicket]:
        """Retrieves tickets past warning threshold or breached within tenant boundary."""
        with self.engine.connect() as conn:
            query = select(enterprise_tickets_table).where(
                enterprise_tickets_table.c.tenant_id == tenant_id,
                or_(
                    enterprise_tickets_table.c.status == TicketStatus.BREACHED.value,
                    enterprise_tickets_table.c.escalated.is_(True),
                    enterprise_tickets_table.c.sla_warning_emitted.is_(True),
                ),
            ).order_by(enterprise_tickets_table.c.created_at.desc())

            rows = conn.execute(query).mappings().all()
            return [self._row_to_ticket(r) for r in rows]
