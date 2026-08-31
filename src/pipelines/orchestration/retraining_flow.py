import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prefect import flow

from src.pipelines.orchestration.tasks import (
    compute_features_task,
    evaluate_model_task,
    ingest_data_task,
    quality_gate_task,
    register_model_task,
    train_model_task,
    validate_data_task,
)


@flow(name="ticket_classifier_retraining_pipeline", log_prints=True)
def retraining_flow(
    data_path: Optional[str] = None,
    num_samples: int = 1200,
    learning_rate: float = 3e-5,
    num_epochs: int = 2,
    batch_size: int = 16,
    output_dir: Optional[str] = None,
    model_name: str = "ticket-classifier",
    min_absolute_macro_f1: float = 0.75,
    allowed_regression_margin: float = 0.02,
) -> Dict[str, Any]:
    """
    Automated Retraining DAG:
    1. Ingest ticket data
    2. Validate data quality, schema, and class distribution
    3. Compute / synchronize point-in-time features with Feast
    4. Fine-tune DistilBERT model
    5. Evaluate on held-out test split
    6. Evaluate Quality Gate against active production baseline
    7. Register model artifact to MLflow and conditionally update production alias
    """
    print("=" * 70)
    print("STARTING PREFECT RETRAINING PIPELINE")
    print("=" * 70)

    model_output_dir = Path(output_dir) if output_dir else (PROJECT_ROOT / "models" / "prefect_candidate")

    # Step 1: Ingest
    raw_df = ingest_data_task(
        data_path=Path(data_path) if data_path else None,
        num_samples=num_samples,
    )

    # Step 2: Validate Data Quality & Integrity
    validated_df = validate_data_task(raw_df)

    # Step 3: Compute / Join Features with Feast
    enriched_df = compute_features_task(validated_df)

    # Step 4: Train Model
    train_results = train_model_task(
        df=enriched_df,
        output_dir=model_output_dir,
        learning_rate=learning_rate,
        num_epochs=num_epochs,
        batch_size=batch_size,
    )

    # Step 5: Evaluate on Test Set
    eval_metrics = evaluate_model_task(
        model_dir=train_results["model_dir"],
        test_df=train_results["test_df"],
    )

    # Step 6: Quality Gate Evaluation
    gate_decision = quality_gate_task(
        candidate_metrics=eval_metrics,
        model_name=model_name,
        min_absolute_macro_f1=min_absolute_macro_f1,
        allowed_regression_margin=allowed_regression_margin,
    )

    # Step 7: MLflow Registration & Promotion
    registration_result = register_model_task(
        model_dir=train_results["model_dir"],
        params=train_results["params"],
        metrics=eval_metrics,
        gate_decision=gate_decision,
        dataset_path=Path(data_path) if data_path else None,
        model_name=model_name,
    )

    print("=" * 70)
    print(f"PIPELINE COMPLETED. Gate Passed: {gate_decision.passed} | Model Version: v{registration_result['version']} ({registration_result['alias']})")
    print("=" * 70)

    return {
        "status": "success",
        "gate_passed": gate_decision.passed,
        "gate_reason": gate_decision.reason,
        "candidate_macro_f1": gate_decision.candidate_macro_f1,
        "production_macro_f1": gate_decision.production_macro_f1,
        "delta_f1": gate_decision.delta_f1,
        "registered_version": registration_result["version"],
        "assigned_alias": registration_result["alias"],
        "eval_metrics": eval_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Prefect Retraining Pipeline for Ticket Classifier")
    parser.add_argument("--data-path", type=str, default=None, help="Path to raw ticket dataset (CSV or Parquet)")
    parser.add_argument("--samples", type=int, default=1200, help="Number of synthetic samples to generate if no file")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate for fine-tuning")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Training batch size")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save candidate checkpoint")

    args = parser.parse_args()

    retraining_flow(
        data_path=args.data_path,
        num_samples=args.samples,
        learning_rate=args.lr,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
