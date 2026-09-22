"""
Enterprise Event Bus Implementations (Hexagonal Adapter Layer).
Provides InMemoryEventBus for unit testing and local development,
and RedisEventBus for distributed multi-worker production deployments.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Dict, List, Optional, Set

from src.domain.entities.event import EnterpriseEvent
from src.domain.interfaces.event_bus_interface import (
    EventSubscriberCallback,
    IEventBus,
)

logger = logging.getLogger("event_bus")


class InMemoryEventBus(IEventBus):
    """
    Thread-safe in-process event bus.
    Routes events to registered subscriber callbacks based on tenant_id or wildcard.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tenant_subscribers: Dict[str, Set[EventSubscriberCallback]] = {}
        self._global_subscribers: Set[EventSubscriberCallback] = set()

    def publish(self, event: EnterpriseEvent) -> None:
        """Publishes an event to tenant-specific and global subscribers."""
        with self._lock:
            tenant_callbacks: List[EventSubscriberCallback] = list(
                self._tenant_subscribers.get(event.tenant_id, set())
            )
            global_callbacks: List[EventSubscriberCallback] = list(
                self._global_subscribers
            )

        # Dispatch outside lock to prevent deadlocks in subscriber callbacks
        for callback in tenant_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in tenant subscriber callback for tenant={event.tenant_id}: {e}",
                    exc_info=True,
                )

        for callback in global_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in global subscriber callback: {e}",
                    exc_info=True,
                )

    def subscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        """Registers a subscriber callback."""
        with self._lock:
            if tenant_id:
                if tenant_id not in self._tenant_subscribers:
                    self._tenant_subscribers[tenant_id] = set()
                self._tenant_subscribers[tenant_id].add(callback)
            else:
                self._global_subscribers.add(callback)

    def unsubscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        """Unregisters a subscriber callback."""
        with self._lock:
            if tenant_id and tenant_id in self._tenant_subscribers:
                self._tenant_subscribers[tenant_id].discard(callback)
                if not self._tenant_subscribers[tenant_id]:
                    del self._tenant_subscribers[tenant_id]
            elif callback in self._global_subscribers:
                self._global_subscribers.discard(callback)


class RedisEventBus(IEventBus):
    """
    Distributed Event Bus adapter backed by Redis Pub/Sub.
    Enables cross-process and cross-container notification synchronization.
    """

    CHANNEL_PREFIX = "enterprise_events"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        redis_client: Optional[object] = None,
    ) -> None:
        import redis

        self._in_memory = InMemoryEventBus()
        if redis_client:
            self._client = redis_client
        else:
            self._client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True,
            )

        self._pubsub = self._client.pubsub()
        self._pubsub_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_listener()

    def _start_listener(self) -> None:
        """Subscribes to Redis pattern and begins background dispatch loop."""
        pattern = f"{self.CHANNEL_PREFIX}:*"
        self._pubsub.psubscribe(pattern)

        def listener_loop():
            for message in self._pubsub.listen():
                if self._stop_event.is_set():
                    break
                if message.get("type") == "pmessage":
                    try:
                        raw_data = message.get("data")
                        if isinstance(raw_data, str):
                            data = json.loads(raw_data)
                            event = EnterpriseEvent.from_dict(data)
                            self._in_memory.publish(event)
                    except Exception as e:
                        logger.error(f"RedisEventBus listener parse error: {e}")

        self._pubsub_thread = threading.Thread(
            target=listener_loop, daemon=True, name="RedisEventBus-Listener"
        )
        self._pubsub_thread.start()

    def publish(self, event: EnterpriseEvent) -> None:
        """Publishes event to Redis pub/sub channel for the specific tenant."""
        channel = f"{self.CHANNEL_PREFIX}:{event.tenant_id}"
        payload = json.dumps(event.to_dict())
        self._client.publish(channel, payload)
        # Also publish immediately in current process
        self._in_memory.publish(event)

    def subscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        self._in_memory.subscribe(tenant_id, callback)

    def unsubscribe(
        self,
        tenant_id: Optional[str],
        callback: EventSubscriberCallback,
    ) -> None:
        self._in_memory.unsubscribe(tenant_id, callback)

    def stop(self) -> None:
        """Stops pubsub listener thread."""
        self._stop_event.set()
        try:
            self._pubsub.close()
        except Exception:
            pass


def create_event_bus() -> IEventBus:
    """
    Factory function creating an appropriate IEventBus instance.
    Defaults to RedisEventBus if REDIS_HOST or REDIS_URL is configured and reachable,
    otherwise gracefully falls back to InMemoryEventBus.
    """
    redis_host = os.getenv("REDIS_HOST")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    if redis_host:
        try:
            import redis

            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                socket_connect_timeout=2.0,
                decode_responses=True,
            )
            client.ping()
            logger.info(f"[EventBus] Connected to Redis Pub/Sub at {redis_host}:{redis_port}")
            return RedisEventBus(redis_client=client)
        except Exception as e:
            logger.warning(
                f"[EventBus] Redis connection failed ({e}). Falling back to InMemoryEventBus."
            )

    logger.info("[EventBus] Initialized local InMemoryEventBus.")
    return InMemoryEventBus()
