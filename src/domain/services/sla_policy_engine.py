"""
Domain Service for Enterprise SLA Policy Calculations.
Computes response and resolution deadlines based on Customer Tier and Priority.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Tuple

from src.domain.entities.tenant import CustomerTier, TicketPriority

# Matrix: (CustomerTier, TicketPriority) -> (response_minutes, resolution_minutes)
SLA_TARGET_MATRIX: Dict[Tuple[CustomerTier, TicketPriority], Tuple[int, int]] = {
    # VIP Enterprise Tier
    (CustomerTier.VIP_ENTERPRISE, TicketPriority.P1_CRITICAL): (30, 120),       # 30m response, 2h resolution
    (CustomerTier.VIP_ENTERPRISE, TicketPriority.P2_HIGH): (60, 240),          # 1h response, 4h resolution
    (CustomerTier.VIP_ENTERPRISE, TicketPriority.P3_MEDIUM): (240, 720),       # 4h response, 12h resolution
    (CustomerTier.VIP_ENTERPRISE, TicketPriority.P4_LOW): (480, 1440),         # 8h response, 24h resolution

    # Business Tier
    (CustomerTier.BUSINESS, TicketPriority.P1_CRITICAL): (60, 240),            # 1h response, 4h resolution
    (CustomerTier.BUSINESS, TicketPriority.P2_HIGH): (120, 480),               # 2h response, 8h resolution
    (CustomerTier.BUSINESS, TicketPriority.P3_MEDIUM): (360, 1440),            # 6h response, 24h resolution
    (CustomerTier.BUSINESS, TicketPriority.P4_LOW): (720, 2880),               # 12h response, 48h resolution

    # Standard Tier
    (CustomerTier.STANDARD, TicketPriority.P1_CRITICAL): (240, 720),           # 4h response, 12h resolution
    (CustomerTier.STANDARD, TicketPriority.P2_HIGH): (480, 1440),              # 8h response, 24h resolution
    (CustomerTier.STANDARD, TicketPriority.P3_MEDIUM): (960, 2880),            # 16h response, 48h resolution
    (CustomerTier.STANDARD, TicketPriority.P4_LOW): (1440, 4320),              # 24h response, 72h resolution

    # Free Tier
    (CustomerTier.FREE, TicketPriority.P1_CRITICAL): (480, 1440),              # 8h response, 24h resolution
    (CustomerTier.FREE, TicketPriority.P2_HIGH): (960, 2880),                  # 16h response, 48h resolution
    (CustomerTier.FREE, TicketPriority.P3_MEDIUM): (1440, 4320),               # 24h response, 72h resolution
    (CustomerTier.FREE, TicketPriority.P4_LOW): (2880, 5760),                  # 48h response, 96h resolution
}


class SLAPolicyEngine:
    """Pure domain service computing deterministic SLA contractual commitments."""

    @staticmethod
    def get_sla_targets(
        customer_tier: CustomerTier,
        priority: TicketPriority,
    ) -> Tuple[int, int]:
        """
        Returns (response_minutes, resolution_minutes) for the given tier and priority.
        Defaults to Standard P3_MEDIUM if unmapped.
        """
        key = (customer_tier, priority)
        return SLA_TARGET_MATRIX.get(key, (960, 2880))

    @classmethod
    def compute_deadlines(
        cls,
        created_at: datetime,
        customer_tier: CustomerTier,
        priority: TicketPriority,
    ) -> Tuple[datetime, datetime]:
        """
        Computes the exact UTC (response_deadline, resolution_deadline) from created_at.
        """
        response_mins, resolution_mins = cls.get_sla_targets(customer_tier, priority)
        response_deadline = created_at + timedelta(minutes=response_mins)
        resolution_deadline = created_at + timedelta(minutes=resolution_mins)
        return response_deadline, resolution_deadline
