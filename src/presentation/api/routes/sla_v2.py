"""
Enterprise SLA Watchdog & Escalation Routes (API v2).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.use_cases.sla_use_cases import (
    EscalateTicketInputDTO,
    EscalateTicketUseCase,
    EvaluateSLAUseCase,
    ListAtRiskTicketsUseCase,
)
from src.domain.entities.tenant import TenantContext, UserRole
from src.infrastructure.workers.sla_watchdog_worker import SLAWatchdogWorker
from src.presentation.api.dependencies.auth import (
    get_current_tenant_context,
    require_roles,
)
from src.presentation.api.routes.tickets_v2 import map_ticket_to_response
from src.presentation.api.schemas.auth_schema import EnterpriseTicketResponse
from src.presentation.api.schemas.sla_schema import (
    EscalateTicketRequest,
    SLAScanReportResponse,
)

router = APIRouter(prefix="/api/v2", tags=["SLA Watchdog & Escalations"])


@router.get(
    "/sla/at-risk",
    response_model=List[EnterpriseTicketResponse],
    summary="List Tickets Past 75% SLA Warning or Breached",
)
def list_at_risk_tickets(
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> List[EnterpriseTicketResponse]:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    use_case = ListAtRiskTicketsUseCase(repo)
    tickets = use_case.execute(context)

    return [map_ticket_to_response(t) for t in tickets]


@router.post(
    "/sla/evaluate",
    response_model=SLAScanReportResponse,
    summary="Trigger Immediate SLA Watchdog Evaluation Cycle",
)
def evaluate_sla(
    request: Request,
    context: TenantContext = Depends(
        require_roles(UserRole.TENANT_ADMIN, UserRole.TRIAGE_LEAD, UserRole.SUPERADMIN)
    ),
) -> SLAScanReportResponse:
    watchdog: SLAWatchdogWorker = getattr(request.app.state, "sla_watchdog", None)
    if not watchdog:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SLA Watchdog worker is not initialized.",
        )

    use_case = EvaluateSLAUseCase(watchdog)
    report = use_case.execute()

    return SLAScanReportResponse(
        scanned_count=report.scanned_count,
        warnings_emitted=report.warnings_emitted,
        breached_and_escalated=report.breached_and_escalated,
        evaluation_timestamp=report.evaluation_timestamp,
    )


@router.post(
    "/tickets/{ticket_id}/escalate",
    response_model=EnterpriseTicketResponse,
    summary="Escalate Ticket to Tier-3 Senior Escalations",
)
def escalate_ticket(
    ticket_id: str,
    payload: EscalateTicketRequest,
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> EnterpriseTicketResponse:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        event_bus = getattr(request.app.state, "event_bus", None)
        use_case = EscalateTicketUseCase(repo, event_bus=event_bus)
        dto = EscalateTicketInputDTO(
            ticket_id=ticket_id,
            reason=payload.reason,
            new_team=payload.new_team or "Tier-3 Senior Escalations",
        )
        escalated_ticket = use_case.execute(context, dto)

        return map_ticket_to_response(escalated_ticket)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
