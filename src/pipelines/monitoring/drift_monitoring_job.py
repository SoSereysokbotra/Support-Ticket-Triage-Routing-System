"""
Closed-Loop Drift Monitoring & Auto-Retraining Trigger
Periodically or on-demand checks production inference logs for distribution shift.
When significant data drift or target drift is detected, automatically synthesizes/augments
retraining data and dispatches the Prefect retraining pipeline.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.infrastructure.data.dataset_loader import DatasetLoader
from src.infrastructure.monitoring.drift_detector import DriftDetector, DriftReportResult
from src.infrastructure.monitoring.prediction_logger import PredictionLogger
from src.pipelines.orchestration.retraining_flow import retraining_flow


def run_drift_monitoring_job(
    window_size: int = 500,
    drift_threshold: float = 0.35,
    auto_trigger_retraining: bool = True,
    epochs: int = 2,
    db_path: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes the drift monitoring routine:
    1. Reads recent production inference logs from SQLite.
    2. Compares distributions against baseline reference dataset.
    3. If drift is detected (> threshold), automatically triggers Prefect retraining flow.
    """
    print("=" * 65)
    print("STARTING CLOSED-LOOP DRIFT MONITORING JOB")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 65)

    logger = PredictionLogger(db_path=db_path)
    current_df = logger.get_recent_logs(limit=window_size)

    if current_df.empty or len(current_df) < 5:
        print(f"[DriftMonitor] Insufficient inference logs ({len(current_df)} records). Awaiting more traffic.")
        return {
            "status": "skipped",
            "reason": f"Insufficient records ({len(current_df)} < 5)",
            "drift_detected": False,
        }

    detector = DriftDetector(
        reports_dir=reports_dir,
        drift_share_threshold=drift_threshold,
    )
    drift_result: DriftReportResult = detector.analyze_drift(current_df, generate_html=True)

    print(f"[DriftMonitor] Analysis complete on {len(current_df)} production records.")
    print(f"  • Drift Detected: {drift_result.drift_detected}")
    print(f"  • Share of Drifted Features: {drift_result.share_drifted_features:.1%}")
    if drift_result.html_report_path:
        print(f"  • HTML Report saved to: {drift_result.html_report_path}")

    # 1. Stage drifted records into an annotation review queue for human-in-the-loop verification
    review_queue_path = Path("data/monitoring/drift_review_queue.csv")
    review_queue_path.parent.mkdir(parents=True, exist_ok=True)
    current_df.to_csv(review_queue_path, index=False)
    print(f"[DriftMonitor] Staged {len(current_df)} recent inference records to annotation queue: {review_queue_path}")

    retraining_triggered = False
    retraining_results = None

    if drift_result.drift_detected and auto_trigger_retraining:
        print("\n" + "!" * 65)
        print("[ALERT] CRITICAL DISTRIBUTION DRIFT DETECTED!")
        print("[MLOps Guard] In production, drifted samples must be human-verified")
        print("to prevent confirmation bias / model collapse feedback loops.")
        print("Dispatching Prefect Retraining Pipeline with augmented dataset...")
        print("!" * 65 + "\n")

        # Save an augmented dataset combining baseline + recent drifted records for retraining
        retraining_dataset_path = Path("data/monitoring/retraining_batch.csv")
        retraining_dataset_path.parent.mkdir(parents=True, exist_ok=True)

        loader = DatasetLoader()
        base_df = loader.load_or_create_dataset(num_samples=800, random_state=42)
        # Prepare current records with 'category'
        recent_augmented = current_df.copy()
        if "predicted_category" in recent_augmented.columns:
            recent_augmented["category"] = recent_augmented["predicted_category"]
        if "urgency" not in recent_augmented.columns:
            recent_augmented["urgency"] = "Medium"

        combined_df = pd.concat([base_df, recent_augmented[["text", "category", "urgency"]]], ignore_index=True)
        combined_df.to_csv(retraining_dataset_path, index=False)
        print(f"[DriftMonitor] Prepared augmented retraining dataset with {len(combined_df)} samples.")

        # Execute Prefect retraining flow
        retraining_results = retraining_flow(
            data_path=str(retraining_dataset_path),
            num_epochs=epochs,
            model_name="ticket-classifier",
        )
        retraining_triggered = True

    return {
        "status": "completed",
        "drift_detected": drift_result.drift_detected,
        "share_drifted_features": drift_result.share_drifted_features,
        "html_report_path": drift_result.html_report_path,
        "json_report_path": drift_result.json_report_path,
        "retraining_triggered": retraining_triggered,
        "retraining_results": retraining_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Run Drift Monitoring & Auto-Retraining Trigger")
    parser.add_argument("--window-size", type=int, default=500, help="Number of recent records to evaluate")
    parser.add_argument("--drift-threshold", type=float, default=0.35, help="Threshold for drift detection")
    parser.add_argument("--no-auto-retrain", action="store_true", help="Disable automatic retraining trigger")
    parser.add_argument("--epochs", type=int, default=2, help="Epochs for triggered retraining run")

    args = parser.parse_args()
    run_drift_monitoring_job(
        window_size=args.window_size,
        drift_threshold=args.drift_threshold,
        auto_trigger_retraining=not args.no_auto_retrain,
        epochs=args.epochs,
    )


if __name__ == "__main__":
    main()
