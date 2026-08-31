from pathlib import Path
from typing import Optional

import pandas as pd
from prefect import task

from src.infrastructure.data.dataset_loader import DatasetLoader


@task(name="ingest_ticket_data", retries=2, retry_delay_seconds=5)
def ingest_data_task(
    data_path: Optional[Path] = None,
    num_samples: int = 1200,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Ingests ticket data from a specified file path or generates a synthetic dataset
    with realistic distributions.
    """
    loader = DatasetLoader()
    if data_path and Path(data_path).exists():
        path = Path(data_path)
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path)
        print(f"[IngestTask] Loaded {len(df)} records from {data_path}")
    else:
        df = loader.load_or_create_dataset(num_samples=num_samples, random_state=random_state)
        print(f"[IngestTask] Ingested {len(df)} synthetic records for retraining")

    return df
