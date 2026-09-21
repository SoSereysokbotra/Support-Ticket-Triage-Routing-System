"""
Prometheus Metrics Instrumentation for Support Ticket Triage System
Provides Prometheus Counters, Gauges, and Histograms for HTTP and ML telemetry.
"""

from typing import Any, Dict

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# 1. HTTP Golden Signals
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests received",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
)

# 2. ML & Triage Telemetry
TRIAGE_PREDICTIONS_TOTAL = Counter(
    "triage_predictions_total",
    "Total ticket triage predictions made",
    ["predicted_category", "priority_level", "assigned_team", "auto_routed"],
)

TRIAGE_PREDICTION_CONFIDENCE = Histogram(
    "triage_prediction_confidence",
    "Distribution of prediction confidence scores",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

TRIAGE_INFERENCE_LATENCY_SECONDS = Histogram(
    "triage_inference_latency_seconds",
    "Latency of ML inference execution in seconds",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

TRIAGE_ACTIVE_MODEL_INFO = Gauge(
    "triage_active_model_info",
    "Current active production model version and framework",
    ["model_version"],
)


def record_prediction_telemetry(prediction: Dict[str, Any]) -> None:
    """Helper to record metrics from a prediction response dict."""
    try:
        predicted_category = str(prediction.get("predicted_category", "Unknown"))
        priority_level = str(prediction.get("priority_level", "Unknown"))
        assigned_team = str(prediction.get("assigned_team", "Unknown"))
        auto_routed = "true" if prediction.get("auto_routed", False) else "false"

        TRIAGE_PREDICTIONS_TOTAL.labels(
            predicted_category=predicted_category,
            priority_level=priority_level,
            assigned_team=assigned_team,
            auto_routed=auto_routed,
        ).inc()

        confidence = float(prediction.get("confidence", 0.0))
        TRIAGE_PREDICTION_CONFIDENCE.observe(confidence)

        latency_ms = float(prediction.get("latency_ms", 0.0))
        TRIAGE_INFERENCE_LATENCY_SECONDS.observe(latency_ms / 1000.0)

        model_version = str(prediction.get("model_version", "unknown"))
        TRIAGE_ACTIVE_MODEL_INFO.labels(model_version=model_version).set(1)
    except Exception:
        pass


def get_prometheus_metrics() -> bytes:
    """Returns the latest Prometheus formatted metrics."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Returns the Prometheus content type header."""
    return CONTENT_TYPE_LATEST
