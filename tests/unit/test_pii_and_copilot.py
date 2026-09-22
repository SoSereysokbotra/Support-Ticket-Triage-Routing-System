"""
Unit Tests for PII Sanitization, SOP Knowledge Retriever, and Copilot Draft Synthesizer.
"""

from datetime import datetime, timezone

import pytest

from src.domain.entities.category import TicketCategory
from src.domain.entities.feedback import AgentFeedbackAnnotation
from src.domain.entities.tenant import EnterpriseTicket, TicketPriority, TicketStatus
from src.domain.services.copilot_service import CopilotService
from src.domain.services.pii_sanitizer import PIISanitizer
from src.infrastructure.knowledge.knowledge_retriever import (
    DEFAULT_SOP_DATABASE,
    KnowledgeRetriever,
    SOPArticle,
)

# ==============================================================================
# 1. PII Sanitizer Tests
# ==============================================================================

def test_pii_sanitizer_credit_card_masking():
    raw_text = "Customer card number is 4532-1234-5678-9012 and backup is 4532 1234 5678 9012."
    sanitized, counts = PIISanitizer.sanitize(raw_text)
    assert "[REDACTED_CARD]" in sanitized
    assert "4532-1234-5678-9012" not in sanitized
    assert "4532 1234 5678 9012" not in sanitized
    assert counts.get("CREDIT_CARD") == 2


def test_pii_sanitizer_ssn_masking():
    raw_text = "Employee SSN is 123-45-6789 for tax records."
    sanitized, counts = PIISanitizer.sanitize(raw_text)
    assert "[REDACTED_SSN]" in sanitized
    assert "123-45-6789" not in sanitized
    assert counts.get("SSN") == 1


def test_pii_sanitizer_api_key_masking():
    raw_text = "Failing with token sk-abc1234567890def1234567890 and ghp_secretpat1234567890abcde."
    sanitized, counts = PIISanitizer.sanitize(raw_text)
    assert "[REDACTED_API_KEY]" in sanitized
    assert "sk-abc1234567890def1234567890" not in sanitized
    assert "ghp_secretpat1234567890abcde" not in sanitized
    assert counts.get("API_KEY") == 2


def test_pii_sanitizer_email_and_phone_masking():
    raw_text = "Please reach out to support@enterprise.corp or call +1 (555) 123-4567."
    sanitized, counts = PIISanitizer.sanitize(raw_text)
    assert "[REDACTED_EMAIL]" in sanitized
    assert "support@enterprise.corp" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "(555) 123-4567" not in sanitized
    assert counts.get("EMAIL") == 1
    assert counts.get("PHONE") == 1


def test_pii_sanitizer_clean_text():
    raw_text = "The server CPU usage is running at 98% in us-east cluster."
    sanitized, counts = PIISanitizer.sanitize(raw_text)
    assert sanitized == raw_text
    assert counts == {}
    assert not PIISanitizer.contains_pii(raw_text)


def test_pii_sanitizer_contains_pii_detection():
    assert PIISanitizer.contains_pii("Contact: admin@corp.io") is True
    assert PIISanitizer.contains_pii("Card: 1111-2222-3333-4444") is True
    assert PIISanitizer.contains_pii("No PII here in this message.") is False
    assert PIISanitizer.contains_pii("") is False


# ==============================================================================
# 2. SOP Knowledge Retriever Tests
# ==============================================================================

def test_knowledge_retriever_default_playbooks():
    retriever = KnowledgeRetriever()
    assert len(retriever.articles) == len(DEFAULT_SOP_DATABASE)
    assert len(retriever.articles) >= 9


def test_knowledge_retriever_category_match():
    retriever = KnowledgeRetriever()
    sops = retriever.find_relevant_sops(query="vpn gateway disconnection", category="Network", limit=2)
    assert len(sops) > 0
    assert any("VPN" in s.title or "Network" == s.category for s in sops)
    assert sops[0].article_id.startswith("SOP-NET")


def test_knowledge_retriever_keyword_relevance():
    retriever = KnowledgeRetriever()
    sops = retriever.find_relevant_sops(query="phishing malware attachment", category="Security", limit=1)
    assert len(sops) == 1
    assert "Security" in sops[0].category or "Phishing" in sops[0].title


def test_knowledge_retriever_fallback():
    retriever = KnowledgeRetriever()
    # Query with non-existent category and query returns empty list
    sops = retriever.find_relevant_sops(query="xylophone purple unicorn", category="UnheardCategory", limit=2)
    assert sops == []


# ==============================================================================
# 3. Copilot Service Tests
# ==============================================================================

