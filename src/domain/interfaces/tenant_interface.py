"""
Domain Interfaces for Multi-Tenant Data Repositories and User Management.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.tenant import EnterpriseTicket, Tenant, User


class ITenantRepository(ABC):
    """Port interface for Tenant organization persistence."""

    @abstractmethod
    def create_tenant(self, tenant: Tenant) -> Tenant:
        """Persists a new tenant organization."""
        pass

    @abstractmethod
    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieves a tenant by primary identifier."""
        pass

    @abstractmethod
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Retrieves a tenant by slug."""
        pass

    @abstractmethod
    def list_all_tenants(self) -> List[Tenant]:
        """Lists all registered tenants (SuperAdmin only)."""
        pass


class IUserRepository(ABC):
    """Port interface for User and RBAC membership persistence."""

    @abstractmethod
    def create_user(self, user: User) -> User:
        """Persists a new user within a tenant."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user by unique identifier."""
        pass

    @abstractmethod
    def get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Retrieves a user by tenant-scoped email address."""
        pass

    @abstractmethod
    def list_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Lists all users belonging to a specific tenant."""
        pass


class IEnterpriseTicketRepository(ABC):
    """Port interface for Tenant-isolated Ticket storage."""

    @abstractmethod
    def save_ticket(self, ticket: EnterpriseTicket) -> EnterpriseTicket:
        """Persists an enterprise ticket."""
        pass

    @abstractmethod
    def get_ticket_by_id(self, tenant_id: str, ticket_id: str) -> Optional[EnterpriseTicket]:
        """Retrieves a ticket within a specific tenant boundary."""
        pass

    @abstractmethod
    def list_tickets_by_tenant(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EnterpriseTicket]:
        """Lists tickets strictly scoped to the specified tenant."""
        pass
