"""
Application Use Cases for Outbound Webhook Management and Connectivity Diagnostics.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from src.domain.entities.tenant import TenantContext
from src.domain.entities.webhook import WebhookSubscription
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.notifications.webhook_dispatcher import WebhookDispatcher


@dataclass
class CreateWebhookSubscriptionInputDTO:
    target_url: str
    events_subscribed: List[str]
    secret_token: Optional[str] = None
    description: Optional[str] = None


class CreateWebhookSubscriptionUseCase:
    """Validates and registers an external webhook subscription for the tenant."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(
        self,
        context: TenantContext,
        dto: CreateWebhookSubscriptionInputDTO,
    ) -> WebhookSubscription:
        parsed = urlparse(dto.target_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid webhook target URL '{dto.target_url}'. Must begin with 'http://' or 'https://'.")

        secret = dto.secret_token or secrets.token_hex(24)
        events = dto.events_subscribed if dto.events_subscribed else ["*"]

        subscription = WebhookSubscription(
            tenant_id=context.tenant_id,
            target_url=dto.target_url,
            secret_token=secret,
            events_subscribed=events,
            description=dto.description,
            is_active=True,
        )

        return self.repository.save_webhook_subscription(subscription)


class ListWebhookSubscriptionsUseCase:
    """Lists all registered webhooks for the tenant."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, context: TenantContext) -> List[WebhookSubscription]:
        return self.repository.list_webhook_subscriptions(context.tenant_id)


class DeleteWebhookSubscriptionUseCase:
    """Removes a registered webhook subscription within tenant scope."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, context: TenantContext, subscription_id: str) -> bool:
        deleted = self.repository.delete_webhook_subscription(
            tenant_id=context.tenant_id,
            subscription_id=subscription_id,
        )
        if not deleted:
            raise ValueError(f"Webhook subscription '{subscription_id}' not found in current tenant.")
        return True


class TestWebhookDeliveryUseCase:
    """Dispatches a signed test ping event to verify webhook URL accessibility."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(
        self,
        context: TenantContext,
        subscription_id: str,
    ) -> Tuple[bool, int, float, Optional[str]]:
        sub = self.repository.get_webhook_subscription(
            tenant_id=context.tenant_id,
            subscription_id=subscription_id,
        )
        if not sub:
            raise ValueError(f"Webhook subscription '{subscription_id}' not found in current tenant.")

        return WebhookDispatcher.test_ping(subscription=sub)
