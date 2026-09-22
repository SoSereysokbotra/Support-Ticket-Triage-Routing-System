"""
Unit Tests for Enterprise Authentication, Cryptography, and RBAC.
"""

from datetime import timedelta

import pytest

from src.application.use_cases.auth_use_cases import (
    AuthenticateUserUseCase,
    RegisterTenantInputDTO,
    RegisterTenantUseCase,
)
from src.domain.entities.tenant import Tenant, TenantContext, TenantPlan, User, UserRole
from src.infrastructure.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.infrastructure.database.enterprise_repository import EnterpriseRepository


class TestEnterpriseSecurity:
    def test_password_hashing_and_verification(self):
        plain = "SuperSecretP@ssw0rd!"
        hashed = hash_password(plain)

        assert hashed.startswith("pbkdf2:sha256:")
        assert verify_password(plain, hashed) is True
        assert verify_password("WrongPassword!", hashed) is False

    def test_different_salts_for_same_password(self):
        plain = "SamePassword123"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)

        assert hash1 != hash2
        assert verify_password(plain, hash1) is True
        assert verify_password(plain, hash2) is True

    def test_jwt_token_creation_and_decoding(self):
        payload = {
            "sub": "user_123",
            "tenant_id": "tenant_abc",
            "role": "TENANT_ADMIN",
            "email": "admin@acme.com",
        }
        token = create_access_token(payload, expires_delta=timedelta(minutes=15))
        assert isinstance(token, str)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "user_123"
        assert decoded["tenant_id"] == "tenant_abc"
        assert decoded["role"] == "TENANT_ADMIN"
        assert decoded["email"] == "admin@acme.com"

    def test_expired_token_raises_value_error(self):
        payload = {"sub": "user_123", "tenant_id": "tenant_abc"}
        expired_token = create_access_token(payload, expires_delta=timedelta(seconds=-10))

        with pytest.raises(ValueError, match="expired"):
            decode_access_token(expired_token)

    def test_tampered_token_raises_value_error(self):
        token = create_access_token({"sub": "user_123"})
        tampered_token = token[:-5] + "XXXXX"

        with pytest.raises(ValueError):
            decode_access_token(tampered_token)


class TestTenantDomainEntities:
    def test_tenant_creation_and_validation(self):
        tenant = Tenant(company_name="Acme Corp", slug="acme-corp", plan=TenantPlan.ENTERPRISE)
        assert tenant.tenant_id is not None
        assert tenant.slug == "acme-corp"
        assert tenant.plan == TenantPlan.ENTERPRISE

    def test_invalid_tenant_slug_raises(self):
        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            Tenant(company_name="Bad Slug", slug="Invalid Slug With Spaces!")

    def test_user_creation_and_validation(self):
        user = User(
            tenant_id="tenant_123",
            email="agent@acme.com",
            password_hash="somehash",
            full_name="Agent Smith",
            role=UserRole.SUPPORT_AGENT,
        )
        assert user.role == UserRole.SUPPORT_AGENT
        assert user.is_active is True

    def test_tenant_context_role_checking(self):
        admin_context = TenantContext(
            tenant_id="t1",
            user_id="u1",
            role=UserRole.TENANT_ADMIN,
            email="admin@t1.com",
        )
        assert admin_context.has_role(UserRole.TENANT_ADMIN) is True
        assert admin_context.has_role(UserRole.SUPPORT_AGENT) is False

        super_context = TenantContext(
            tenant_id="platform",
            user_id="root",
            role=UserRole.SUPERADMIN,
            email="root@platform.io",
        )
        # SuperAdmin bypasses all role checks
        assert super_context.has_role(UserRole.SUPPORT_AGENT) is True
        assert super_context.has_role(UserRole.AUDITOR) is True


class TestAuthUseCases:
    @pytest.fixture
    def memory_repo(self, tmp_path):
        sqlite_url = f"sqlite:///{tmp_path}/test_enterprise.db"
        return EnterpriseRepository(db_url=sqlite_url)

    def test_register_tenant_success(self, memory_repo):
        use_case = RegisterTenantUseCase(memory_repo)
        dto = RegisterTenantInputDTO(
            company_name="Globex Tech",
            slug="globex",
            admin_email="admin@globex.com",
            admin_password="SecretPassword123!",
            admin_full_name="Homer Simpson",
            plan=TenantPlan.ENTERPRISE,
        )
        response = use_case.execute(dto)

        assert response.tenant_id is not None
        assert response.role == UserRole.TENANT_ADMIN.value
        assert response.company_name == "Globex Tech"
        assert response.access_token is not None

        # Cannot register duplicate slug
        with pytest.raises(ValueError, match="already registered"):
            use_case.execute(dto)

    def test_authenticate_user_success_and_failures(self, memory_repo):
        reg_case = RegisterTenantUseCase(memory_repo)
        reg_case.execute(
            RegisterTenantInputDTO(
                company_name="Initech",
                slug="initech",
                admin_email="peter@initech.com",
                admin_password="TPSReportPassword1!",
                admin_full_name="Peter Gibbons",
            )
        )

        auth_case = AuthenticateUserUseCase(memory_repo)
        # Valid login
        auth_resp = auth_case.execute("initech", "peter@initech.com", "TPSReportPassword1!")
        assert auth_resp.access_token is not None
        assert auth_resp.email == "peter@initech.com"

        # Invalid password
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth_case.execute("initech", "peter@initech.com", "WrongPassword!")

        # Non-existent tenant
        with pytest.raises(ValueError, match="Invalid tenant"):
            auth_case.execute("non-existent-co", "peter@initech.com", "TPSReportPassword1!")
