"""
Enterprise WebSocket Routes for Real-Time Triage & SLA Notifications (API v2).
Enforces cryptographic token authentication and strict tenant-isolated message dispatch.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from starlette.status import WS_1008_POLICY_VIOLATION, WS_1011_INTERNAL_ERROR

from src.domain.entities.tenant import TenantContext, UserRole
from src.infrastructure.auth.security import decode_access_token
from src.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from src.presentation.api.dependencies.auth import (
    require_roles,
)

logger = logging.getLogger("websocket_route")

router = APIRouter(prefix="/api/v2", tags=["Real-Time Triage WebSockets"])

ALLOWED_WS_ROLES = {
    UserRole.SUPPORT_AGENT.value,
    UserRole.TRIAGE_LEAD.value,
    UserRole.TENANT_ADMIN.value,
    UserRole.SUPERADMIN.value,
}


@router.websocket("/ws/triage")
async def websocket_triage_feed(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
) -> None:
    """
    Real-time streaming WebSocket endpoint for agent queues and SLA watchdog notifications.
    Authenticates via `?token=<jwt_token>` query parameter.
    Streams events (`ticket.ingested`, `ticket.sla_warning`, `ticket.escalated`) in real-time.
    """
    manager: Optional[WebSocketConnectionManager] = getattr(
        websocket.app.state, "websocket_manager", None
    )

    if not manager:
        logger.error("[WebSocket] Connection rejected: WebSocketConnectionManager not initialized.")
        await websocket.close(code=WS_1011_INTERNAL_ERROR, reason="WebSocket manager not initialized.")
        return

    if not token:
        logger.warning("[WebSocket] Connection rejected: Missing authentication token.")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Missing authentication token.")
        return

    # Cryptographic JWT Token Verification
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        logger.warning(f"[WebSocket] Connection rejected: Invalid token - {e}")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason=f"Unauthorized: {e}")
        return

    tenant_id: Optional[str] = payload.get("tenant_id")
    user_id: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")

    if not tenant_id or not user_id:
        logger.warning("[WebSocket] Connection rejected: Malformed claims in token.")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Malformed token claims.")
        return

    if role not in ALLOWED_WS_ROLES:
        logger.warning(f"[WebSocket] Connection rejected: Role '{role}' not authorized for live queue.")
        await websocket.close(code=WS_1008_POLICY_VIOLATION, reason="Forbidden role.")
        return

    # Accept connection and register in tenant's connection pool
    await manager.connect(websocket, tenant_id=tenant_id)

    # Send handshake confirmation
    await websocket.send_json({
        "type": "connection_established",
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role": role,
    })

    try:
        while True:
            # Listen for client heartbeat/ping
            message = await websocket.receive_text()
            if message in ("ping", '{"type":"ping"}', '{"type": "ping"}'):
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id=tenant_id)
        logger.info(f"[WebSocket] Client {user_id} disconnected cleanly from tenant {tenant_id}.")
    except Exception as e:
        manager.disconnect(websocket, tenant_id=tenant_id)
        logger.warning(f"[WebSocket] Client {user_id} connection terminated: {e}")


@router.get(
    "/ws/stats",
    summary="Get Active WebSocket Connection Metrics (Tenant Scoped)",
)
def get_websocket_stats(
    request: Request,
    context: TenantContext = Depends(
        require_roles(UserRole.TENANT_ADMIN, UserRole.TRIAGE_LEAD, UserRole.SUPERADMIN)
    ),
) -> Dict[str, object]:
    """Returns active real-time agent connections for the current tenant."""
    manager: Optional[WebSocketConnectionManager] = getattr(
        request.app.state, "websocket_manager", None
    )
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WebSocket manager is not initialized.",
        )

    tenant_count = manager.get_active_count(tenant_id=context.tenant_id)
    total_count = manager.get_active_count()

    return {
        "tenant_id": context.tenant_id,
        "active_agent_connections": tenant_count,
        "cluster_total_connections": total_count,
    }
