from pathlib import Path
from typing import Any, Dict, Optional

from prefect import task

from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry
from src.pipelines.orchestration.tasks.gate import GateDecision


@task(name="register_model_task")
def register_model_task(
    model_dir: Path,
    params: Dict[str, str],
    metrics: Dict[str, Any],
    gate_decision: GateDecision,
    dataset_path: Optional[Path] = None,
    registry: Optional[MLflowModelRegistry] = None,
    model_name: str = "ticket-classifier",
    run_name_prefix: str = "prefect_retrain",
) -> Dict[str, Any]:
    """
    Registers the trained model into MLflow and applies alias according to GateDecision.
    """
    reg = registry or MLflowModelRegistry()
    run_name = f"{run_name_prefix}_f1_{gate_decision.candidate_macro_f1:.4f}"

    # Flatten and prefix metrics for MLflow logging
    mlflow_metrics = {
        "test_macro_f1": gate_decision.candidate_macro_f1,
        "test_weighted_f1": float(metrics.get("weighted_f1", 0.0)),
        "test_accuracy": float(metrics.get("accuracy", 0.0)),
        "p50_latency_ms": float(metrics.get("p50_latency_ms", 0.0)),
        "p95_latency_ms": float(metrics.get("p95_latency_ms", 0.0)),
        "gate_passed": 1.0 if gate_decision.passed else 0.0,
    }

    # Add per-class f1 metrics
    for cat, f1_score in metrics.get("per_class_f1", {}).items():
        clean_key = f"test_f1_{cat.lower().replace(' ', '_').replace('&', 'and')}"
        mlflow_metrics[clean_key] = float(f1_score)

    print("[RegisterTask] Logging training run to MLflow...")
    run_id = reg.log_training_run(
        params=params,
        metrics=mlflow_metrics,
        model_artifact_dir=model_dir,
        dataset_path=dataset_path,
        run_name=run_name,
        tags={
            "orchestrator": "prefect",
            "gate_decision": "passed" if gate_decision.passed else "rejected",
            "gate_reason": gate_decision.reason,
        },
    )

    print(f"[RegisterTask] Registering model version under '{model_name}'...")
    mv = reg.register_model_from_run(
        run_id=run_id,
        model_name=model_name,
        description=f"Prefect Retraining (Macro-F1: {gate_decision.candidate_macro_f1:.4f}) | Gate: {gate_decision.reason}",
    )
    version_str = str(mv.version)

    # Apply alias based on gate decision
    target_alias = gate_decision.target_alias
    reg.set_alias(model_name=model_name, alias=target_alias, version=version_str)
    print(f"[RegisterTask] Model version v{version_str} tagged with alias '{target_alias}'.")

    return {
        "run_id": run_id,
        "model_name": model_name,
        "version": version_str,
        "alias": target_alias,
        "gate_passed": gate_decision.passed,
        "reason": gate_decision.reason,
    }
