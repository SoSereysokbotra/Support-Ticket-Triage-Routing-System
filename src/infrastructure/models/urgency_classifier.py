"""
Urgency Classifier Implementations
Provides Baseline TF-IDF and DistilBERT adapters for ticket urgency inference.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.domain.entities.category import TicketUrgency
from src.domain.interfaces.urgency_interface import IUrgencyClassifier
from src.domain.value_objects.urgency_result import UrgencyPredictionResult


class BaselineUrgencyClassifier(IUrgencyClassifier):
    """
    TF-IDF + Logistic Regression baseline model implementing IUrgencyClassifier.
    """

    def __init__(self, model_version: str = "tfidf-urgency-v0") -> None:
        self._model_version = model_version
        self._pipeline: Optional[Pipeline] = None
        self._classes: List[str] = []

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_fitted(self) -> bool:
        return self._pipeline is not None

    def fit(self, texts: List[str], labels: List[str]) -> "BaselineUrgencyClassifier":
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=4000, ngram_range=(1, 2), sublinear_tf=True)),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=500, random_state=42)),
        ])
        self._pipeline.fit(texts, labels)
        self._classes = list(self._pipeline.classes_)
        return self

    def predict(self, text: str) -> UrgencyPredictionResult:
        if not self.is_fitted:
            raise RuntimeError("Baseline urgency classifier must be fitted before predict() is called.")

        start_time = time.perf_counter()
        proba_array = self._pipeline.predict_proba([text])[0]
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        top_idx = int(np.argmax(proba_array))
        predicted_label = self._classes[top_idx]
        confidence = float(proba_array[top_idx])

        probabilities: Dict[str, float] = {
            cls_name: float(p) for cls_name, p in zip(self._classes, proba_array)
        }

        urgency = TicketUrgency.from_str(predicted_label)
        return UrgencyPredictionResult(
            predicted_urgency=urgency,
            confidence=confidence,
            probabilities=probabilities,
            model_version=self._model_version,
            latency_ms=round(elapsed_ms, 2),
        )

    def predict_batch(self, texts: List[str]) -> List[UrgencyPredictionResult]:
        if not self.is_fitted:
            raise RuntimeError("Baseline urgency classifier must be fitted before predict_batch() is called.")

        start_time = time.perf_counter()
        probas = self._pipeline.predict_proba(texts)
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / max(len(texts), 1)

        results = []
        for proba_array in probas:
            top_idx = int(np.argmax(proba_array))
            predicted_label = self._classes[top_idx]
            confidence = float(proba_array[top_idx])
            probabilities = {cls_name: float(p) for cls_name, p in zip(self._classes, proba_array)}
            urgency = TicketUrgency.from_str(predicted_label)
            results.append(
                UrgencyPredictionResult(
                    predicted_urgency=urgency,
                    confidence=confidence,
                    probabilities=probabilities,
                    model_version=self._model_version,
                    latency_ms=round(avg_latency_ms, 2),
                )
            )
        return results


class DistilBertUrgencyClassifier(IUrgencyClassifier):
    """
    Fine-tuned DistilBERT model implementing IUrgencyClassifier.
    """

    def __init__(
        self,
        model_path_or_name: Union[str, Path] = "distilbert-base-uncased",
        model_version: str = "distilbert-urgency-v0",
        device: Optional[str] = None,
        max_length: int = 128,
    ) -> None:
        self._model_version = model_version
        self.max_length = max_length

        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path_or_name))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(model_path_or_name))
        self.model.to(self.device)
        self.model.eval()

        self.id2label = self.model.config.id2label or {
            0: "Low",
            1: "Medium",
            2: "High",
            3: "Critical",
        }
        self.id2label = {int(k): v for k, v in self.id2label.items()}

    @property
    def model_version(self) -> str:
        return self._model_version

    @torch.no_grad()
    def predict(self, text: str) -> UrgencyPredictionResult:
        start_time = time.perf_counter()
        inputs = self.tokenizer(
            text,
            max_length=self.max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1).squeeze(0).cpu().numpy()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        top_idx = int(np.argmax(probs))
        predicted_label = self.id2label.get(top_idx, "Medium")
        confidence = float(probs[top_idx])

        probabilities: Dict[str, float] = {
            self.id2label.get(idx, f"CLASS_{idx}"): float(prob)
            for idx, prob in enumerate(probs)
        }

        urgency = TicketUrgency.from_str(predicted_label)
        return UrgencyPredictionResult(
            predicted_urgency=urgency,
            confidence=confidence,
            probabilities=probabilities,
            model_version=self._model_version,
            latency_ms=round(elapsed_ms, 2),
        )

    @torch.no_grad()
    def predict_batch(self, texts: List[str]) -> List[UrgencyPredictionResult]:
        if not texts:
            return []

        start_time = time.perf_counter()
        inputs = self.tokenizer(
            texts,
            max_length=self.max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        all_probs = F.softmax(outputs.logits, dim=-1).cpu().numpy()
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / len(texts)

        results = []
        for probs in all_probs:
            top_idx = int(np.argmax(probs))
            predicted_label = self.id2label.get(top_idx, "Medium")
            confidence = float(probs[top_idx])
            probabilities = {
                self.id2label.get(idx, f"CLASS_{idx}"): float(prob)
                for idx, prob in enumerate(probs)
            }
            urgency = TicketUrgency.from_str(predicted_label)
            results.append(
                UrgencyPredictionResult(
                    predicted_urgency=urgency,
                    confidence=confidence,
                    probabilities=probabilities,
                    model_version=self._model_version,
                    latency_ms=round(avg_latency_ms, 2),
                )
            )
        return results
