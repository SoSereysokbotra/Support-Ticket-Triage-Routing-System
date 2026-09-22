"""
Alert Dispatcher Background Worker.
Subscribes to the Enterprise Event Bus and asynchronously routes critical alerts to:
1. Slack Interactive Block Kit channels
2. PagerDuty Events API v2
3. Outbound HMAC-SHA256 Signed Webhooks
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.domain.interfaces.event_bus_interface import IEventBus
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.notifications.pagerduty_notifier import PagerDutyNotifier
from src.infrastructure.notifications.slack_notifier import SlackBlockKitNotifier
from src.infrastructure.notifications.webhook_dispatcher import WebhookDispatcher

logger = logging.getLogger("alert_dispatcher_worker")


class AlertDispatcherWorker:
    """
    Asynchronous event bus subscriber that translates domain events
    into external incident dispatches and signed webhook deliveries.
    """

    def __init__(
        self,
        event_bus: IEventBus,
        repository: EnterpriseRepository,
        slack_webhook_url: Optional[str] = None,
        pagerduty_routing_key: Optional[str] = None,
        max_workers: int = 4,
    ) -> None:
        self.event_bus = event_bus
        self.repository = repository
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.pagerduty_routing_key = pagerduty_routing_key or os.getenv("PAGERDUTY_ROUTING_KEY")
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="alert-dispatch")
        self._subscription_ids = []
        self._is_running = False

    def start(self) -> None:
        """Subscribes worker listeners to relevant event types on the event bus."""
        if self._is_running:
            return

        events_to_monitor = [
            EnterpriseEventType.TICKET_INGESTED,
            EnterpriseEventType.SLA_WARNING,
            EnterpriseEventType.TICKET_ESCALATED,
            EnterpriseEventType.TICKET_RESOLVED,
        ]

        for ev_type in events_to_monitor:
            sub_id = self.event_bus.subscribe(ev_type, self._on_event_received)
            self._subscription_ids.append(sub_id)

        self._is_running = True
        logger.info("[AlertDispatcherWorker] Started and subscribed to event bus.")

    def stop(self) -> None:
        """Unsubscribes from event bus and shuts down worker thread pool."""
        if not self._is_running:
            return

        for sub_id in self._subscription_ids:
            try:
                self.event_bus.unsubscribe(sub_id)
            except Exception:
                pass
        self._subscription_ids.clear()
        self._executor.shutdown(wait=False)
        self._is_running = False
        logger.info("[AlertDispatcherWorker] Stopped.")

    def _on_event_received(self, event: EnterpriseEvent) -> None:
        """Schedules non-blocking async dispatch for received domain events."""
        self._executor.submit(self._process_event, event)

    def _process_event(self, event: EnterpriseEvent) -> None:
        """Processes event through Slack, PagerDuty, and Webhook dispatch pipelines."""
        try:
            event_type_str = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )

            # 1. Outbound Webhooks for Tenant
            webhooks = self.repository.get_active_subscriptions_for_event(
                tenant_id=event.tenant_id,
                event_type=event_type_str,
            )
            for sub in webhooks:
                try:
                    WebhookDispatcher.dispatch(sub, event)
                except Exception as e:
                    logger.warning(f"Error dispatching webhook '{sub.subscription_id}': {e}")

            # 2. Slack Block Kit Dispatch
            is_critical = (
                event.payload.get("priority") == "P1_CRITICAL"
                or "security" in str(event.payload.get("predicted_category", "")).lower()
                or event.event_type in (EnterpriseEventType.TICKET_ESCALATED, EnterpriseEventType.SLA_WARNING)
            )

            if is_critical and self.slack_webhook_url:
                try:
                    SlackBlockKitNotifier.send_alert(
                        webhook_url=self.slack_webhook_url,
                        event=event,
                    )
                except Exception as e:
                    logger.warning(f"Error dispatching Slack Block Kit alert: {e}")

            # 3. PagerDuty Incident Dispatch
            is_pagerduty_urgent = (
                event.payload.get("priority") == "P1_CRITICAL"
                or event.event_type == EnterpriseEventType.TICKET_ESCALATED
            )

            if is_pagerduty_urgent and self.pagerduty_routing_key:
                try:
                    PagerDutyNotifier.send_incident(
                        routing_key=self.pagerduty_routing_key,
                        event=event,
                    )
                except Exception as e:
                    logger.warning(f"Error dispatching PagerDuty incident: {e}")

        except Exception as e:
            logger.error(f"Failed to process alert dispatch for event '{event.event_id}': {e}", exc_info=True)
