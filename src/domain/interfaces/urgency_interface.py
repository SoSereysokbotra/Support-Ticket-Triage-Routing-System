"""
Urgency Model Interface Port
"""

from abc import ABC, abstractmethod
from typing import List

from src.domain.value_objects.urgency_result import UrgencyPredictionResult


class IUrgencyClassifier(ABC):
    """Abstract interface for ticket urgency classification models."""

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Returns the semantic version / tag of the active model."""
        pass

    @abstractmethod
    def predict(self, text: str) -> UrgencyPredictionResult:
        """Infers urgency level for a single ticket body."""
        pass

    @abstractmethod
    def predict_batch(self, texts: List[str]) -> List[UrgencyPredictionResult]:
        """Performs batched inference for a list of ticket bodies."""
        pass
