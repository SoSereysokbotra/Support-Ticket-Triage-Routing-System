from pathlib import Path
from typing import Any, Dict

import pandas as pd
from prefect import task

from src.infrastructure.data.dataset_loader import DatasetLoader
from src.pipelines.training.train_distilbert import train_model


@task(name="train_model_task")
def train_model_task(
    df: pd.DataFrame,
    output_dir: Path,
    learning_rate: float = 3e-5,
    num_epochs: int = 2,
    batch_size: int = 16,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Trains the DistilBERT model using stratified splits and weighted loss.
    """
    loader = DatasetLoader()
    train_df, val_df, test_df = loader.stratified_split(df, random_state=random_state)
    print(f"[TrainTask] Data split: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Train DistilBERT
    eval_results = train_model(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        output_dir=output_dir,
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
        random_state=random_state,
    )

    # Auto-export candidate to ONNX for ultra-low latency serving
    try:
        from src.pipelines.export.export_onnx import export_distilbert_to_onnx

        print(f"[TrainTask] Auto-exporting candidate model to ONNX: {output_dir / 'model.onnx'}...")
        export_distilbert_to_onnx(model_dir=output_dir)
        print("[TrainTask] Candidate ONNX export succeeded.")
    except Exception as e:
        print(f"[TrainTask] Candidate ONNX export skipped/failed: {e}")

    return {
        "model_dir": output_dir,
        "test_df": test_df,
        "params": {
            "model_architecture": "distilbert-base-uncased",
            "learning_rate": str(learning_rate),
            "num_epochs": str(num_epochs),
            "batch_size": str(batch_size),
            "loss_function": "WeightedCrossEntropyLoss",
        },
        "train_eval_results": eval_results,
    }
