"""
Enterprise Ticket Management Routes (API v2).
All endpoints are cryptographically scoped by the caller's TenantContext.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.application.use_cases.enterprise_ticket_use_cases import (
    CreateEnterpriseTicketInputDTO,
    CreateEnterpriseTicketUseCase,
    ListEnterpriseTicketsUseCase,
)
from src.domain.entities.tenant import CustomerTier, EnterpriseTicket, TenantContext
from src.presentation.api.dependencies.auth import get_current_tenant_context
from src.presentation.api.schemas.auth_schema import (
    CreateEnterpriseTicketRequest,
    EnterpriseTicketResponse,
)


def map_ticket_to_response(ticket: EnterpriseTicket) -> EnterpriseTicketResponse:
    return EnterpriseTicketResponse(
        ticket_id=ticket.ticket_id,
        tenant_id=ticket.tenant_id,
        title=ticket.title,
        description=ticket.description,
        customer_id=ticket.customer_id,
        customer_tier=ticket.customer_tier.value,
        status=ticket.status.value,
        predicted_category=ticket.predicted_category,
        confidence=ticket.confidence,
        probabilities=ticket.probabilities,
        assigned_team=ticket.assigned_team,
        priority=ticket.priority.value,
        auto_routed=ticket.auto_routed,
        model_version=ticket.model_version,
        latency_ms=ticket.latency_ms,
        created_at=ticket.created_at.isoformat(),
        sla_response_deadline=ticket.sla_response_deadline.isoformat() if ticket.sla_response_deadline else None,
        sla_resolution_deadline=ticket.sla_resolution_deadline.isoformat() if ticket.sla_resolution_deadline else None,
        sla_warning_emitted=ticket.sla_warning_emitted,
        escalated=ticket.escalated,
        escalation_reason=ticket.escalation_reason,
    )


router = APIRouter(prefix="/api/v2/tickets", tags=["Enterprise Multi-Tenant Triage"])


@router.post(
    "",
    response_model=EnterpriseTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest & Triage Enterprise Ticket (Tenant Isolated)",
)
def create_enterprise_ticket(
    payload: CreateEnterpriseTicketRequest,
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> EnterpriseTicketResponse:
    repo = getattr(request.app.state, "enterprise_repository", None)
    predict_use_case = getattr(request.app.state, "predict_use_case", None)

    if not repo or not predict_use_case:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Triage engine or enterprise repository is not ready.",
        )

    try:
        tier_enum = CustomerTier(payload.customer_tier.upper()) if payload.customer_tier else CustomerTier.STANDARD
        dto = CreateEnterpriseTicketInputDTO(
            description=payload.description,
            customer_id=payload.customer_id,
            title=payload.title,
            customer_tier=tier_enum,
            priority_hint=payload.priority_hint,
        )
        use_case = CreateEnterpriseTicketUseCase(
            repository=repo,
            predict_use_case=predict_use_case,
        )
        ticket = use_case.execute(context, dto)
        return map_ticket_to_response(ticket)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=List[EnterpriseTicketResponse],
    summary="List Tickets Belonging to Current Tenant",
)
def list_enterprise_tickets(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    context: TenantContext = Depends(get_current_tenant_context),
) -> List[EnterpriseTicketResponse]:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    use_case = ListEnterpriseTicketsUseCase(repo)
    tickets = use_case.execute(
        context=context,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [map_ticket_to_response(t) for t in tickets]


@router.get(
    "/{ticket_id}",
    response_model=EnterpriseTicketResponse,
    summary="Retrieve a Single Ticket Within Tenant Boundary",
)
def get_enterprise_ticket(
    ticket_id: str,
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> EnterpriseTicketResponse:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    ticket = repo.get_by_id_tenant(tenant_id=context.tenant_id, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found in current tenant.",
        )

    return map_ticket_to_response(ticket)
