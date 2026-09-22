"""
Asynchronous SLA Watchdog Worker Daemon.
Scans active open tickets, detects 75% SLA warning thresholds,
and automatically escalates breached tickets to Tier 3 Senior Escalations.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from src.domain.entities.tenant import TicketStatus
from src.infrastructure.database.enterprise_repository import EnterpriseRepository

logger = logging.getLogger("sla_watchdog")


@dataclass
class SLAScanReport:
    """Summary metrics emitted by an SLA evaluation pass."""
    scanned_count: int
    warnings_emitted: int
    breached_and_escalated: int
    evaluation_timestamp: str


class SLAWatchdogWorker:
    """
    Thread-safe background daemon monitoring SLA compliance across tenants.
    Emits warnings at 75% threshold and auto-escalates at 100% breach.
    """

    def __init__(
        self,
        repository: EnterpriseRepository,
        poll_interval_seconds: int = 30,
        warning_threshold_pct: float = 0.75,
    ) -> None:
        self.repository = repository
        self.poll_interval_seconds = poll_interval_seconds
        self.warning_threshold_pct = warning_threshold_pct
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def evaluate_open_tickets(self, now: Optional[datetime] = None) -> SLAScanReport:
        """
        Executes a single evaluation pass over all open tickets.
        Supports simulated time injection for testing and auditing.
        """
        current_time = now or datetime.now(timezone.utc)
        open_tickets = self.repository.get_open_tickets()

        scanned = len(open_tickets)
        warnings = 0
        breached = 0

        for ticket in open_tickets:
            # 1. Check for 100% SLA Resolution Breach
            if ticket.is_past_resolution_deadline(current_time):
                if ticket.status != TicketStatus.BREACHED:
                    ticket.status = TicketStatus.BREACHED
                    ticket.escalate(
                        reason="SLA resolution deadline breached - auto-escalated by SLA Watchdog.",
                        new_team="Tier-3 Senior Escalations",
                    )
                    self.repository.update_ticket_sla(ticket)
                    breached += 1
                    logger.warning(
                        f"[SLA Breach] Ticket {ticket.ticket_id} (Tenant: {ticket.tenant_id}) "
                        f"breached resolution deadline {ticket.sla_resolution_deadline}. Escalated to Tier 3."
                    )

            # 2. Check for 75% SLA Warning Threshold
            elif ticket.is_past_warning_threshold(current_time, threshold_pct=self.warning_threshold_pct):
                if not ticket.sla_warning_emitted:
                    ticket.sla_warning_emitted = True
                    self.repository.update_ticket_sla(ticket)
                    warnings += 1
                    logger.info(
                        f"[SLA Warning] Ticket {ticket.ticket_id} (Tenant: {ticket.tenant_id}) "
                        f"crossed {int(self.warning_threshold_pct * 100)}% SLA threshold."
                    )

        return SLAScanReport(
            scanned_count=scanned,
            warnings_emitted=warnings,
            breached_and_escalated=breached,
            evaluation_timestamp=current_time.isoformat(),
        )

    def _worker_loop(self) -> None:
        logger.info("[SLA Watchdog] Daemon loop started.")
        while not self._stop_event.is_set():
            try:
                self.evaluate_open_tickets()
            except Exception as e:
                logger.error(f"[SLA Watchdog] Error during evaluation cycle: {e}", exc_info=True)

            self._stop_event.wait(self.poll_interval_seconds)
        logger.info("[SLA Watchdog] Daemon loop stopped.")

    def start(self) -> None:
        """Starts the background worker thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="SLAWatchdogThread")
        self._thread.start()
        logger.info(f"[SLA Watchdog] Background worker running (interval: {self.poll_interval_seconds}s).")

    def stop(self) -> None:
        """Stops the background worker thread cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        logger.info("[SLA Watchdog] Background worker shut down.")
