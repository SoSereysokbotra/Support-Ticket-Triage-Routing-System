from typing import List, Optional

from src.application.dto.ticket_dto import TicketInputDTO, TriageResponseDTO
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.domain.entities.category import TicketUrgency
from src.domain.entities.ticket import Ticket
from src.domain.interfaces.feature_store_interface import IFeatureStore
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.interfaces.urgency_interface import IUrgencyClassifier


class PredictTicketUseCase:
    """
    Main use-case orchestrator for multi-model ticket classification and routing.
    Coordinates domain invariants, Category model port, Urgency model port,
    Feature store port, and composite routing rules.
    """

    def __init__(
        self,
        classifier: ITicketClassifier,
        urgency_classifier: Optional[IUrgencyClassifier] = None,
        router: Optional[RouteTicketUseCase] = None,
        feature_store: Optional[IFeatureStore] = None,
    ) -> None:
        self._classifier = classifier
        self._urgency_classifier = urgency_classifier
        self._router = router or RouteTicketUseCase()
        self._feature_store = feature_store

    def _determine_urgency(self, hint: Optional[str], text: str) -> TicketUrgency:
        if hint:
            return TicketUrgency.from_str(hint)
        if self._urgency_classifier:
            try:
                urg_res = self._urgency_classifier.predict(text)
                return urg_res.predicted_urgency
            except Exception:
                return TicketUrgency.MEDIUM
        return TicketUrgency.MEDIUM

    def execute(self, input_dto: TicketInputDTO) -> TriageResponseDTO:
        urgency = self._determine_urgency(input_dto.urgency_hint, input_dto.text)

        ticket_kwargs = {
            "body": input_dto.text,
            "title": input_dto.title,
            "customer_id": input_dto.customer_id,
            "actual_urgency": urgency,
        }
        if input_dto.ticket_id:
            ticket_kwargs["id"] = input_dto.ticket_id

        ticket = Ticket(**ticket_kwargs)

        # 1. Fetch real-time online features from Feature Store if available
        customer_features = None
        if self._feature_store and ticket.customer_id:
            try:
                customer_features = self._feature_store.get_customer_feature(ticket.customer_id)
            except Exception:
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

    def batch_execute(self, input_dtos: List[TicketInputDTO]) -> List[TriageResponseDTO]:
        """
        True vectorized batch execution:
        1. Validates tickets and determines urgencies.
        2. Vectorizes feature store lookup for all customer IDs in a single call.
        3. Performs vectorized tensor inference on the model classifier in batch.
        4. Applies deterministic routing rules across the batch.
        """
        if not input_dtos:
            return []

        tickets: List[Ticket] = []
        urgencies: List[TicketUrgency] = []

        for dto in input_dtos:
            urgency = self._determine_urgency(dto.urgency_hint, dto.text)
            ticket_kwargs = {
                "body": dto.text,
                "title": dto.title,
                "customer_id": dto.customer_id,
                "actual_urgency": urgency,
            }
            if dto.ticket_id:
                ticket_kwargs["id"] = dto.ticket_id
            ticket = Ticket(**ticket_kwargs)
            tickets.append(ticket)
            urgencies.append(urgency)

        # 1. Vectorized online feature lookup for all customers in batch
        customer_ids = [t.customer_id for t in tickets if t.customer_id]
        customer_features_map = {}
        if self._feature_store and customer_ids:
            try:
                unique_cids = list(dict.fromkeys(customer_ids))
                features_list = self._feature_store.get_online_features(unique_cids)
                customer_features_map = dict(zip(unique_cids, features_list))
            except Exception:
                pass

        # 2. Vectorized batch prediction using ITicketClassifier.predict_batch()
        full_texts = [t.full_text for t in tickets]
        predictions = self._classifier.predict_batch(full_texts)

        # 3. Route each ticket and build response DTOs
        responses: List[TriageResponseDTO] = []
        for ticket, urgency, pred in zip(tickets, urgencies, predictions):
            c_features = customer_features_map.get(ticket.customer_id) if ticket.customer_id else None
            routing = self._router.execute(
                ticket,
                pred,
                urgency_override=urgency,
                customer_features=c_features,
            )
            responses.append(
                TriageResponseDTO(
                    ticket_id=ticket.id,
                    predicted_category=pred.predicted_category.value,
                    confidence=pred.confidence,
                    probabilities=pred.probabilities,
                    assigned_team=routing.assigned_team,
                    priority_level=routing.priority_level.value,
                    target_sla_hours=routing.target_sla_hours,
                    auto_routed=routing.auto_routed,
                    routing_reason=routing.routing_reason,
                    model_version=pred.model_version,
                    latency_ms=pred.latency_ms,
                    customer_features=c_features,
                )
            )

        return responses
