from pathlib import Path
from typing import Any, Dict

import pandas as pd
from prefect import task

from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier
from src.pipelines.training.evaluate import evaluate_classifier


@task(name="evaluate_model_task")
def evaluate_model_task(
    model_dir: Path,
    test_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Evaluates candidate model on the held-out test split.
    """
    print(f"[EvaluateTask] Evaluating model from {model_dir} on {len(test_df)} test samples...")
    classifier = DistilBertTicketClassifier(
        model_path_or_name=model_dir,
        model_version="candidate-evaluation",
    )

    metrics = evaluate_classifier(
        classifier=classifier,
        test_df=test_df,
    )

    print(f"[EvaluateTask] Evaluation complete. Test Macro-F1: {metrics['macro_f1']:.4f}, Accuracy: {metrics['accuracy']:.4f}")
    return {
        "macro_f1": float(metrics["macro_f1"]),
        "weighted_f1": float(metrics["weighted_f1"]),
        "accuracy": float(metrics["accuracy"]),
        "per_class_f1": {k: float(v["f1-score"]) for k, v in metrics["per_class_f1"].items()},
        "p50_latency_ms": float(metrics["latency"]["p50_ms"]),
        "p95_latency_ms": float(metrics["latency"]["p95_ms"]),
    }
