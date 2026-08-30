from abc import ABC, abstractmethod
from typing import List

from src.domain.value_objects.prediction_result import PredictionResult


class ITicketClassifier(ABC):
    """
    Abstract Port (Interface) for all Ticket Classifier models.
    Infrastructure adapters (DistilBERT, TF-IDF, BentoML) must implement this.
    Domain and Application layers depend ONLY on this abstraction.
    """

    @abstractmethod
    def predict(self, text: str) -> PredictionResult:
        """Classify a single ticket text."""
        pass

    @abstractmethod
    def predict_batch(self, texts: List[str]) -> List[PredictionResult]:
        """Classify a batch of ticket texts."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Returns the version or identifier of the underlying model."""
        pass
