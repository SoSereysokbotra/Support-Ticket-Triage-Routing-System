from dataclasses import dataclass
from typing import Any, Dict, Optional

from prefect import task

from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry


@dataclass
class GateDecision:
    passed: bool
    candidate_macro_f1: float
    production_macro_f1: float
    delta_f1: float
    target_alias: str
    reason: str


@task(name="quality_gate_task")
def quality_gate_task(
    candidate_metrics: Dict[str, Any],
    registry: Optional[MLflowModelRegistry] = None,
    model_name: str = "ticket-classifier",
    min_absolute_macro_f1: float = 0.75,
    allowed_regression_margin: float = 0.02,
) -> GateDecision:
    """
    Quality Evaluation Gate.
    Compares candidate model's macro-F1 against current production model in MLflow.
    Blocks regressed models from promotion to production.
    """
    print("=" * 60)
    print("[QualityGateTask] Evaluating Candidate Model vs Production Benchmark...")
    print("=" * 60)

    candidate_f1 = float(candidate_metrics.get("macro_f1", 0.0))
    reg = registry or MLflowModelRegistry()

    # 1. Check absolute quality floor
    if candidate_f1 < min_absolute_macro_f1:
        reason = (
            f"Candidate macro-F1 ({candidate_f1:.4f}) failed absolute quality floor "
            f"threshold of {min_absolute_macro_f1:.4f}."
        )
        print(f"[QualityGate REJECTED] {reason}")
        return GateDecision(
            passed=False,
            candidate_macro_f1=candidate_f1,
            production_macro_f1=0.0,
            delta_f1=candidate_f1,
            target_alias="candidate_rejected",
            reason=reason,
        )

    # 2. Check against current production benchmark in MLflow
    prod_version = None
    try:
        prod_version = reg.get_version_by_alias(alias="production", model_name=model_name)
    except Exception as e:
        print(f"[QualityGateTask] No active production model found in registry: {e}")

    if not prod_version:
        # No existing production model; promote candidate as baseline
        reason = (
            f"No existing production model found. Candidate macro-F1 ({candidate_f1:.4f}) "
            f"exceeds floor ({min_absolute_macro_f1:.4f}) -> Initial Production Baseline."
        )
        print(f"[QualityGate PASSED] {reason}")
        return GateDecision(
            passed=True,
            candidate_macro_f1=candidate_f1,
            production_macro_f1=0.0,
            delta_f1=candidate_f1,
            target_alias="production",
            reason=reason,
        )

    prod_f1 = 0.85
    if hasattr(prod_version, "metrics") and isinstance(prod_version.metrics, dict) and prod_version.metrics:
        prod_f1 = float(prod_version.metrics.get("test_macro_f1", prod_version.metrics.get("macro_f1", 0.85)))
    elif prod_version and getattr(prod_version, "run_id", None) and isinstance(prod_version.run_id, str):
        try:
            run_data = reg.client.get_run(prod_version.run_id).data
            prod_f1 = float(run_data.metrics.get("test_macro_f1", run_data.metrics.get("macro_f1", 0.85)))
        except Exception:
            prod_f1 = 0.85

    delta_f1 = candidate_f1 - prod_f1
    required_f1 = prod_f1 - allowed_regression_margin

    if candidate_f1 >= required_f1:
        if delta_f1 >= 0:
            reason = (
                f"Candidate macro-F1 ({candidate_f1:.4f}) improved or matched production "
                f"macro-F1 ({prod_f1:.4f}) by +{delta_f1:.4f}."
            )
        else:
            reason = (
                f"Candidate macro-F1 ({candidate_f1:.4f}) is within allowed regression margin "
                f"(-{abs(delta_f1):.4f} <= {allowed_regression_margin:.4f}) vs production ({prod_f1:.4f})."
            )
        print(f"[QualityGate PASSED] {reason}")
        return GateDecision(
            passed=True,
            candidate_macro_f1=candidate_f1,
            production_macro_f1=prod_f1,
            delta_f1=delta_f1,
            target_alias="production",
            reason=reason,
        )
    else:
        reason = (
            f"Candidate macro-F1 ({candidate_f1:.4f}) regressed beyond allowed margin "
            f"vs production ({prod_f1:.4f}) [delta: {delta_f1:.4f} < -{allowed_regression_margin:.4f}]. Promotion blocked."
        )
        print(f"[QualityGate REJECTED] {reason}")
        return GateDecision(
            passed=False,
            candidate_macro_f1=candidate_f1,
            production_macro_f1=prod_f1,
            delta_f1=delta_f1,
            target_alias="candidate_rejected",
            reason=reason,
        )
