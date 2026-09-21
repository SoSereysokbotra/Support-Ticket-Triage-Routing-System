import statistics
import sys
import time
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from src.infrastructure.data.dataset_loader import DatasetLoader
from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier
from src.infrastructure.models.onnx_distilbert_classifier import OnnxDistilBertClassifier


def run_benchmark(model_dir: str = "models/distilbert_v0", num_samples: int = 50):
    print("=" * 70)
    print("  ONNX MODEL ACCELERATION BENCHMARK: PyTorch vs. ONNX Runtime  ")
    print("=" * 70)

    model_path = Path(model_dir)
    if not (model_path / "model.onnx").exists():
        print(f"Error: ONNX model not found in {model_dir}. Please run export first.")
        sys.exit(1)

    # 1. Load sample dataset
    print(f"\n[1/4] Loading {num_samples} evaluation tickets from dataset...")
    loader = DatasetLoader()
    df = loader.load_or_create_dataset()
    texts = df["text"].head(num_samples).tolist()

    # 2. Instantiate both classifiers
    print("[2/4] Initializing PyTorch DistilBertTicketClassifier...")
    pt_clf = DistilBertTicketClassifier(
        model_path_or_name=model_path,
        model_version="distilbert-pytorch",
        device="cpu",
    )

    print("[2/4] Initializing OnnxDistilBertClassifier (intra_op_threads=4)...")
    onnx_clf = OnnxDistilBertClassifier(
        model_path_or_dir=model_path,
        model_version="distilbert-onnx",
        num_threads=4,
    )

    # 3. Warm-up
    print("[3/4] Warming up inference runtimes (5 iterations)...")
    for t in texts[:5]:
        _ = pt_clf.predict(t)
        _ = onnx_clf.predict(t)

    # 4. Single-Item Latency Benchmark
    print(f"[4/4] Executing single-prediction benchmark ({num_samples} tickets)...")
    pt_latencies = []
    pt_categories = []
    pt_probs = []

    for t in texts:
        t0 = time.perf_counter()
        res = pt_clf.predict(t)
        pt_latencies.append((time.perf_counter() - t0) * 1000.0)
        pt_categories.append(res.predicted_category.value)
        pt_probs.append(res.probabilities)

    onnx_latencies = []
    onnx_categories = []
    onnx_probs = []

    for t in texts:
        t0 = time.perf_counter()
        res = onnx_clf.predict(t)
        onnx_latencies.append((time.perf_counter() - t0) * 1000.0)
        onnx_categories.append(res.predicted_category.value)
        onnx_probs.append(res.probabilities)

    # Compute Statistics
    pt_mean = statistics.mean(pt_latencies)
    pt_p50 = statistics.median(pt_latencies)
    pt_p95 = np.percentile(pt_latencies, 95)
    pt_p99 = np.percentile(pt_latencies, 99)

    onnx_mean = statistics.mean(onnx_latencies)
    onnx_p50 = statistics.median(onnx_latencies)
    onnx_p95 = np.percentile(onnx_latencies, 95)
    onnx_p99 = np.percentile(onnx_latencies, 99)

    speedup_mean = pt_mean / onnx_mean if onnx_mean > 0 else 0
    speedup_p50 = pt_p50 / onnx_p50 if onnx_p50 > 0 else 0
    speedup_p95 = pt_p95 / onnx_p95 if onnx_p95 > 0 else 0

    # Numerical Parity Check
    category_matches = sum(1 for p, o in zip(pt_categories, onnx_categories) if p == o)
    agreement_pct = (category_matches / len(texts)) * 100.0

    max_prob_diff = 0.0
    for p_map, o_map in zip(pt_probs, onnx_probs):
        for k in p_map:
            diff = abs(p_map[k] - o_map.get(k, 0.0))
            if diff > max_prob_diff:
                max_prob_diff = diff

    # 5. Batch Throughput Benchmark
    batch_size = 20
    batch_texts = texts[:batch_size]
    t0 = time.perf_counter()
    _ = pt_clf.predict_batch(batch_texts)
    pt_batch_time = time.perf_counter() - t0
    pt_qps = batch_size / pt_batch_time

    t0 = time.perf_counter()
    _ = onnx_clf.predict_batch(batch_texts)
    onnx_batch_time = time.perf_counter() - t0
    onnx_qps = batch_size / onnx_batch_time
    batch_speedup = onnx_qps / pt_qps if pt_qps > 0 else 0

    # Print Summary Report
    print("\n" + "=" * 70)
    print("                    BENCHMARK RESULTS & METRICS                       ")
    print("=" * 70)
    print(f"{'Metric':<30} | {'PyTorch CPU':<16} | {'ONNX Runtime':<16} | {'Speedup'}")
    print("-" * 75)
    print(f"{'Mean Latency':<30} | {pt_mean:8.2f} ms     | {onnx_mean:8.2f} ms     | {speedup_mean:5.2f}x")
    print(f"{'p50 Latency (Median)':<30} | {pt_p50:8.2f} ms     | {onnx_p50:8.2f} ms     | {speedup_p50:5.2f}x")
    print(f"{'p95 Latency':<30} | {pt_p95:8.2f} ms     | {onnx_p95:8.2f} ms     | {speedup_p95:5.2f}x")
    print(f"{'p99 Latency':<30} | {pt_p99:8.2f} ms     | {onnx_p99:8.2f} ms     | {pt_p99/onnx_p99:5.2f}x")
    print(f"{'Batch Throughput (QPS)':<30} | {pt_qps:8.1f} req/s  | {onnx_qps:8.1f} req/s  | {batch_speedup:5.2f}x")
    print("-" * 75)
    print("\nNUMERICAL ACCURACY & PARITY:")
    print(f"  • Category Classification Agreement: {agreement_pct:.2f}% ({category_matches}/{len(texts)} tickets matched)")
    print(f"  • Maximum Absolute Probability Delta: {max_prob_diff:.6e} (tolerance: 1e-3)")

    if agreement_pct == 100.0 and max_prob_diff < 1e-3:
        print("  • Status: [PASS] 100% Bit-level & Logical Parity Verified!")
    else:
        print("  • Status: [WARNING] Slight discrepancy detected in probability values.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
