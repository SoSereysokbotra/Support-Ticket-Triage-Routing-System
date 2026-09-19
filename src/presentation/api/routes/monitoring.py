"""
Monitoring API Routes
Provides endpoints for querying live inference telemetry, KPIs, and triggering
statistical drift analysis on demand.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from src.infrastructure.monitoring.drift_detector import DriftDetector
from src.infrastructure.monitoring.prediction_logger import PredictionLogger

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring & Drift"])


@router.get("/metrics")
async def get_monitoring_metrics(request: Request) -> Dict[str, Any]:
    """Returns aggregated real-time prediction KPIs and category distribution."""
    logger: Optional[PredictionLogger] = getattr(request.app.state, "prediction_logger", None)
    if not logger:
        raise HTTPException(status_code=503, detail="Prediction logger is not initialized.")
    return logger.get_summary_metrics()


@router.get("/logs")
async def get_recent_logs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=5000),
) -> List[Dict[str, Any]]:
    """Returns the most recent prediction logs as JSON objects."""
    logger: Optional[PredictionLogger] = getattr(request.app.state, "prediction_logger", None)
    if not logger:
        raise HTTPException(status_code=503, detail="Prediction logger is not initialized.")

    df = logger.get_recent_logs(limit=limit)
    if df.empty:
        return []

    # Convert dataframe records to serializable dicts
    records = df.to_dict(orient="records")
    for r in records:
        if "timestamp" in r and hasattr(r["timestamp"], "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()
    return records


@router.post("/drift/analyze")
async def analyze_drift(
    request: Request,
    window_size: int = Query(default=500, ge=10, le=5000),
) -> Dict[str, Any]:
    """Runs statistical drift detection on current production inference logs."""
    logger: Optional[PredictionLogger] = getattr(request.app.state, "prediction_logger", None)
    if not logger:
        raise HTTPException(status_code=503, detail="Prediction logger is not initialized.")

    current_df = logger.get_recent_logs(limit=window_size)
    if len(current_df) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient logged traffic ({len(current_df)} records) for statistical drift analysis. Require at least 5 records.",
        )

    detector = DriftDetector()
    drift_result = detector.analyze_drift(current_df, generate_html=True)
    return drift_result.to_dict()
