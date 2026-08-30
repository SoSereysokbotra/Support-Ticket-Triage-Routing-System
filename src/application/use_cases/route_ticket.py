from src.domain.entities.category import TicketCategory, TicketUrgency
from src.domain.entities.ticket import Ticket
from src.domain.value_objects.prediction_result import PredictionResult
from src.domain.value_objects.routing_decision import RoutingDecision


class RouteTicketUseCase:
    """
    Application use case for determining team routing, priority, and SLA
    based on predicted category, confidence, and ticket metadata.
    """

    CONFIDENCE_THRESHOLD = 0.65  # Below this, route to Tier-1 Triage for manual review

    TEAM_MAPPING = {
        TicketCategory.HARDWARE: "Hardware Support Tier-2",
        TicketCategory.SOFTWARE: "Software Application Support",
        TicketCategory.NETWORK: "Network Operations Center (NOC)",
        TicketCategory.ACCESS_SECURITY: "Identity & Access Management (IAM)",
        TicketCategory.BILLING_ADMIN: "Billing & Accounts Operations",
        TicketCategory.OTHER: "General Customer Support",
    }

    SLA_HOURS = {
        TicketUrgency.CRITICAL: 1,
        TicketUrgency.HIGH: 4,
        TicketUrgency.MEDIUM: 12,
        TicketUrgency.LOW: 24,
    }

    def execute(
        self,
        ticket: Ticket,
        prediction: PredictionResult,
        urgency_override: TicketUrgency | None = None,
        customer_features: dict | None = None,
    ) -> RoutingDecision:
        features = customer_features or {}
        is_vip = features.get("is_vip", False)
        customer_tier = features.get("customer_tier", 0)

        urgency = urgency_override or ticket.actual_urgency or TicketUrgency.MEDIUM

        # VIP/Enterprise priority escalation
        if is_vip and urgency in (TicketUrgency.LOW, TicketUrgency.MEDIUM):
            urgency = TicketUrgency.HIGH
        elif customer_tier == 2 and urgency == TicketUrgency.LOW:
            urgency = TicketUrgency.MEDIUM

        base_sla_hours = self.SLA_HOURS.get(urgency, 12)
        # Expedited SLA for VIP/Enterprise
        sla_hours = max(1, base_sla_hours // 2) if is_vip else base_sla_hours

        if prediction.confidence < self.CONFIDENCE_THRESHOLD:
            # Low confidence fallback: route to human triage first
            return RoutingDecision(
                ticket_id=ticket.id,
                assigned_team="Tier-1 Human Triage Queue",
                priority_level=urgency,
                target_sla_hours=sla_hours,
                category=prediction.predicted_category,
                confidence=prediction.confidence,
                auto_routed=False,
                routing_reason=(
                    f"Model confidence ({prediction.confidence:.2%}) is below routing "
                    f"threshold ({self.CONFIDENCE_THRESHOLD:.0%}). Assigned to human triage."
                    + (" (VIP Escalation applied)" if is_vip else "")
                ),
                fallback_applied=True,
            )

        assigned_team = self.TEAM_MAPPING.get(
            prediction.predicted_category, "General Customer Support"
        )
        return RoutingDecision(
            ticket_id=ticket.id,
            assigned_team=assigned_team,
            priority_level=urgency,
            target_sla_hours=sla_hours,
            category=prediction.predicted_category,
            confidence=prediction.confidence,
            auto_routed=True,
            routing_reason=(
                f"Auto-routed to {assigned_team} based on {prediction.predicted_category.value} "
                f"classification (confidence: {prediction.confidence:.2%})."
                + (" [VIP Customer — Expedited SLA]" if is_vip else "")
            ),
            fallback_applied=False,
        )
