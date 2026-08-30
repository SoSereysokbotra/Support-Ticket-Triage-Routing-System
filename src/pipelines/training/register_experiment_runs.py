import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.infrastructure.data.dataset_loader import DatasetLoader
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry
from src.pipelines.training.train_distilbert import train_model


def run_experiment_suite() -> None:
    """
    Executes multiple training runs with distinct hyperparameters,
    logs parameters, metrics, dataset hash, and artifacts to MLflow,
    registers model versions, and tags initial staging and production aliases.
    """
    print("=" * 70)
    print("PHASE 1: MLflow Experiment Tracking & Multi-Version Registration")
    print("=" * 70)

    registry = MLflowModelRegistry(project_root=PROJECT_ROOT)
    data_loader = DatasetLoader()
    raw_dataset_path = data_loader.raw_dir / "tickets_bootstrap.csv"
    if not raw_dataset_path.exists():
        data_loader.generate_bootstrap_dataset()

    experiments = [
        {
            "run_name": "distilbert_v1_baseline_lr3e-5",
            "lr": 3e-5,
            "epochs": 2,
            "batch_size": 16,
            "alias_target": "production",
            "desc": "Baseline DistilBERT fine-tuning (LR: 3e-5, 2 epochs)",
        },
        {
            "run_name": "distilbert_v2_high_lr5e-5",
            "lr": 5e-5,
            "epochs": 1,
            "batch_size": 16,
            "alias_target": "staging",
            "desc": "Aggressive learning rate experiment (LR: 5e-5, 1 epoch)",
        },
        {
            "run_name": "distilbert_v3_conservative_lr1e-5",
            "lr": 1e-5,
            "epochs": 1,
            "batch_size": 16,
            "alias_target": None,
            "desc": "Conservative learning rate experiment (LR: 1e-5, 1 epoch)",
        },
    ]

    registered_versions = []

    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] Running Experiment: {exp['run_name']}...")
        output_dir = PROJECT_ROOT / "models" / f"exp_run_{i}"

        # 1. Train model
        train_metadata = train_model(
            output_dir=output_dir,
            num_epochs=exp["epochs"],
            batch_size=exp["batch_size"],
            learning_rate=exp["lr"],
        )

        # 2. Log to MLflow
        params = {
            "model_architecture": "distilbert-base-uncased",
            "learning_rate": exp["lr"],
            "num_epochs": exp["epochs"],
            "batch_size": exp["batch_size"],
            "loss_function": "WeightedCrossEntropyLoss",
        }
        metrics = {
            "test_macro_f1": train_metadata["test_macro_f1"],
            "test_weighted_f1": train_metadata["test_weighted_f1"],
            "test_accuracy": train_metadata["test_accuracy"],
        }

        run_id = registry.log_training_run(
            params=params,
            metrics=metrics,
            model_artifact_dir=output_dir,
            dataset_path=raw_dataset_path,
            run_name=exp["run_name"],
            tags={"experiment_phase": "Phase 1 - Model Registry"},
        )
        print(f"Logged run {run_id} to MLflow.")

        # 3. Register in Model Registry
        mv = registry.register_model_from_run(
            run_id=run_id,
            model_name="ticket-classifier",
            description=exp["desc"],
        )
        version_num = str(mv.version)
        print(f"Registered Model Version: v{version_num} for ticket-classifier.")

        # 4. Set Alias if specified
        if exp["alias_target"]:
            registry.set_alias(
                model_name="ticket-classifier",
                alias=exp["alias_target"],
                version=version_num,
            )
            print(f"Tagged v{version_num} as '{exp['alias_target']}'.")

        registered_versions.append({
            "version": version_num,
            "run_id": run_id,
            "alias": exp["alias_target"],
            "macro_f1": train_metadata["test_macro_f1"],
        })

    print("\n" + "=" * 70)
    print("REGISTRY SUMMARY")
    print("=" * 70)
    for rv in registered_versions:
        print(f"Version: v{rv['version']:<3} | Alias: {str(rv['alias']):<12} | Macro-F1: {rv['macro_f1']:.4f} | Run ID: {rv['run_id']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_experiment_suite()
