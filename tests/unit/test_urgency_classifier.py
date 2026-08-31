"""
Unit Tests for Urgency Classifiers and Multi-Model Composite Routing
"""

import pytest

from src.application.dto.ticket_dto import TicketInputDTO
from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.domain.entities.category import TicketCategory, TicketUrgency
from src.infrastructure.models.baseline_classifier import BaselineTfidfClassifier
from src.infrastructure.models.urgency_classifier import BaselineUrgencyClassifier


@pytest.fixture
def fitted_models():
    # Category classifier
    cat_clf = BaselineTfidfClassifier()
    cat_clf.fit(
        [
            "Network switch down and router unreachable",
            "Payment credit card transaction failed",
            "Cannot access login credentials",
        ],
        ["Network", "Billing & Admin", "Access & Security"],
    )

    # Urgency classifier
    urg_clf = BaselineUrgencyClassifier()
    urg_clf.fit(
        [
            "System is down immediately all users blocked",
            "Minor typo on dashboard",
            "Cannot access login credentials",
        ],
        ["Critical", "Low", "High"],
    )

    return cat_clf, urg_clf


def test_baseline_urgency_classifier_prediction(fitted_models):
    _, urg_clf = fitted_models
    assert urg_clf.is_fitted is True

    res = urg_clf.predict("System is down immediately all users blocked")
    assert isinstance(res.predicted_urgency, TicketUrgency)
    assert res.confidence >= 0.0
    assert "Critical" in res.probabilities
    assert res.latency_ms >= 0.0


def test_baseline_urgency_classifier_batch_prediction(fitted_models):
    _, urg_clf = fitted_models
    texts = [
        "System is down immediately",
        "Minor typo on dashboard",
    ]
    results = urg_clf.predict_batch(texts)
    assert len(results) == 2
    assert isinstance(results[0].predicted_urgency, TicketUrgency)
    assert isinstance(results[1].predicted_urgency, TicketUrgency)


def test_composite_multi_model_routing_use_case(fitted_models):
    cat_clf, urg_clf = fitted_models
    use_case = PredictTicketUseCase(
        classifier=cat_clf,
        urgency_classifier=urg_clf,
        router=RouteTicketUseCase(),
    )

    dto = TicketInputDTO(text="Network switch down and router unreachable")
    response = use_case.execute(dto)

    assert response.ticket_id is not None
    assert response.predicted_category in ["Network", "Other"]
    assert response.priority_level in [u.value for u in TicketUrgency]
    assert response.target_sla_hours > 0
    assert response.assigned_team in ["Network Operations Team", "Level 1 Support Triage", "Tier-1 Human Triage Queue"]
