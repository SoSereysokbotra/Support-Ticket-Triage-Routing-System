"""
Enterprise Multi-Tenant Authentication & Identity Routes (API v2).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.use_cases.auth_use_cases import (
    AuthenticateUserUseCase,
    RegisterTenantInputDTO,
    RegisterTenantUseCase,
)
from src.domain.entities.tenant import TenantContext, TenantPlan
from src.presentation.api.dependencies.auth import get_current_tenant_context
from src.presentation.api.schemas.auth_schema import (
    AuthResponse,
    LoginRequest,
    RegisterTenantRequest,
    UserProfileResponse,
)

router = APIRouter(prefix="/api/v2/auth", tags=["Enterprise Identity & RBAC"])


@router.post(
    "/register-tenant",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new Enterprise Tenant & TenantAdmin",
)
def register_tenant(
    payload: RegisterTenantRequest,
    request: Request,
) -> AuthResponse:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not initialized.",
        )

    try:
        plan_enum = TenantPlan(payload.plan.upper()) if payload.plan else TenantPlan.GROWTH
        dto = RegisterTenantInputDTO(
            company_name=payload.company_name,
            slug=payload.slug,
            admin_email=payload.admin_email,
            admin_password=payload.admin_password,
            admin_full_name=payload.admin_full_name,
            plan=plan_enum,
        )
        use_case = RegisterTenantUseCase(repo)
        result = use_case.execute(dto)
        return AuthResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            tenant_id=result.tenant_id,
            user_id=result.user_id,
            role=result.role,
            email=result.email,
            full_name=result.full_name,
            company_name=result.company_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate User and Issue JWT Access Token",
)
def login(
    payload: LoginRequest,
    request: Request,
) -> AuthResponse:
    repo = getattr(request.app.state, "enterprise_repository", None)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise repository is not initialized.",
        )

    try:
        use_case = AuthenticateUserUseCase(repo)
        result = use_case.execute(
            tenant_slug=payload.tenant_slug,
            email=payload.email,
            password=payload.password,
        )
        return AuthResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            tenant_id=result.tenant_id,
            user_id=result.user_id,
            role=result.role,
            email=result.email,
            full_name=result.full_name,
            company_name=result.company_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Inspect Authenticated Tenant Identity",
)
def get_current_user_profile(
    context: TenantContext = Depends(get_current_tenant_context),
) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        email=context.email,
        role=context.role.value,
    )
