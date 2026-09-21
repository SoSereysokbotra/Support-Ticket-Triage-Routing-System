import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

from src.domain.entities.category import TicketCategory
from src.domain.interfaces.model_interface import ITicketClassifier
from src.domain.value_objects.prediction_result import PredictionResult


def _softmax(x: np.ndarray) -> np.ndarray:
    """Computes numerically stable softmax over the last axis of a NumPy array."""
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)


class OnnxDistilBertClassifier(ITicketClassifier):
    """
    High-performance ONNX Runtime implementation of ITicketClassifier.
    Executes compiled DistilBERT computation graphs via optimized CPU kernels,
    delivering ~3-4x lower latency and reduced memory overhead compared to PyTorch.
    """

    def __init__(
        self,
        model_path_or_dir: Union[str, Path] = "models/distilbert_v0",
        onnx_file_name: str = "model.onnx",
        id2label: Optional[Dict[int, str]] = None,
        model_version: str = "distilbert-onnx-v0",
        num_threads: Optional[int] = None,
    ) -> None:
        import os

        self._model_version = model_version
        self._device = "cpu-onnxruntime"

        base_path = Path(model_path_or_dir)
        if base_path.is_file() and base_path.suffix == ".onnx":
            self._onnx_path = base_path
            self._model_dir = base_path.parent
        else:
            self._model_dir = base_path
            self._onnx_path = base_path / onnx_file_name

        if not self._onnx_path.exists():
            raise FileNotFoundError(
                f"ONNX model file not found at: {self._onnx_path}. "
                f"Run the ONNX exporter (src/pipelines/export/export_onnx.py) first."
            )

        # 1. Initialize Tokenizer from model directory
        self.tokenizer = AutoTokenizer.from_pretrained(str(self._model_dir))

        # 2. Configure ONNX Runtime Session Options
        effective_threads = num_threads or min(8, os.cpu_count() or 4)
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = effective_threads
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        self.session = ort.InferenceSession(
            str(self._onnx_path),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )

        # 3. Resolve Label Mapping
        if id2label is not None:
            self._id2label = id2label
        else:
            config_path = self._model_dir / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    raw_id2label = cfg.get("id2label", {})
                    self._id2label = {int(k): v for k, v in raw_id2label.items()} if raw_id2label else {}
                except Exception:
                    self._id2label = {}
            else:
                self._id2label = {}

        if not self._id2label:
            self._id2label = {i: cat.value for i, cat in enumerate(TicketCategory)}

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def device(self) -> str:
        return self._device

    def predict(self, text: str) -> PredictionResult:
        """
        Runs accelerated single-ticket inference using ONNX Runtime.
        """
        start_time = time.perf_counter()

        # Tokenize directly to NumPy arrays (bypasses PyTorch tensor allocation)
        inputs = self.tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            max_length=256,
            padding=True,
        )

        ort_inputs = {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        }

        ort_outputs = self.session.run(["logits"], ort_inputs)
        logits = ort_outputs[0]
        probs = _softmax(logits)[0]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        top_idx = int(probs.argmax())
        label_str = self._id2label.get(top_idx, TicketCategory.OTHER.value)
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
        """
        Runs accelerated vectorized batch inference using ONNX Runtime.
        """
        if not texts:
            return []

        start_time = time.perf_counter()

        inputs = self.tokenizer(
            texts,
            return_tensors="np",
            truncation=True,
            max_length=256,
            padding=True,
        )

        ort_inputs = {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        }

        ort_outputs = self.session.run(["logits"], ort_inputs)
        logits = ort_outputs[0]
        probs = _softmax(logits)

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        avg_latency_ms = total_elapsed_ms / len(texts)

        results = []
        for row in probs:
            top_idx = int(row.argmax())
            label_str = self._id2label.get(top_idx, TicketCategory.OTHER.value)
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
