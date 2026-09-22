"""
Unit Tests for SLA Policy Engine, Ticket Deadlines, and SLA Watchdog Worker.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.entities.tenant import (
    CustomerTier,
    EnterpriseTicket,
    TicketPriority,
    TicketStatus,
)
from src.domain.services.sla_policy_engine import SLAPolicyEngine
from src.infrastructure.database.enterprise_repository import EnterpriseRepository
from src.infrastructure.workers.sla_watchdog_worker import SLAWatchdogWorker


class TestSLAPolicyEngine:
    def test_sla_target_matrix_commitments(self):
        # VIP Enterprise commitments
        resp, resol = SLAPolicyEngine.get_sla_targets(CustomerTier.VIP_ENTERPRISE, TicketPriority.P1_CRITICAL)
        assert resp == 30    # 30 mins response
        assert resol == 120  # 2 hours resolution

        # Business Tier commitments
        resp, resol = SLAPolicyEngine.get_sla_targets(CustomerTier.BUSINESS, TicketPriority.P2_HIGH)
        assert resp == 120   # 2 hours response
        assert resol == 480  # 8 hours resolution

        # Standard Tier commitments
        resp, resol = SLAPolicyEngine.get_sla_targets(CustomerTier.STANDARD, TicketPriority.P3_MEDIUM)
        assert resp == 960   # 16 hours response
        assert resol == 2880 # 48 hours resolution

        # Free Tier commitments
        resp, resol = SLAPolicyEngine.get_sla_targets(CustomerTier.FREE, TicketPriority.P4_LOW)
        assert resp == 2880  # 48 hours response
        assert resol == 5760 # 96 hours resolution

    def test_compute_deadlines(self):
        now = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)
        resp_dl, resol_dl = SLAPolicyEngine.compute_deadlines(
            created_at=now,
            customer_tier=CustomerTier.VIP_ENTERPRISE,
            priority=TicketPriority.P1_CRITICAL,
        )
        assert resp_dl == now + timedelta(minutes=30)
        assert resol_dl == now + timedelta(hours=2)


class TestEnterpriseTicketSLAMethods:
    def test_sla_deadline_checks(self):
        now = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)
        ticket = EnterpriseTicket(
            tenant_id="t1",
            title="Database Outage",
            description="Production DB unreachable",
            customer_id="CUST-1",
            customer_tier=CustomerTier.VIP_ENTERPRISE,
            status=TicketStatus.OPEN,
            predicted_category="Database",
            confidence=0.95,
            probabilities={"Database": 0.95},
            assigned_team="Database Team",
            priority=TicketPriority.P1_CRITICAL,
            model_version="onnx-v0",
            latency_ms=8.5,
            created_at=now,
            sla_resolution_deadline=now + timedelta(hours=2), # 120 min duration
        )

        # 1. 30 minutes in (25% window) -> Not warning, not breached
        t_30m = now + timedelta(minutes=30)
        assert ticket.is_past_resolution_deadline(t_30m) is False
        assert ticket.is_past_warning_threshold(t_30m, threshold_pct=0.75) is False

        # 2. 95 minutes in (~79% window) -> Warning threshold crossed, but not breached
        t_95m = now + timedelta(minutes=95)
        assert ticket.is_past_resolution_deadline(t_95m) is False
        assert ticket.is_past_warning_threshold(t_95m, threshold_pct=0.75) is True

        # 3. 125 minutes in (104% window) -> Breached
        t_125m = now + timedelta(minutes=125)
        assert ticket.is_past_resolution_deadline(t_125m) is True

    def test_escalate_mutation(self):
        ticket = EnterpriseTicket(
            tenant_id="t1",
            description="Critical Auth Flaw",
            customer_id="CUST-1",
            predicted_category="Security",
            confidence=0.99,
            probabilities={"Security": 0.99},
            assigned_team="SecOps Tier 1",
            priority=TicketPriority.P1_CRITICAL,
            model_version="onnx-v0",
            latency_ms=7.2,
        )

        assert ticket.escalated is False
        ticket.escalate(reason="Executive intervention required", new_team="Tier-3 Senior Escalations")
        assert ticket.escalated is True
        assert ticket.escalation_reason == "Executive intervention required"
        assert ticket.assigned_team == "Tier-3 Senior Escalations"


class TestSLAWatchdogWorker:
    @pytest.fixture
    def test_repo(self, tmp_path):
        db_url = f"sqlite:///{tmp_path}/test_sla_watchdog.db"
        return EnterpriseRepository(db_url=db_url)

    def test_watchdog_warning_and_escalation_flow(self, test_repo):
        now = datetime(2026, 9, 22, 10, 0, 0, tzinfo=timezone.utc)

        # Ticket 1: Safe ticket (deadline in 10 hours)
        t_safe = EnterpriseTicket(
            tenant_id="t1",
            description="General inquiry",
            customer_id="C1",
            predicted_category="General",
            confidence=0.9,
            probabilities={"General": 0.9},
            assigned_team="Support Tier 1",
            priority=TicketPriority.P4_LOW,
            model_version="onnx-v0",
            latency_ms=8.0,
            created_at=now,
            sla_resolution_deadline=now + timedelta(hours=10),
        )
        test_repo.save(t_safe)

        # Ticket 2: Approaching deadline (80% window passed)
        t_warning = EnterpriseTicket(
            tenant_id="t1",
            description="Billing error on invoice",
            customer_id="C2",
            predicted_category="Billing",
            confidence=0.9,
            probabilities={"Billing": 0.9},
            assigned_team="Billing Team",
            priority=TicketPriority.P3_MEDIUM,
            model_version="onnx-v0",
            latency_ms=8.0,
            created_at=now,
            sla_resolution_deadline=now + timedelta(hours=1), # 60 min total
        )
        test_repo.save(t_warning)

        # Ticket 3: Already breached
        t_breached = EnterpriseTicket(
            tenant_id="t1",
            description="Server on fire",
            customer_id="C3",
            predicted_category="Infrastructure",
            confidence=0.98,
            probabilities={"Infrastructure": 0.98},
            assigned_team="Infra Team",
            priority=TicketPriority.P1_CRITICAL,
            model_version="onnx-v0",
            latency_ms=8.0,
            created_at=now,
            sla_resolution_deadline=now + timedelta(minutes=30), # 30 min total
        )
        test_repo.save(t_breached)

        # Evaluate at now + 50 minutes:
        # t_safe (50m of 600m = 8%) -> OK
        # t_warning (50m of 60m = 83%) -> Warning threshold crossed (>=75%)
        # t_breached (50m of 30m = 166%) -> Breached & Escalated
        eval_time = now + timedelta(minutes=50)
        worker = SLAWatchdogWorker(repository=test_repo, warning_threshold_pct=0.75)
        report = worker.evaluate_open_tickets(now=eval_time)

        assert report.scanned_count == 3
        assert report.warnings_emitted == 1
        assert report.breached_and_escalated == 1

        # Verify t_warning in repository
        updated_warning = test_repo.get_ticket_by_id("t1", t_warning.ticket_id)
        assert updated_warning.sla_warning_emitted is True
        assert updated_warning.status == TicketStatus.OPEN

        # Verify t_breached in repository
        updated_breached = test_repo.get_ticket_by_id("t1", t_breached.ticket_id)
        assert updated_breached.status == TicketStatus.BREACHED
        assert updated_breached.escalated is True
        assert updated_breached.assigned_team == "Tier-3 Senior Escalations"
        assert "SLA resolution deadline breached" in updated_breached.escalation_reason
