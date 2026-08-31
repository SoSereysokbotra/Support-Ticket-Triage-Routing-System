from typing import Optional

from src.application.dto.ticket_dto import TicketInputDTO, TriageResponseDTO
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.domain.entities.category import TicketUrgency
from src.domain.entities.ticket import Ticket
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.interfaces.urgency_interface import IUrgencyClassifier
from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter


class PredictTicketUseCase:
    """
    Main use-case orchestrator for multi-model ticket classification and routing.
    Coordinates domain invariants, Category model port, Urgency model port,
    Feast online feature store, and composite routing rules.
    """

    def __init__(
        self,
        classifier: ITicketClassifier,
        urgency_classifier: Optional[IUrgencyClassifier] = None,
        router: Optional[RouteTicketUseCase] = None,
        feature_store: Optional[FeastFeatureStoreAdapter] = None,
    ) -> None:
        self._classifier = classifier
        self._urgency_classifier = urgency_classifier
        self._router = router or RouteTicketUseCase()
        self._feature_store = feature_store

    def execute(self, input_dto: TicketInputDTO) -> TriageResponseDTO:
        # Determine urgency: explicit hint takes priority; otherwise infer via urgency model
        urgency = None
        if input_dto.urgency_hint:
            urgency = TicketUrgency.from_str(input_dto.urgency_hint)
        elif self._urgency_classifier:
            try:
                urg_res = self._urgency_classifier.predict(input_dto.text)
                urgency = urg_res.predicted_urgency
            except Exception:
                urgency = TicketUrgency.MEDIUM

        ticket_kwargs = {
            "body": input_dto.text,
            "title": input_dto.title,
            "customer_id": input_dto.customer_id,
            "actual_urgency": urgency,
        }
        if input_dto.ticket_id:
            ticket_kwargs["id"] = input_dto.ticket_id

        ticket = Ticket(**ticket_kwargs)

        # 1. Fetch real-time online features from Feast if available
        customer_features = None
        if self._feature_store and ticket.customer_id:
            try:
                customer_features = self._feature_store.get_customer_feature(ticket.customer_id)
            except Exception:
                # Resilient fallback if store is temporarily unavailable
                pass

        # 2. Run Category Model inference
        prediction = self._classifier.predict(ticket.full_text)

        # 3. Compute routing decision factoring in category prediction + urgency + customer features
        routing = self._router.execute(
            ticket,
            prediction,
            urgency_override=urgency,
            customer_features=customer_features,
        )

        return TriageResponseDTO(
            ticket_id=ticket.id,
            predicted_category=prediction.predicted_category.value,
            confidence=prediction.confidence,
            probabilities=prediction.probabilities,
            assigned_team=routing.assigned_team,
            priority_level=routing.priority_level.value,
            target_sla_hours=routing.target_sla_hours,
            auto_routed=routing.auto_routed,
            routing_reason=routing.routing_reason,
            model_version=prediction.model_version,
            latency_ms=prediction.latency_ms,
            customer_features=customer_features,
        )
