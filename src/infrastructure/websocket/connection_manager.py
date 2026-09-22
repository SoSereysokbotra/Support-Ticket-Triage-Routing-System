"""
Enterprise WebSocket Connection Manager.
Manages multi-tenant WebSocket pools, provides tenant-isolated real-time broadcasts,
and bridges IEventBus domain events to connected browser agents.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

from src.domain.entities.event import EnterpriseEvent
from src.domain.interfaces.event_bus_interface import IEventBus

logger = logging.getLogger("websocket_manager")


class WebSocketConnectionManager:
    """
    Thread-safe and async-safe WebSocket Connection Pool.
    Maintains active connections segregated by tenant_id to guarantee zero cross-tenant leakage.
    Automatically listens to an IEventBus and dispatches events to the correct tenant clients.
    """

    def __init__(self, event_bus: Optional[IEventBus] = None) -> None:
        self._lock = threading.RLock()
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_bus = event_bus

        if self._event_bus:
            # Subscribe to all events globally to route them to tenant WebSockets
            self._event_bus.subscribe(None, self._on_event_received)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Explicitly records the main async event loop for background threadsafe dispatch."""
        self._loop = loop

    async def connect(self, websocket: WebSocket, tenant_id: str) -> None:
        """Accepts a WebSocket connection and registers it in the tenant pool."""
        await websocket.accept()
        with self._lock:
            if tenant_id not in self._active_connections:
                self._active_connections[tenant_id] = set()
            self._active_connections[tenant_id].add(websocket)

        # Cache running loop if not already captured
        if not self._loop:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        logger.info(
            f"[WebSocket] Client connected to tenant='{tenant_id}'. Active count: {len(self._active_connections[tenant_id])}"
        )

    def disconnect(self, websocket: WebSocket, tenant_id: str) -> None:
        """Unregisters a WebSocket connection from the tenant pool."""
        with self._lock:
            if tenant_id in self._active_connections:
                self._active_connections[tenant_id].discard(websocket)
                if not self._active_connections[tenant_id]:
                    del self._active_connections[tenant_id]

        logger.info(f"[WebSocket] Client disconnected from tenant='{tenant_id}'.")

    async def broadcast_to_tenant(self, tenant_id: str, message: dict) -> None:
        """
        Broadcasts a JSON message exclusively to all active WebSockets
        belonging to the specified tenant.
        """
        with self._lock:
            sockets: List[WebSocket] = list(self._active_connections.get(tenant_id, set()))

        if not sockets:
            return

        dead_sockets: List[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(
                    f"[WebSocket] Error sending to client in tenant='{tenant_id}': {e}. Marking for cleanup."
                )
                dead_sockets.append(ws)

        if dead_sockets:
            with self._lock:
                if tenant_id in self._active_connections:
                    for dead in dead_sockets:
                        self._active_connections[tenant_id].discard(dead)
                    if not self._active_connections[tenant_id]:
                        del self._active_connections[tenant_id]

    def _on_event_received(self, event: EnterpriseEvent) -> None:
        """
        Callback invoked by IEventBus when a domain event is published.
        Bridges the event into the running async event loop for WebSocket delivery.
        """
        payload = event.to_dict()
        tenant_id = event.tenant_id

        # Determine how to execute the async broadcast
        try:
            loop = self._loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_to_tenant(tenant_id, payload),
                    loop,
                )
            else:
                # Try getting current running loop if called from async context
                try:
                    current_loop = asyncio.get_running_loop()
                    current_loop.create_task(self.broadcast_to_tenant(tenant_id, payload))
                except RuntimeError:
                    # No active event loop running (e.g. unit tests without async loop)
                    pass
        except Exception as e:
            logger.error(f"[WebSocket] Failed to schedule event broadcast: {e}", exc_info=True)

    def get_active_count(self, tenant_id: Optional[str] = None) -> int:
        """Returns the count of active WebSocket connections."""
        with self._lock:
            if tenant_id:
                return len(self._active_connections.get(tenant_id, set()))
            return sum(len(s) for s in self._active_connections.values())
