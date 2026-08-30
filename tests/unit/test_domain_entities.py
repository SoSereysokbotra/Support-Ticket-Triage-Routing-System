import pytest

from src.domain.entities.category import TicketCategory, TicketUrgency
from src.domain.entities.ticket import Ticket
from src.domain.value_objects.prediction_result import PredictionResult
from src.domain.value_objects.routing_decision import RoutingDecision


def test_ticket_creation_and_validation():
    # Valid ticket
    ticket = Ticket(
        body="My laptop keyboard spacebar is stuck and unresponsive.",
        title="Broken spacebar",
        customer_id="CUST-1001",
    )
    assert ticket.id is not None
    assert ticket.title == "Broken spacebar"
    assert ticket.full_text == "Broken spacebar. My laptop keyboard spacebar is stuck and unresponsive."

    # Empty body should raise ValueError
    with pytest.raises(ValueError, match="Ticket body cannot be empty"):
        Ticket(body="")

    # Too short body should raise ValueError
    with pytest.raises(ValueError, match="at least 5 characters"):
        Ticket(body="help")


def test_category_and_urgency_enums():
    assert TicketCategory.from_str("hardware") == TicketCategory.HARDWARE
    assert TicketCategory.from_str("ACCESS & SECURITY") == TicketCategory.ACCESS_SECURITY
    assert TicketCategory.from_str("unknown_category") == TicketCategory.OTHER

    assert TicketUrgency.from_str("critical") == TicketUrgency.CRITICAL
    assert TicketUrgency.from_str("invalid") == TicketUrgency.MEDIUM


def test_prediction_result_invariants():
    # Valid prediction
    pred = PredictionResult(
        predicted_category=TicketCategory.SOFTWARE,
        confidence=0.88,
        probabilities={"Software": 0.88, "Hardware": 0.12},
    )
    assert pred.predicted_category == TicketCategory.SOFTWARE
    assert pred.confidence == 0.88

    # Out of bounds confidence
    with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
        PredictionResult(predicted_category=TicketCategory.SOFTWARE, confidence=1.5)

    # Negative latency
    with pytest.raises(ValueError, match="Latency cannot be negative"):
        PredictionResult(
            predicted_category=TicketCategory.SOFTWARE,
            confidence=0.9,
            latency_ms=-5.0,
        )
