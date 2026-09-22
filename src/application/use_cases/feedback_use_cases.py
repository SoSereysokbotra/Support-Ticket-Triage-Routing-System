"""
Application Use Cases for Human-in-the-Loop (HITL) Feedback & Active Learning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.domain.entities.feedback import AgentFeedbackAnnotation
from src.domain.entities.tenant import (
    EnterpriseTicket,
    TenantContext,
    TicketPriority,
)
from src.domain.interfaces.event_bus_interface import IEventBus
from src.infrastructure.database.enterprise_repository import EnterpriseRepository


@dataclass
class SubmitAgentFeedbackInputDTO:
    ticket_id: str
    corrected_category: str
    corrected_priority: Optional[str] = None
    reclassification_reason: Optional[str] = None


@dataclass
class SubmitAgentFeedbackResultDTO:
    annotation: AgentFeedbackAnnotation
    updated_ticket: EnterpriseTicket
    retraining_threshold_reached: bool
    unprocessed_count: int


class SubmitAgentFeedbackUseCase:
    """
    Ingests human support agent corrections as ground-truth annotations.
    Updates the active ticket classification and checks active retraining trigger thresholds.
    """

    def __init__(
        self,
        repository: EnterpriseRepository,
        event_bus: Optional[IEventBus] = None,
    ) -> None:
        self.repository = repository
        self.event_bus = event_bus

    def execute(
        self,
        context: TenantContext,
        dto: SubmitAgentFeedbackInputDTO,
    ) -> SubmitAgentFeedbackResultDTO:
        # 1. Verify ticket exists within caller's tenant boundary
        ticket = self.repository.get_by_id_tenant(
            tenant_id=context.tenant_id, ticket_id=dto.ticket_id
        )
        if not ticket:
            raise ValueError(f"Ticket '{dto.ticket_id}' not found in current tenant.")

        original_cat = ticket.predicted_category
        original_prio = ticket.priority.value
        corrected_prio = dto.corrected_priority or original_prio

        # 2. Persist Immutable Feedback Annotation
        annotation = AgentFeedbackAnnotation(
            tenant_id=context.tenant_id,
            ticket_id=ticket.ticket_id,
            agent_id=context.user_id,
            original_category=original_cat,
            corrected_category=dto.corrected_category,
            original_priority=original_prio,
            corrected_priority=corrected_prio,
            model_version=ticket.model_version,
            original_confidence=ticket.confidence,
            reclassification_reason=dto.reclassification_reason,
        )
        saved_annotation = self.repository.save_feedback(annotation)

        # 3. Update Active Ticket with Ground Truth
        ticket.predicted_category = dto.corrected_category
        try:
            ticket.priority = TicketPriority(corrected_prio)
        except ValueError:
            pass

        updated_ticket = self.repository.save(ticket)

        # 4. Check Active Retraining Threshold
        stats = self.repository.get_feedback_stats(context.tenant_id)
        threshold_reached = bool(stats.get("retraining_threshold_reached", False))

        # 5. Emit Event
        if self.event_bus:
            event = EnterpriseEvent(
                event_type=EnterpriseEventType.FEEDBACK_SUBMITTED,
                tenant_id=context.tenant_id,
                ticket_id=ticket.ticket_id,
                payload={
                    "feedback_id": saved_annotation.feedback_id,
                    "original_category": original_cat,
                    "corrected_category": dto.corrected_category,
                    "is_high_confidence_error": saved_annotation.is_high_confidence_error,
                    "retraining_threshold_reached": threshold_reached,
                },
            )
            self.event_bus.publish(event)

        return SubmitAgentFeedbackResultDTO(
            annotation=saved_annotation,
            updated_ticket=updated_ticket,
            retraining_threshold_reached=threshold_reached,
            unprocessed_count=stats.get("unprocessed_annotations", 0),
        )


class GetFeedbackStatsUseCase:
    """Retrieves annotation and retraining metrics for a tenant."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, context: TenantContext) -> Dict[str, Any]:
        return self.repository.get_feedback_stats(context.tenant_id)
