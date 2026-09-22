"""
Enterprise Routes for Agent Copilot and Human-in-the-Loop Feedback (API v2).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.use_cases.copilot_use_cases import (
    ApproveCopilotDraftUseCase,
    GenerateCopilotDraftUseCase,
)
from src.application.use_cases.feedback_use_cases import (
    GetFeedbackStatsUseCase,
    SubmitAgentFeedbackInputDTO,
    SubmitAgentFeedbackUseCase,
)
from src.domain.entities.tenant import TenantContext, UserRole
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.events.event_bus import IEventBus
from src.presentation.api.dependencies.auth import (
    get_current_tenant_context,
    require_roles,
)
from src.presentation.api.routes.tickets_v2 import map_ticket_to_response
from src.presentation.api.schemas.auth_schema import EnterpriseTicketResponse
from src.presentation.api.schemas.copilot_schema import (
    AgentFeedbackRequest,
    AgentFeedbackResponse,
    CopilotDraftResponse,
    FeedbackStatsResponse,
)

logger = logging.getLogger("copilot_routes")

router = APIRouter(prefix="/api/v2/tickets", tags=["Copilot & HITL Feedback"])


@router.post(
    "/{ticket_id}/feedback",
    response_model=AgentFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Agent Ground-Truth Reclassification (Active Learning)",
)
def submit_agent_feedback(
    ticket_id: str,
    payload: AgentFeedbackRequest,
    request: Request,
    context: TenantContext = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.TRIAGE_LEAD,
            UserRole.TENANT_ADMIN,
            UserRole.SUPERADMIN,
        )
    ),
) -> AgentFeedbackResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    event_bus: Optional[IEventBus] = getattr(request.app.state, "event_bus", None)

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = SubmitAgentFeedbackUseCase(repository=repo, event_bus=event_bus)
        dto = SubmitAgentFeedbackInputDTO(
            ticket_id=ticket_id,
            corrected_category=payload.corrected_category,
            corrected_priority=payload.corrected_priority,
            reclassification_reason=payload.reclassification_reason,
        )
        result = use_case.execute(context=context, dto=dto)
        ann = result.annotation

        return AgentFeedbackResponse(
            feedback_id=ann.feedback_id,
            tenant_id=ann.tenant_id,
            ticket_id=ann.ticket_id,
            agent_id=ann.agent_id,
            original_category=ann.original_category,
            corrected_category=ann.corrected_category,
            original_priority=ann.original_priority,
            corrected_priority=ann.corrected_priority,
            model_version=ann.model_version,
            original_confidence=ann.original_confidence,
            reclassification_reason=ann.reclassification_reason,
            is_high_confidence_error=ann.is_high_confidence_error,
            sample_weight=ann.sample_weight,
            retraining_threshold_reached=result.retraining_threshold_reached,
            created_at=ann.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/feedback/stats",
    response_model=FeedbackStatsResponse,
    summary="Get Tenant Feedback Metrics & Active Retraining Status",
)
def get_feedback_stats(
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> FeedbackStatsResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    use_case = GetFeedbackStatsUseCase(repository=repo)
    stats = use_case.execute(context)

    return FeedbackStatsResponse(
        tenant_id=stats["tenant_id"],
        total_annotations=stats["total_annotations"],
        unprocessed_annotations=stats["unprocessed_annotations"],
        high_confidence_false_positives=stats["high_confidence_false_positives"],
        retraining_threshold_reached=stats["retraining_threshold_reached"],
    )


@router.post(
    "/{ticket_id}/copilot/generate",
    response_model=CopilotDraftResponse,
    summary="Generate Grounded Copilot Resolution Draft (RAG)",
)
def generate_copilot_draft(
    ticket_id: str,
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> CopilotDraftResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = GenerateCopilotDraftUseCase(repository=repo)
        _, draft = use_case.execute(context=context, ticket_id=ticket_id)

        return CopilotDraftResponse(
            ticket_id=ticket_id,
            suggested_response=draft.suggested_response,
            copilot_confidence=draft.confidence,
            sources=draft.sources,
            is_skipped=draft.is_skipped,
            skip_reason=draft.skip_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{ticket_id}/copilot/approve",
    response_model=EnterpriseTicketResponse,
    summary="1-Click Agent Approval (Resolves Ticket)",
)
def approve_copilot_draft(
    ticket_id: str,
    request: Request,
    context: TenantContext = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.TRIAGE_LEAD,
            UserRole.TENANT_ADMIN,
            UserRole.SUPERADMIN,
        )
    ),
) -> EnterpriseTicketResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    event_bus: Optional[IEventBus] = getattr(request.app.state, "event_bus", None)

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = ApproveCopilotDraftUseCase(repository=repo, event_bus=event_bus)
        resolved_ticket = use_case.execute(context=context, ticket_id=ticket_id)
        return map_ticket_to_response(resolved_ticket)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
