import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from src.domain.entities.category import TicketCategory
from src.domain.interfaces.model_interface import ITicketClassifier
from src.infrastructure.data.dataset_loader import DatasetLoader
from src.infrastructure.models.baseline_classifier import BaselineTfidfClassifier
from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier


def evaluate_classifier(
    classifier: ITicketClassifier,
    test_df: pd.DataFrame,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """
    Evaluates an ITicketClassifier against a test DataFrame.
    Computes macro-F1, per-class F1, confusion matrix, and latency percentiles.
    """
    texts = test_df["text"].tolist()
    ground_truth = test_df["category"].tolist()

    # Latency & Batch Inference
    latencies: List[float] = []
    predictions: List[str] = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        t0 = time.perf_counter()
        results = classifier.predict_batch(batch_texts)
        t1 = time.perf_counter()

        batch_latency_ms = (t1 - t0) * 1000.0
        per_sample_latency = batch_latency_ms / len(batch_texts)
        latencies.extend([per_sample_latency] * len(batch_texts))
        predictions.extend([r.predicted_category.value for r in results])

    categories = [cat.value for cat in TicketCategory]
    report_dict = classification_report(
        ground_truth,
        predictions,
        labels=categories,
        output_dict=True,
        zero_division=0,
    )

    macro_f1 = f1_score(ground_truth, predictions, average="macro", zero_division=0)
    weighted_f1 = f1_score(ground_truth, predictions, average="weighted", zero_division=0)
    cm = confusion_matrix(ground_truth, predictions, labels=categories)

    latencies_np = np.array(latencies)
    latency_stats = {
        "p50_ms": round(float(np.percentile(latencies_np, 50)), 2),
        "p90_ms": round(float(np.percentile(latencies_np, 90)), 2),
        "p95_ms": round(float(np.percentile(latencies_np, 95)), 2),
        "p99_ms": round(float(np.percentile(latencies_np, 99)), 2),
        "mean_ms": round(float(np.mean(latencies_np)), 2),
    }

    per_class_f1 = {
        cat: {
            "precision": round(report_dict[cat]["precision"], 4),
            "recall": round(report_dict[cat]["recall"], 4),
            "f1-score": round(report_dict[cat]["f1-score"], 4),
            "support": int(report_dict[cat]["support"]),
        }
        for cat in categories
        if cat in report_dict
    }

    return {
        "model_version": classifier.model_version,
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "accuracy": round(report_dict["accuracy"], 4),
        "per_class_f1": per_class_f1,
        "latency": latency_stats,
        "confusion_matrix": cm.tolist(),
        "categories": categories,
    }


def print_evaluation_summary(metrics: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print(f"EVALUATION SUMMARY — Model: {metrics['model_version']}")
    print("=" * 70)
    print(f"Overall Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro-F1 (Gate Metric): {metrics['macro_f1']:.4f}")
    print(f"Weighted-F1: {metrics['weighted_f1']:.4f}")
    print("\n--- Per-Class Performance ---")
    print(f"{'Category':<24} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 70)
    for cat, stats in metrics["per_class_f1"].items():
        print(
            f"{cat:<24} | {stats['precision']:<10.4f} | {stats['recall']:<10.4f} | "
            f"{stats['f1-score']:<10.4f} | {stats['support']:<8}"
        )

    print("\n--- Inference Latency ---")
    print(
        f"Mean: {metrics['latency']['mean_ms']}ms | "
        f"p50: {metrics['latency']['p50_ms']}ms | "
        f"p95: {metrics['latency']['p95_ms']}ms | "
        f"p99: {metrics['latency']['p99_ms']}ms"
    )
    print("=" * 70 + "\n")


def run_benchmark_comparison() -> None:
    loader = DatasetLoader()
    train_df, val_df, test_df = loader.get_stratified_splits()

    print(f"Loaded test set with {len(test_df)} samples across {test_df['category'].nunique()} categories.")

    # 1. Evaluate TF-IDF Baseline
    print("\n[1/2] Training and Evaluating TF-IDF Baseline...")
    tfidf_clf = BaselineTfidfClassifier(model_version="tfidf-baseline-v0")
    tfidf_clf.fit(train_df["text"].tolist(), train_df["category"].tolist())
    tfidf_metrics = evaluate_classifier(tfidf_clf, test_df)
    print_evaluation_summary(tfidf_metrics)

    # 2. Evaluate DistilBERT if available
    project_root = Path(__file__).resolve().parents[3]
    distilbert_path = project_root / "models" / "distilbert_v0"
    if distilbert_path.exists() and (distilbert_path / "config.json").exists():
        print("[2/2] Evaluating DistilBERT Fine-Tuned Model...")
        distilbert_clf = DistilBertTicketClassifier(
            model_path_or_name=distilbert_path,
            model_version="distilbert-v0",
        )
        distilbert_metrics = evaluate_classifier(distilbert_clf, test_df)
        print_evaluation_summary(distilbert_metrics)
    else:
        print("[2/2] DistilBERT checkpoint not found. Run train_distilbert.py to train it.")


if __name__ == "__main__":
    run_benchmark_comparison()
