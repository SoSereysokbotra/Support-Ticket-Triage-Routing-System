"""
Application Use Cases for SLA Evaluation, At-Risk Queries, and Manual/Automated Escalation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.domain.entities.tenant import EnterpriseTicket, TenantContext
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.workers.sla_watchdog_worker import SLAScanReport, SLAWatchdogWorker


@dataclass
class EscalateTicketInputDTO:
    ticket_id: str
    reason: str
    new_team: str = "Tier-3 Senior Escalations"


class EvaluateSLAUseCase:
    """Runs an immediate SLA evaluation cycle across all active tickets."""

    def __init__(self, watchdog_worker: SLAWatchdogWorker) -> None:
        self.watchdog_worker = watchdog_worker

    def execute(self, now: Optional[datetime] = None) -> SLAScanReport:
        return self.watchdog_worker.evaluate_open_tickets(now=now)


class EscalateTicketUseCase:
    """Escalates a specific ticket within the caller's tenant boundary."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(
        self,
        context: TenantContext,
        dto: EscalateTicketInputDTO,
    ) -> EnterpriseTicket:
        ticket = self.repository.get_ticket_by_id(
            tenant_id=context.tenant_id,
            ticket_id=dto.ticket_id,
        )
        if not ticket:
            raise ValueError(f"Ticket '{dto.ticket_id}' not found in current tenant.")

        ticket.escalate(reason=dto.reason, new_team=dto.new_team)
        return self.repository.update_ticket_sla(ticket)


class ListAtRiskTicketsUseCase:
    """Lists tickets at or past the 75% SLA warning threshold or breached."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, context: TenantContext) -> List[EnterpriseTicket]:
        return self.repository.list_at_risk_tickets(tenant_id=context.tenant_id)
