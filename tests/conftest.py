import pytest

from src.domain.entities.category import TicketCategory, TicketUrgency
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.value_objects.prediction_result import PredictionResult


class MockTicketClassifier(ITicketClassifier):
    """
    In-memory test double for ITicketClassifier.
    Allows testing application and presentation layers with zero model overhead.
    """

    def __init__(
        self,
        predicted_category: TicketCategory = TicketCategory.HARDWARE,
        confidence: float = 0.92,
        model_version: str = "mock-v1",
    ) -> None:
        self._predicted_category = predicted_category
        self._confidence = confidence
        self._model_version = model_version

    @property
    def model_version(self) -> str:
        return self._model_version

    def predict(self, text: str) -> PredictionResult:
        probabilities = {
            cat.value: (self._confidence if cat == self._predicted_category else (1.0 - self._confidence) / 5)
            for cat in TicketCategory
        }
        return PredictionResult(
            predicted_category=self._predicted_category,
            confidence=self._confidence,
            probabilities=probabilities,
            model_version=self._model_version,
            latency_ms=1.5,
        )

    def predict_batch(self, texts: list[str]) -> list[PredictionResult]:
        return [self.predict(t) for t in texts]


@pytest.fixture
def mock_classifier() -> MockTicketClassifier:
    return MockTicketClassifier()


@pytest.fixture(scope="session", autouse=True)
def ensure_test_fixtures():
    """Ensure Feast feature store is bootstrapped on clean checkouts."""
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    parquet_path = project_root / "features" / "data" / "customer_features.parquet"
    db_path = project_root / "features" / "data" / "online_store.db"

    if not parquet_path.exists() or not db_path.exists():
        from src.infrastructure.features.feature_generator import bootstrap_feast_store

        bootstrap_feast_store()

