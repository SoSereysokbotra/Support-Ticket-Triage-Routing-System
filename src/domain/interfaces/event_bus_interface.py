"""
Abstract Domain Port for Enterprise Event Bus.
Supports asynchronous event publishing and tenant-scoped subscriptions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from src.domain.entities.event import EnterpriseEvent

# Callback type: synchronous or coroutine-aware handler accepting an EnterpriseEvent
EventSubscriberCallback = Callable[[EnterpriseEvent], None]


class IEventBus(ABC):
    """
    Hexagonal Port for publishing and subscribing to enterprise lifecycle events.
    Implementations may be in-memory (local tests) or distributed (Redis Pub/Sub).
    """

    @abstractmethod
    def publish(self, event: EnterpriseEvent) -> None:
        """Publishes an enterprise domain event."""
        raise NotImplementedError

    @abstractmethod
    def subscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        """
        Subscribes a callback to events.
        If tenant_id is provided, only events matching tenant_id are delivered.
        If tenant_id is None, all events (e.g. system-level audit) are delivered.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        """Removes a previously registered subscriber callback."""
        raise NotImplementedError
