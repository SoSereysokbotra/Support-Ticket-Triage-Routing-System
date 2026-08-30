import time
from typing import Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.domain.entities.category import TicketCategory
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.value_objects.prediction_result import PredictionResult


class BaselineTfidfClassifier(ITicketClassifier):
    """
    TF-IDF + LogisticRegression baseline model implementing ITicketClassifier.
    Useful for fast baseline metrics comparison, unit tests, and fallback.
    """

    def __init__(self, model_version: str = "tfidf-baseline-v0") -> None:
        self._model_version = model_version
        self._pipeline: Optional[Pipeline] = None
        self._classes: List[str] = []

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_fitted(self) -> bool:
        return self._pipeline is not None

    def fit(self, texts: List[str], labels: List[str]) -> "BaselineTfidfClassifier":
        """Fits the TF-IDF and Logistic Regression pipeline."""
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=500, random_state=42)),
        ])
        self._pipeline.fit(texts, labels)
        self._classes = list(self._pipeline.classes_)
        return self

    def predict(self, text: str) -> PredictionResult:
        if not self.is_fitted:
            raise RuntimeError("Baseline classifier must be fitted before predict() is called.")

        start_time = time.perf_counter()
        proba_array = self._pipeline.predict_proba([text])[0]
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        top_idx = int(np.argmax(proba_array))
        predicted_label = self._classes[top_idx]
        confidence = float(proba_array[top_idx])

        probabilities: Dict[str, float] = {
            cls_name: float(p) for cls_name, p in zip(self._classes, proba_array)
        }

        category = TicketCategory.from_str(predicted_label)
        return PredictionResult(
            predicted_category=category,
            confidence=round(confidence, 4),
            probabilities={k: round(v, 4) for k, v in probabilities.items()},
            model_version=self._model_version,
            latency_ms=round(elapsed_ms, 2),
        )

    def predict_batch(self, texts: List[str]) -> List[PredictionResult]:
        if not self.is_fitted:
            raise RuntimeError("Baseline classifier must be fitted before predict_batch() is called.")

        start_time = time.perf_counter()
        proba_matrix = self._pipeline.predict_proba(texts)
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / max(len(texts), 1)

        results = []
        for proba_array in proba_matrix:
            top_idx = int(np.argmax(proba_array))
            predicted_label = self._classes[top_idx]
            confidence = float(proba_array[top_idx])
            probabilities = {
                cls_name: float(p) for cls_name, p in zip(self._classes, proba_array)
            }
            results.append(
                PredictionResult(
                    predicted_category=TicketCategory.from_str(predicted_label),
                    confidence=round(confidence, 4),
                    probabilities={k: round(v, 4) for k, v in probabilities.items()},
                    model_version=self._model_version,
                    latency_ms=round(avg_latency_ms, 2),
                )
            )
        return results
