"""
Application Use Cases for Generative Copilot Draft Synthesis & 1-Click Resolution.
"""

from __future__ import annotations

from typing import Optional

from src.domain.entities.event import EnterpriseEvent, EnterpriseEventType
from src.domain.entities.tenant import EnterpriseTicket, TenantContext
from src.domain.interfaces.event_bus_interface import IEventBus
from src.domain.services.copilot_service import CopilotDraftResult, CopilotService
from src.domain.services.pii_sanitizer import PIISanitizer
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.knowledge.knowledge_retriever import KnowledgeRetriever


class GenerateCopilotDraftUseCase:
    """
    Executes safety sanitization, SOP knowledge retrieval, and Copilot draft synthesis.
    Stores the drafted resolution on the ticket for support agent 1-click review.
    """

    def __init__(
        self,
        repository: EnterpriseRepository,
        knowledge_retriever: Optional[KnowledgeRetriever] = None,
    ) -> None:
        self.repository = repository
        self.knowledge_retriever = knowledge_retriever or KnowledgeRetriever()

    def execute(self, context: TenantContext, ticket_id: str) -> tuple[EnterpriseTicket, CopilotDraftResult]:
        # 1. Fetch ticket within tenant boundary
        ticket = self.repository.get_by_id_tenant(
            tenant_id=context.tenant_id, ticket_id=ticket_id
        )
        if not ticket:
            raise ValueError(f"Ticket '{ticket_id}' not found in current tenant.")

        # 2. Execute PII Masking
        sanitized_description, _ = PIISanitizer.sanitize(ticket.description)
        query = f"{ticket.title or ''} {sanitized_description}".strip()

        # 3. Retrieve Grounded SOP Playbooks
        sops = self.knowledge_retriever.find_relevant_sops(
            query=query, category=ticket.predicted_category, top_k=2
        )

        # 4. Synthesize Grounded Copilot Draft
        draft_result = CopilotService.generate_draft(
            ticket=ticket,
            sanitized_description=sanitized_description,
            retrieved_sops=sops,
        )

        # 5. Persist Draft onto Ticket if generated
        if draft_result.suggested_response:
            self.repository.update_ticket_copilot_draft(
                ticket_id=ticket.ticket_id,
                tenant_id=ticket.tenant_id,
                draft=draft_result.suggested_response,
                confidence=draft_result.confidence,
                sources=draft_result.sources,
            )

        # Refetch refreshed ticket
        updated_ticket = self.repository.get_by_id_tenant(
            tenant_id=context.tenant_id, ticket_id=ticket_id
        )
        return updated_ticket, draft_result


class ApproveCopilotDraftUseCase:
    """
    1-Click Agent Approval: marks ticket as RESOLVED and records resolution timestamp.
    Dispatches TICKET_RESOLVED event across the enterprise event bus.
    """

    def __init__(
        self,
        repository: EnterpriseRepository,
        event_bus: Optional[IEventBus] = None,
    ) -> None:
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, context: TenantContext, ticket_id: str) -> EnterpriseTicket:
        resolved_ticket = self.repository.resolve_ticket(
            ticket_id=ticket_id, tenant_id=context.tenant_id
        )

        if self.event_bus:
            event = EnterpriseEvent(
                event_type=EnterpriseEventType.TICKET_RESOLVED,
                tenant_id=context.tenant_id,
                ticket_id=ticket_id,
                payload={
                    "status": resolved_ticket.status.value,
                    "resolved_at": (
                        resolved_ticket.resolved_at.isoformat()
                        if resolved_ticket.resolved_at
                        else None
                    ),
                    "resolver_user_id": context.user_id,
                },
            )
            self.event_bus.publish(event)

        return resolved_ticket
