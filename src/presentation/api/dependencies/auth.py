"""
FastAPI Authentication & RBAC Dependencies.
Extracts JWT Bearer tokens, decodes TenantContext, and enforces role permissions.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Header, HTTPException, status

from src.domain.entities.tenant import TenantContext, UserRole
from src.infrastructure.auth.security import decode_access_token


async def get_current_tenant_context(
    authorization: str = Header(..., description="Bearer JWT access token"),
) -> TenantContext:
    """
    Dependency that validates the Authorization header, decodes the JWT,
    and returns the immutable TenantContext for the current request.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:].strip()
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role_str = payload.get("role")
        email = payload.get("email")

        if not user_id or not tenant_id or not role_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token payload.",
            )

        return TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=UserRole(role_str),
            email=email or "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Factory dependency ensuring the authenticated user holds at least one
    of the required UserRoles (SuperAdmin bypasses automatically).
    """

    async def role_checker(
        context: TenantContext = Depends(get_current_tenant_context),
    ) -> TenantContext:
        if not context.has_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return context

    return role_checker
