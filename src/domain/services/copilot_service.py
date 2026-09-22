"""
Enterprise Agent Copilot Service (RAG Resolution Draft Synthesizer).
Grounded in Standard Operating Procedures with deterministic fallback gating.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.domain.entities.tenant import EnterpriseTicket
from src.infrastructure.knowledge.knowledge_retriever import SOPArticle


@dataclass(frozen=True)
class CopilotDraftResult:
    """Generated Copilot draft response with confidence telemetry and source citations."""
    suggested_response: Optional[str]
    confidence: float
    sources: List[str]
    is_skipped: bool = False
    skip_reason: Optional[str] = None


class CopilotService:
    """
    Synthesizes AI Copilot draft responses grounded in verified SOP knowledge.
    Enforces a strict confidence floor (< 0.60) to prevent ungrounded hallucinations.
    """

    CONFIDENCE_GATE_FLOOR = 0.60

    @classmethod
    def generate_draft(
        cls,
        ticket: EnterpriseTicket,
        sanitized_description: str,
        retrieved_sops: List[SOPArticle],
    ) -> CopilotDraftResult:
        """
        Generates a contextual, grounded resolution draft for support agents.
        Returns a fallback result if confidence is below the safety threshold.
        """
        # 1. Deterministic Fallback Gate
        if ticket.confidence < cls.CONFIDENCE_GATE_FLOOR:
            return CopilotDraftResult(
                suggested_response=None,
                confidence=0.0,
                sources=[],
                is_skipped=True,
                skip_reason=(
                    f"Model confidence ({ticket.confidence:.2%}) is below the "
                    f"safety threshold ({cls.CONFIDENCE_GATE_FLOOR:.0%}). "
                    "Skipping automated generation to prevent hallucinations."
                ),
            )

        # 2. Select primary SOP playbook
        primary_sop = retrieved_sops[0] if retrieved_sops else None
        sources = [f"{sop.article_id}: {sop.title}" for sop in retrieved_sops]

        # 3. Assemble Grounded Markdown Resolution
        customer_ref = ticket.customer_id or "Valued Customer"
        steps_markdown = ""
        if primary_sop:
            steps_markdown = "\n".join(
                f"{i+1}. **Step {i+1}:** {step}"
                for i, step in enumerate(primary_sop.resolution_steps)
            )
        else:
            steps_markdown = (
                "1. **Step 1:** Review system configuration and network status.\n"
                "2. **Step 2:** Ensure local client application is up to date.\n"
                "3. **Step 3:** Contact your designated system administrator if issue persists."
            )

        title_header = f" Regarding: {ticket.title}" if ticket.title else ""
        sop_citation = (
            f"> *Grounded in Standard Operating Procedure: [{primary_sop.article_id}] {primary_sop.title}*"
            if primary_sop
            else "> *General Enterprise Technical Support Playbook*"
        )

        response_body = f"""Hello {customer_ref},

Thank you for contacting enterprise support{title_header}. Our triage diagnostics categorized this issue under **{ticket.predicted_category}** (Priority: **{ticket.priority.value}**).

Based on our standard technical procedures, please execute the following troubleshooting steps:

{sop_citation}

{steps_markdown}

If the issue continues after completing these steps, please reply directly to this ticket with any error codes or screenshots. Our engineering team is standing by.

Best regards,
**Enterprise Technical Operations & Support Team**"""

        # Groundedness confidence: combination of triage confidence and SOP availability
        copilot_confidence = (
            round(ticket.confidence * 0.95, 4) if primary_sop else round(ticket.confidence * 0.70, 4)
        )

        return CopilotDraftResult(
            suggested_response=response_body,
            confidence=copilot_confidence,
            sources=sources,
            is_skipped=False,
        )
