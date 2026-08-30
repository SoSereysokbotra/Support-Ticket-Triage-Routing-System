import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.domain.entities.category import TicketCategory
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.value_objects.prediction_result import PredictionResult


class DistilBertTicketClassifier(ITicketClassifier):
    """
    DistilBERT implementation of ITicketClassifier.
    Wraps PyTorch / Hugging Face model & tokenizer for production inference.
    """

    def __init__(
        self,
        model_path_or_name: Union[str, Path] = "distilbert-base-uncased",
        id2label: Optional[Dict[int, str]] = None,
        model_version: str = "distilbert-v0",
        device: Optional[str] = None,
    ) -> None:
        self._model_path = str(model_path_or_name)
        self._model_version = model_version
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Load Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self._model_path)

        # Load Model
        if id2label is not None:
            label2id = {v: k for k, v in id2label.items()}
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self._model_path,
                num_labels=len(id2label),
                id2label=id2label,
                label2id=label2id,
            )
        else:
            self.model = AutoModelForSequenceClassification.from_pretrained(self._model_path)

        self.model.to(self._device)
        self.model.eval()

        # Cache labels
        self._id2label = getattr(self.model.config, "id2label", None) or {
            i: cat.value for i, cat in enumerate(TicketCategory)
        }

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def device(self) -> str:
        return self._device

    def predict(self, text: str) -> PredictionResult:
        """Runs single-ticket inference."""
        start_time = time.perf_counter()

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=True,
        ).to(self._device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)[0].cpu().numpy()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        top_idx = int(probs.argmax())
        label_str = self._id2label[top_idx]
        confidence = float(probs[top_idx])

        probabilities = {
            self._id2label[i]: float(p) for i, p in enumerate(probs)
        }

        category = TicketCategory.from_str(label_str)
        return PredictionResult(
            predicted_category=category,
            confidence=round(confidence, 4),
            probabilities={k: round(v, 4) for k, v in probabilities.items()},
            model_version=self._model_version,
            latency_ms=round(elapsed_ms, 2),
        )

    def predict_batch(self, texts: List[str]) -> List[PredictionResult]:
        """Runs batch inference."""
        if not texts:
            return []

        start_time = time.perf_counter()

        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=True,
        ).to(self._device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1).cpu().numpy()

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / len(texts)

        results = []
        for row in probs:
            top_idx = int(row.argmax())
            label_str = self._id2label[top_idx]
            confidence = float(row[top_idx])
            probabilities = {
                self._id2label[i]: float(p) for i, p in enumerate(row)
            }
            results.append(
                PredictionResult(
                    predicted_category=TicketCategory.from_str(label_str),
                    confidence=round(confidence, 4),
                    probabilities={k: round(v, 4) for k, v in probabilities.items()},
                    model_version=self._model_version,
                    latency_ms=round(avg_latency_ms, 2),
                )
            )

        return results
