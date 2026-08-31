from pathlib import Path
from typing import Optional

import pandas as pd
from prefect import task

from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter
from src.infrastructure.features.feature_generator import bootstrap_feast_store


@task(name="compute_features_task")
def compute_features_task(
    df: pd.DataFrame,
    features_repo_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Computes or retrieves point-in-time features from Feast offline store
    and ensures online store is synchronized.
    """
    project_root = Path(__file__).resolve().parents[4]
    repo_path = features_repo_path or (project_root / "features")

    # If customer features parquet does not exist, bootstrap it
    parquet_path = repo_path / "data" / "customer_features.parquet"
    if not parquet_path.exists():
        print("[ComputeFeaturesTask] Bootstrapping Feast store...")
        bootstrap_feast_store()

    adapter = FeastFeatureStoreAdapter(repo_path=repo_path)

    # Attach customer_ids if not in dataset
    df_features = df.copy()
    if "customer_id" not in df_features.columns:
        # Default mock customer mapping for training
        df_features["customer_id"] = [f"CUST-{1000 + (i % 2000)}" for i in range(len(df_features))]

    enriched_df = adapter.get_historical_features(df_features)
    print(f"[ComputeFeaturesTask] Enriched {len(enriched_df)} training samples with Feast customer features.")
    return enriched_df
