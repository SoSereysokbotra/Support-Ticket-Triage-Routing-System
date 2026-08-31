from unittest.mock import MagicMock
import pytest

from src.pipelines.orchestration.tasks.gate import GateDecision, quality_gate_task


def test_quality_gate_blocks_candidate_below_absolute_floor():
    metrics = {"macro_f1": 0.50}
    decision = quality_gate_task.fn(
        candidate_metrics=metrics,
        min_absolute_macro_f1=0.75,
    )
    assert decision.passed is False
    assert decision.target_alias == "candidate_rejected"
    assert "absolute quality floor" in decision.reason


def test_quality_gate_passes_when_no_production_baseline_exists():
    mock_registry = MagicMock()
    mock_registry.get_version_by_alias.return_value = None

    metrics = {"macro_f1": 0.88}
    decision = quality_gate_task.fn(
        candidate_metrics=metrics,
        registry=mock_registry,
        min_absolute_macro_f1=0.75,
    )
    assert decision.passed is True
    assert decision.target_alias == "production"
    assert "Initial Production Baseline" in decision.reason


def test_quality_gate_passes_when_candidate_improves_over_production():
    mock_prod_version = MagicMock()
    mock_prod_version.metrics = {"test_macro_f1": 0.90}

    mock_registry = MagicMock()
    mock_registry.get_version_by_alias.return_value = mock_prod_version

    candidate_metrics = {"macro_f1": 0.94}
    decision = quality_gate_task.fn(
        candidate_metrics=candidate_metrics,
        registry=mock_registry,
    )
    assert decision.passed is True
    assert decision.target_alias == "production"
    assert decision.delta_f1 > 0
    assert "improved or matched" in decision.reason


def test_quality_gate_blocks_regressed_candidate():
    mock_prod_version = MagicMock()
    mock_prod_version.metrics = {"test_macro_f1": 0.95}

    mock_registry = MagicMock()
    mock_registry.get_version_by_alias.return_value = mock_prod_version

    # Candidate with Macro-F1 = 0.82 (regressed by 0.13, greater than allowed margin 0.02)
    candidate_metrics = {"macro_f1": 0.82}
    decision = quality_gate_task.fn(
        candidate_metrics=candidate_metrics,
        registry=mock_registry,
        allowed_regression_margin=0.02,
    )
    assert decision.passed is False
    assert decision.target_alias == "candidate_rejected"
    assert decision.delta_f1 < -0.02
    assert "Promotion blocked" in decision.reason
