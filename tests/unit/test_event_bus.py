"""
Unit Tests for Enterprise Event Bus & WebSocket Connection Manager.
Verifies event serialization, tenant isolation in pub/sub dispatch,
and multi-tenant WebSocket connection pool management.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.infrastructure.events.event_bus import InMemoryEventBus
from src.infrastructure.websocket.connection_manager import WebSocketConnectionManager


class TestEnterpriseEvent:
    def test_event_serialization_round_trip(self):
        event = EnterpriseEvent(
            event_type=EnterpriseEventType.TICKET_INGESTED,
            tenant_id="tenant-alpha",
            ticket_id="ticket-999",
            payload={"category": "Network", "priority": "P1_CRITICAL"},
        )
        data = event.to_dict()
        assert data["event_type"] == "ticket.ingested"
        assert data["tenant_id"] == "tenant-alpha"
        assert data["ticket_id"] == "ticket-999"
        assert data["payload"]["category"] == "Network"
        assert "event_id" in data
        assert "timestamp" in data

        hydrated = EnterpriseEvent.from_dict(data)
        assert hydrated.event_id == event.event_id
        assert hydrated.event_type == EnterpriseEventType.TICKET_INGESTED
        assert hydrated.tenant_id == "tenant-alpha"
        assert hydrated.ticket_id == "ticket-999"
        assert hydrated.payload["priority"] == "P1_CRITICAL"


class TestInMemoryEventBus:
    def test_tenant_subscription_and_isolation(self):
        bus = InMemoryEventBus()
        tenant_a_events = []
        tenant_b_events = []
        global_events = []

        bus.subscribe("tenant-a", lambda e: tenant_a_events.append(e))
        bus.subscribe("tenant-b", lambda e: tenant_b_events.append(e))
        bus.subscribe(None, lambda e: global_events.append(e))

        # 1. Publish Event for Tenant A
        event_a = EnterpriseEvent(
            event_type=EnterpriseEventType.TICKET_INGESTED,
            tenant_id="tenant-a",
            ticket_id="ticket-001",
            payload={"info": "A"},
        )
        bus.publish(event_a)

        assert len(tenant_a_events) == 1
        assert tenant_a_events[0].ticket_id == "ticket-001"
        # Strict isolation: Tenant B never receives Tenant A's event
        assert len(tenant_b_events) == 0
        # Global subscriber receives all events
        assert len(global_events) == 1

        # 2. Publish Event for Tenant B
        event_b = EnterpriseEvent(
            event_type=EnterpriseEventType.SLA_WARNING,
            tenant_id="tenant-b",
            ticket_id="ticket-002",
            payload={"info": "B"},
        )
        bus.publish(event_b)

        assert len(tenant_a_events) == 1
        assert len(tenant_b_events) == 1
        assert tenant_b_events[0].ticket_id == "ticket-002"
        assert len(global_events) == 2

    def test_unsubscribe(self):
        bus = InMemoryEventBus()
        received = []

        def cb(e):
            received.append(e)

        bus.subscribe("tenant-x", cb)
        bus.publish(EnterpriseEvent(EnterpriseEventType.TICKET_INGESTED, "tenant-x", "t1", {}))
        assert len(received) == 1

        bus.unsubscribe("tenant-x", cb)
        bus.publish(EnterpriseEvent(EnterpriseEventType.TICKET_INGESTED, "tenant-x", "t2", {}))
        assert len(received) == 1


class TestWebSocketConnectionManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect_and_active_counts(self):
        manager = WebSocketConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Connect ws1 for Tenant 1
        await manager.connect(mock_ws1, tenant_id="tenant-1")
        mock_ws1.accept.assert_awaited_once()
        assert manager.get_active_count("tenant-1") == 1
        assert manager.get_active_count("tenant-2") == 0
        assert manager.get_active_count() == 1

        # Connect ws2 for Tenant 2
        await manager.connect(mock_ws2, tenant_id="tenant-2")
        assert manager.get_active_count("tenant-1") == 1
        assert manager.get_active_count("tenant-2") == 1
        assert manager.get_active_count() == 2

        # Disconnect ws1
        manager.disconnect(mock_ws1, tenant_id="tenant-1")
        assert manager.get_active_count("tenant-1") == 0
        assert manager.get_active_count("tenant-2") == 1
        assert manager.get_active_count() == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_tenant_isolation(self):
        manager = WebSocketConnectionManager()
        ws_a = AsyncMock()
        ws_b = AsyncMock()

        await manager.connect(ws_a, tenant_id="tenant-a")
        await manager.connect(ws_b, tenant_id="tenant-b")

        msg_a = {"event": "ticket_created", "ticket_id": "T-100"}
        await manager.broadcast_to_tenant("tenant-a", msg_a)

        # ws_a should have received msg_a
        ws_a.send_json.assert_awaited_once_with(msg_a)
        # ws_b should NOT have received msg_a
        ws_b.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dead_socket_cleanup_on_send_error(self):
        manager = WebSocketConnectionManager()
        bad_ws = AsyncMock()
        bad_ws.send_json.side_effect = RuntimeError("Socket closed abruptly")

        await manager.connect(bad_ws, tenant_id="tenant-fail")
        assert manager.get_active_count("tenant-fail") == 1

        # Broadcasting to failing socket should handle error and clean up
        await manager.broadcast_to_tenant("tenant-fail", {"test": "data"})
        assert manager.get_active_count("tenant-fail") == 0