def test_copilot_service_confidence_gate_skip():
    # Ticket confidence below 0.60 safety floor
    ticket = EnterpriseTicket(
        ticket_id="tick-low-conf-1",
        tenant_id="tenant-123",
        title="Flapping tunnel",
        description="Tunnel goes up and down",
        customer_id="cust-1",
        predicted_category="Network",
        confidence=0.45,  # Below 0.60
        probabilities={"Network": 0.45, "Hardware": 0.35},
        assigned_team="Network Ops",
        latency_ms=12.4,
        model_version="v1.0",
        priority=TicketPriority.P3_MEDIUM,
        status=TicketStatus.OPEN,
    )
    retriever = KnowledgeRetriever()
    sops = retriever.find_relevant_sops(query=ticket.description, category=ticket.predicted_category)

    result = CopilotService.generate_draft(
        ticket=ticket,
        sanitized_description=ticket.description,
        retrieved_sops=sops,
    )

    assert result.is_skipped is True
    assert result.suggested_response is None
    assert result.confidence == 0.0
    assert "below the safety threshold" in result.skip_reason


def test_copilot_service_successful_draft_generation():
    # Ticket confidence >= 0.60
    ticket = EnterpriseTicket(
        ticket_id="tick-high-conf-1",
        tenant_id="tenant-123",
        title="VPN Connection Failure",
        description="GlobalProtect dropped connection during remote shift",
        customer_id="alice@corp.com",
        predicted_category="Network",
        confidence=0.92,
        probabilities={"Network": 0.92, "Software": 0.05},
        assigned_team="Network Ops",
        latency_ms=15.2,
        model_version="v1.0",
        priority=TicketPriority.P2_HIGH,
        status=TicketStatus.OPEN,
    )
    retriever = KnowledgeRetriever()
    sops = retriever.find_relevant_sops(query=ticket.description, category=ticket.predicted_category)

    result = CopilotService.generate_draft(
        ticket=ticket,
        sanitized_description=ticket.description,
        retrieved_sops=sops,
    )

    assert result.is_skipped is False
    assert result.suggested_response is not None
    assert "Hello alice@corp.com" in result.suggested_response
    assert "Network" in result.suggested_response
    assert "Grounded in Standard Operating Procedure" in result.suggested_response
    assert result.confidence > 0.80
    assert len(result.sources) > 0


def test_copilot_service_draft_without_sops():
    ticket = EnterpriseTicket(
        ticket_id="tick-no-sop-1",
        tenant_id="tenant-123",
        title="Custom Internal Tool Glitch",
        description="Internal portal widget is blank",
        customer_id="bob@corp.com",
        predicted_category="Software",
        confidence=0.75,
        probabilities={"Software": 0.75, "Database": 0.20},
        assigned_team="Application Engineering",
        latency_ms=18.0,
        model_version="v1.0",
        priority=TicketPriority.P4_LOW,
        status=TicketStatus.OPEN,
    )
    result = CopilotService.generate_draft(
        ticket=ticket,
        sanitized_description=ticket.description,
        retrieved_sops=[],
    )

    assert result.is_skipped is False
    assert result.suggested_response is not None
    assert "General Enterprise Technical Support Playbook" in result.suggested_response
    assert result.confidence == round(0.75 * 0.70, 4)


# ==============================================================================
# 4. Agent Feedback Annotation Domain Tests
# ==============================================================================

def test_feedback_annotation_high_confidence_error():
    # Category changed AND model had >= 0.85 confidence
    ann = AgentFeedbackAnnotation(
        tenant_id="tenant-1",
        ticket_id="tick-1",
        agent_id="agent-1",
        original_category="Network",
        corrected_category="Security",
        original_priority="MEDIUM",
        corrected_priority="HIGH",
        model_version="v2.1",
        original_confidence=0.88,
        reclassification_reason="Suspicious port scan identified",
    )

    assert ann.is_high_confidence_error is True
    assert ann.sample_weight == 3.0
    data = ann.to_dict()
    assert data["is_high_confidence_error"] is True
    assert data["sample_weight"] == 3.0


def test_feedback_annotation_low_confidence_error():
    # Category changed BUT model had < 0.85 confidence
    ann = AgentFeedbackAnnotation(
        tenant_id="tenant-1",
        ticket_id="tick-2",
        agent_id="agent-1",
        original_category="Network",
        corrected_category="Hardware",
        original_priority="LOW",
        corrected_priority="LOW",
        model_version="v2.1",
        original_confidence=0.62,
    )

    assert ann.is_high_confidence_error is False
    assert ann.sample_weight == 1.0


def test_feedback_annotation_priority_only_correction():
    # Category unchanged, only priority corrected
    ann = AgentFeedbackAnnotation(
        tenant_id="tenant-1",
        ticket_id="tick-3",
        agent_id="agent-1",
        original_category="Billing",
        corrected_category="Billing",
        original_priority="LOW",
        corrected_priority="CRITICAL",
        model_version="v2.1",
        original_confidence=0.95,
    )

    assert ann.is_high_confidence_error is False
    assert ann.sample_weight == 1.0
