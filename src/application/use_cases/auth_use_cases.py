"""
Application Use Cases for Enterprise Authentication, Tenant Onboarding, and JWT Issuance.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.tenant import Tenant, TenantPlan, User, UserRole
from src.infrastructure.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from src.infrastructure.database.enterprise_repository import EnterpriseRepository


@dataclass
class RegisterTenantInputDTO:
    company_name: str
    slug: str
    admin_email: str
    admin_password: str
    admin_full_name: str
    plan: TenantPlan = TenantPlan.GROWTH


@dataclass
class AuthResponseDTO:
    access_token: str
    token_type: str
    tenant_id: str
    user_id: str
    role: str
    email: str
    full_name: str
    company_name: str


class RegisterTenantUseCase:
    """Provisions an enterprise tenant and its initial TenantAdmin user."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, dto: RegisterTenantInputDTO) -> AuthResponseDTO:
        existing_tenant = self.repository.get_by_slug(dto.slug.strip().lower())
        if existing_tenant:
            raise ValueError(f"Tenant slug '{dto.slug}' is already registered.")

        # 1. Create Tenant Entity
        tenant = Tenant(
            company_name=dto.company_name.strip(),
            slug=dto.slug.strip().lower(),
            plan=dto.plan,
        )
        self.repository.create(tenant)

        # 2. Create Initial Tenant Admin User
        password_hash = hash_password(dto.admin_password)
        admin_user = User(
            tenant_id=tenant.tenant_id,
            email=dto.admin_email.strip().lower(),
            password_hash=password_hash,
            full_name=dto.admin_full_name.strip(),
            role=UserRole.TENANT_ADMIN,
        )
        self.repository.create_user(admin_user)

        # 3. Issue JWT Access Token
        token = create_access_token(
            data={
                "sub": admin_user.user_id,
                "tenant_id": tenant.tenant_id,
                "role": admin_user.role.value,
                "email": admin_user.email,
            }
        )

        return AuthResponseDTO(
            access_token=token,
            token_type="bearer",
            tenant_id=tenant.tenant_id,
            user_id=admin_user.user_id,
            role=admin_user.role.value,
            email=admin_user.email,
            full_name=admin_user.full_name,
            company_name=tenant.company_name,
        )


class AuthenticateUserUseCase:
    """Authenticates credentials and returns a signed JWT with tenant claims."""

    def __init__(self, repository: EnterpriseRepository) -> None:
        self.repository = repository

    def execute(self, tenant_slug: str, email: str, password: str) -> AuthResponseDTO:
        tenant = self.repository.get_by_slug(tenant_slug.strip().lower())
        if not tenant or not tenant.is_active:
            raise ValueError("Invalid tenant or tenant account is inactive.")

        user = self.repository.get_user_by_email(tenant.tenant_id, email.strip().lower())
        if not user or not user.is_active:
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")

        token = create_access_token(
            data={
                "sub": user.user_id,
                "tenant_id": tenant.tenant_id,
                "role": user.role.value,
                "email": user.email,
            }
        )

        return AuthResponseDTO(
            access_token=token,
            token_type="bearer",
            tenant_id=tenant.tenant_id,
            user_id=user.user_id,
            role=user.role.value,
            email=user.email,
            full_name=user.full_name,
            company_name=tenant.company_name,
        )
