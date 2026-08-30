import shutil
from pathlib import Path

import pytest

from src.domain.entities.category import TicketCategory
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry


@pytest.fixture
def test_registry(tmp_path: Path):
    db_file = tmp_path / "test_mlruns.db"
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    tracking_uri = f"sqlite:///{db_file.as_posix()}"
    registry = MLflowModelRegistry(
        tracking_uri=tracking_uri,
        registry_uri=tracking_uri,
        project_root=tmp_path,
    )
    yield registry


def test_experiment_creation_and_dataset_hash(test_registry: MLflowModelRegistry, tmp_path: Path):
    # Test dataset hashing
    sample_file = tmp_path / "dataset.csv"
    sample_file.write_text("text,category\nsample ticket,Hardware\n", encoding="utf-8")
    hash_val = test_registry.compute_dataset_hash(sample_file)
    assert len(hash_val) == 12

    # Test experiment creation
    exp_id = test_registry.get_or_create_experiment("test-exp")
    assert exp_id is not None


def test_log_run_and_register_model(test_registry: MLflowModelRegistry, tmp_path: Path):
    model_dir = tmp_path / "model_weights"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type": "distilbert"}', encoding="utf-8")

    params = {"learning_rate": 3e-5, "epochs": 3}
    metrics = {"macro_f1": 0.94, "accuracy": 0.95}

    run_id = test_registry.log_training_run(
        params=params,
        metrics=metrics,
        model_artifact_dir=model_dir,
        run_name="test-run-1",
    )
    assert run_id is not None

    # Register Model
    mv = test_registry.register_model_from_run(
        run_id=run_id,
        model_name="test-ticket-classifier",
        description="Initial unit test version",
    )
    assert str(mv.version) == "1"

    # Set Alias to production
    test_registry.set_alias(
        model_name="test-ticket-classifier",
        alias="production",
        version="1",
    )

    prod_version = test_registry.get_version_by_alias(
        model_name="test-ticket-classifier",
        alias="production",
    )
    assert prod_version is not None
    assert str(prod_version.version) == "1"


def test_metadata_rollback_mechanism(test_registry: MLflowModelRegistry, tmp_path: Path):
    model_dir = tmp_path / "model_weights"
    model_dir.mkdir(exist_ok=True)
    (model_dir / "config.json").write_text('{"model_type": "distilbert"}', encoding="utf-8")

    # Run 1 -> Version 1 (Promoted to production)
    run1 = test_registry.log_training_run(
        params={"lr": 1e-4},
        metrics={"macro_f1": 0.88},
        model_artifact_dir=model_dir,
        run_name="v1",
    )
    mv1 = test_registry.register_model_from_run(run_id=run1, model_name="rollback-classifier")
    test_registry.set_alias("rollback-classifier", "production", str(mv1.version))

    # Run 2 -> Version 2 (Promoted to production)
    run2 = test_registry.log_training_run(
        params={"lr": 2e-4},
        metrics={"macro_f1": 0.70},  # Regressed model
        model_artifact_dir=model_dir,
        run_name="v2",
    )
    mv2 = test_registry.register_model_from_run(run_id=run2, model_name="rollback-classifier")
    test_registry.set_alias("rollback-classifier", "production", str(mv2.version))

    # Confirm v2 is currently production
    curr_prod = test_registry.get_version_by_alias("rollback-classifier", "production")
    assert str(curr_prod.version) == "2"

    # Rollback to v1 (Zero code change)
    rollback_res = test_registry.rollback_to_version(
        target_version="1",
        model_name="rollback-classifier",
        alias="production",
    )
    assert rollback_res["rollback_status"] == "success"
    assert str(rollback_res["previous_version"]) == "2"
    assert str(rollback_res["current_version"]) == "1"

    # Confirm active production is now v1
    new_prod = test_registry.get_version_by_alias("rollback-classifier", "production")
    assert str(new_prod.version) == "1"
