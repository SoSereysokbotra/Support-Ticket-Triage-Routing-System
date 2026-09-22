"""
Enterprise Webhook Subscription & Integration Management Routes (API v2).
Enforces strict tenant isolation and role-based permissions for webhook configurations.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.use_cases.webhook_use_cases import (
    CreateWebhookSubscriptionInputDTO,
    CreateWebhookSubscriptionUseCase,
    DeleteWebhookSubscriptionUseCase,
    ListWebhookSubscriptionsUseCase,
    TestWebhookDeliveryUseCase,
)
from src.domain.entities.tenant import TenantContext, UserRole
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.presentation.api.dependencies.auth import (
    get_current_tenant_context,
    require_roles,
)
from src.presentation.api.schemas.webhook_schema import (
    CreateWebhookSubscriptionRequest,
    TestWebhookDeliveryResponse,
    WebhookSubscriptionResponse,
)

router = APIRouter(prefix="/api/v2/webhooks", tags=["Enterprise Outbound Webhooks"])


@router.post(
    "/subscriptions",
    response_model=WebhookSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Outbound Webhook Subscription",
)
def create_webhook_subscription(
    payload: CreateWebhookSubscriptionRequest,
    request: Request,
    context: TenantContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.SUPERADMIN)),
) -> WebhookSubscriptionResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = CreateWebhookSubscriptionUseCase(repository=repo)
        dto = CreateWebhookSubscriptionInputDTO(
            target_url=payload.target_url,
            events_subscribed=payload.events_subscribed,
            secret_token=payload.secret_token,
            description=payload.description,
        )
        sub = use_case.execute(context=context, dto=dto)
        return WebhookSubscriptionResponse(
            subscription_id=sub.subscription_id,
            tenant_id=sub.tenant_id,
            target_url=sub.target_url,
            secret_token=sub.secret_token,
            events_subscribed=sub.events_subscribed,
            description=sub.description,
            is_active=sub.is_active,
            created_at=sub.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/subscriptions",
    response_model=List[WebhookSubscriptionResponse],
    summary="List Tenant Webhook Subscriptions",
)
def list_webhook_subscriptions(
    request: Request,
    context: TenantContext = Depends(get_current_tenant_context),
) -> List[WebhookSubscriptionResponse]:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    use_case = ListWebhookSubscriptionsUseCase(repository=repo)
    subs = use_case.execute(context=context)
    return [
        WebhookSubscriptionResponse(
            subscription_id=s.subscription_id,
            tenant_id=s.tenant_id,
            target_url=s.target_url,
            secret_token=s.secret_token,
            events_subscribed=s.events_subscribed,
            description=s.description,
            is_active=s.is_active,
            created_at=s.created_at.isoformat(),
        )
        for s in subs
    ]


@router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Webhook Subscription",
)
def delete_webhook_subscription(
    subscription_id: str,
    request: Request,
    context: TenantContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.SUPERADMIN)),
) -> None:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = DeleteWebhookSubscriptionUseCase(repository=repo)
        use_case.execute(context=context, subscription_id=subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/subscriptions/{subscription_id}/test",
    response_model=TestWebhookDeliveryResponse,
    summary="Test Ping Webhook Connectivity",
)
def test_webhook_delivery(
    subscription_id: str,
    request: Request,
    context: TenantContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.SUPERADMIN)),
) -> TestWebhookDeliveryResponse:
    repo: Optional[EnterpriseRepository] = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not ready.",
        )

    try:
        use_case = TestWebhookDeliveryUseCase(repository=repo)
        success, status_code, latency_ms, error_msg = use_case.execute(
            context=context,
            subscription_id=subscription_id,
        )
        return TestWebhookDeliveryResponse(
            subscription_id=subscription_id,
            success=success,
            status_code=status_code,
            latency_ms=latency_ms,
            error_message=error_msg,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
