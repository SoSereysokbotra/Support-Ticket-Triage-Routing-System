"""
Enterprise Ticket Management Use Cases.
Integrates TenantContext, ONNX Model Triage, and Enterprise Persistence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.application.dto.ticket_dto import TicketInputDTO
from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.domain.entities.tenant import (
    CustomerTier,
    EnterpriseTicket,
    TenantContext,
    TicketPriority,
    TicketStatus,
)
from src.domain.interfaces.event_bus_interface import IEventBus
from src.domain.services.sla_policy_engine import SLAPolicyEngine
from src.infrastructure.database.enterprise_repository import EnterpriseRepository


@dataclass
class CreateEnterpriseTicketInputDTO:
    description: str
    customer_id: str
    title: Optional[str] = None
    customer_tier: CustomerTier = CustomerTier.STANDARD
    priority_hint: Optional[str] = None


class CreateEnterpriseTicketUseCase:
    """Ingests, triages via ONNX, and persists an enterprise ticket within tenant boundary."""

    def __init__(
        self,
        repository: EnterpriseRepository,
        predict_use_case: PredictTicketUseCase,
        event_bus: Optional[IEventBus] = None,
    ) -> None:
        self.repository = repository
        self.predict_use_case = predict_use_case
        self.event_bus = event_bus

    def execute(
        self,
        context: TenantContext,
        dto: CreateEnterpriseTicketInputDTO,
    ) -> EnterpriseTicket:
        start_time = time.perf_counter()

        # 1. Run ONNX-Accelerated Model Inference & SLA Routing
        predict_dto = TicketInputDTO(
            text=dto.description,
            title=dto.title,
            customer_id=dto.customer_id,
            urgency_hint=dto.priority_hint,
        )
        prediction_result = self.predict_use_case.execute(predict_dto)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 2. Map priority string to TicketPriority enum
        priority_map = {
            "Critical": TicketPriority.P1_CRITICAL,
            "High": TicketPriority.P2_HIGH,
            "Medium": TicketPriority.P3_MEDIUM,
            "Low": TicketPriority.P4_LOW,
        }
        ticket_priority = priority_map.get(prediction_result.priority_level, TicketPriority.P3_MEDIUM)

        # 3. Compute Dynamic Contractual SLA Deadlines
        now = datetime.now(timezone.utc)
        resp_deadline, resol_deadline = SLAPolicyEngine.compute_deadlines(
            created_at=now,
            customer_tier=dto.customer_tier,
            priority=ticket_priority,
        )

        # 4. Create & Persist Enterprise Ticket Entity
        enterprise_ticket = EnterpriseTicket(
            tenant_id=context.tenant_id,
            title=dto.title,
            description=dto.description,
            customer_id=dto.customer_id,
            customer_tier=dto.customer_tier,
            status=TicketStatus.OPEN,
            predicted_category=prediction_result.predicted_category,
            confidence=prediction_result.confidence,
            probabilities=prediction_result.probabilities,
            assigned_team=prediction_result.assigned_team,
            priority=ticket_priority,
            auto_routed=prediction_result.auto_routed,
            model_version=prediction_result.model_version,
            latency_ms=round(latency_ms, 2),
            sla_response_deadline=resp_deadline,
            sla_resolution_deadline=resol_deadline,
            created_at=now,
        )

        saved_ticket = self.repository.save(enterprise_ticket)
        if self.event_bus:
            event = EnterpriseEvent(
                event_type=EnterpriseEventType.TICKET_INGESTED,
                tenant_id=saved_ticket.tenant_id,
                ticket_id=saved_ticket.ticket_id,
                payload={
                    "title": saved_ticket.title,
                    "description": saved_ticket.description,
                    "predicted_category": saved_ticket.predicted_category,
                    "confidence": saved_ticket.confidence,
                    "assigned_team": saved_ticket.assigned_team,
                    "priority": saved_ticket.priority.value,
                    "customer_tier": saved_ticket.customer_tier.value,
                    "sla_response_deadline": (
                        saved_ticket.sla_response_deadline.isoformat()
                        if saved_ticket.sla_response_deadline
                        else None
                    ),
                    "sla_resolution_deadline": (
                        saved_ticket.sla_resolution_deadline.isoformat()
                        if saved_ticket.sla_resolution_deadline
                        else None
                    ),
                    "created_at": saved_ticket.created_at.isoformat(),
                },
            )
            self.event_bus.publish(event)

        return saved_ticket


class ListEnterpriseTicketsUseCase:
    """Lists tickets strictly scoped to the authenticated tenant."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(
        self,
        context: TenantContext,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EnterpriseTicket]:
        return self.repository.list_tickets_by_tenant(
            tenant_id=context.tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )
