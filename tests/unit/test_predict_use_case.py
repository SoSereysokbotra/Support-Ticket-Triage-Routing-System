import pytest

from src.application.dto.ticket_dto import TicketInputDTO
from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.domain.entities.category import TicketCategory
from tests.conftest import MockTicketClassifier


def test_predict_ticket_use_case_high_confidence():
    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.HARDWARE,
        confidence=0.95,
        model_version="mock-test-v1",
    )
    use_case = PredictTicketUseCase(classifier=mock_clf)

    input_dto = TicketInputDTO(
        text="The printer on 2nd floor is smoking and jammed with paper.",
        title="Printer smoking",
        customer_id="CUST-42",
        urgency_hint="High",
    )

    response = use_case.execute(input_dto)

    assert response.predicted_category == "Hardware"
    assert response.confidence == 0.95
    assert response.assigned_team == "Hardware Support Tier-2"
    assert response.priority_level == "High"
    assert response.target_sla_hours == 4
    assert response.auto_routed is True
    assert response.model_version == "mock-test-v1"


def test_predict_ticket_use_case_low_confidence_fallback():
    # Low confidence (below 0.65 threshold)
    mock_clf = MockTicketClassifier(
        predicted_category=TicketCategory.SOFTWARE,
        confidence=0.45,
    )
    use_case = PredictTicketUseCase(classifier=mock_clf)

    input_dto = TicketInputDTO(
        text="Something is wrong with my computer today.",
        urgency_hint="Low",
    )

    response = use_case.execute(input_dto)

    assert response.predicted_category == "Software"
    assert response.confidence == 0.45
    assert response.assigned_team == "Tier-1 Human Triage Queue"
    assert response.auto_routed is False
    assert "below routing threshold" in response.routing_reason
