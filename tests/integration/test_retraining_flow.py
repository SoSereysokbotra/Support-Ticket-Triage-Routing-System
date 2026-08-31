from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.infrastructure.data.dataset_loader import DatasetLoader
from src.pipelines.orchestration.retraining_flow import retraining_flow
from src.pipelines.orchestration.tasks.gate import GateDecision
from src.pipelines.orchestration.tasks.validate import DataValidationError


def test_retraining_flow_halts_on_corrupted_data(tmp_path):
    # Create corrupted CSV with null texts
    corrupted_csv = tmp_path / "corrupted_tickets.csv"
    df = pd.DataFrame({
        "text": [None, "VPN is down", "Printer broke"] * 30,
        "category": ["Network", "Network", "Hardware"] * 30,
    })
    df.to_csv(corrupted_csv, index=False)

    with pytest.raises(DataValidationError, match="null values in 'text' column"):
        retraining_flow.fn(
            data_path=str(corrupted_csv),
            output_dir=str(tmp_path / "model_out"),
        )


def test_retraining_flow_end_to_end_orchestration(tmp_path):
    import importlib
    import sys

    # Get the actual module object
    flow_mod = sys.modules.get("src.pipelines.orchestration.retraining_flow") or importlib.import_module("src.pipelines.orchestration.retraining_flow")

    with (
        patch.object(
            flow_mod.compute_features_task,
            "fn",
            return_value=pd.DataFrame({"text": ["test sample text"] * 60, "category": ["Hardware"] * 60}),
        ),
        patch.object(
            flow_mod.train_model_task,
            "fn",
            return_value={
                "model_dir": tmp_path / "mock_model",
                "test_df": pd.DataFrame({"text": ["test sample text"], "category": ["Hardware"]}),
                "params": {"lr": "3e-5"},
            },
        ),
        patch.object(
            flow_mod.evaluate_model_task,
            "fn",
            return_value={
                "macro_f1": 0.96,
                "weighted_f1": 0.97,
                "accuracy": 0.97,
                "per_class_f1": {"Hardware": 0.96},
                "p50_latency_ms": 15.0,
                "p95_latency_ms": 25.0,
            },
        ),
        patch.object(
            flow_mod.quality_gate_task,
            "fn",
            return_value=GateDecision(
                passed=True,
                candidate_macro_f1=0.96,
                production_macro_f1=0.92,
                delta_f1=0.04,
                target_alias="production",
                reason="Improved by +0.04",
            ),
        ),
        patch.object(
            flow_mod.register_model_task,
            "fn",
            return_value={
                "run_id": "mock_run_123",
                "model_name": "ticket-classifier",
                "version": "4",
                "alias": "production",
                "gate_passed": True,
                "reason": "Improved by +0.04",
            },
        ),
    ):
        result = flow_mod.retraining_flow.fn(
            num_samples=600,
            output_dir=str(tmp_path / "mock_model"),
        )

        assert result["status"] == "success"
        assert result["gate_passed"] is True
        assert result["registered_version"] == "4"
        assert result["assigned_alias"] == "production"
        assert result["candidate_macro_f1"] == 0.96


