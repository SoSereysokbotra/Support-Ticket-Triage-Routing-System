import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd


def generate_customer_parquet(
    output_path: Path,
    num_customers: int = 2000,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generates historical customer metadata records and writes to Parquet.
    Includes timestamps for point-in-time correctness joins.
    """
    random.seed(random_state)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    records = []

    # Deterministic known customers for testing
    vip_test_customers = {"CUST-1001", "CUST-1002", "CUST-1003"}
    enterprise_test_customers = {"CUST-2001", "CUST-2002"}

    for i in range(1000, 1000 + num_customers):
        cust_id = f"CUST-{i}"

        if cust_id in vip_test_customers:
            tier = 2  # Enterprise
            is_vip = True
            past_count = random.randint(25, 80)
            avg_res = round(random.uniform(1.0, 3.5), 2)
        elif cust_id in enterprise_test_customers:
            tier = 2
            is_vip = False
            past_count = random.randint(15, 45)
            avg_res = round(random.uniform(2.5, 6.0), 2)
        else:
            # General distribution
            tier = random.choices([0, 1, 2], weights=[0.65, 0.25, 0.10], k=1)[0]
            is_vip = (tier == 2) and (random.random() < 0.3)
            past_count = random.randint(1, 30) if tier > 0 else random.randint(0, 8)
            avg_res = round(random.uniform(2.0, 24.0), 2)

        # Spread timestamps over the last 90 days
        event_time = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))

        records.append({
            "customer_id": cust_id,
            "customer_tier": int(tier),
            "past_ticket_count": int(past_count),
            "avg_resolution_time_hours": float(avg_res),
            "is_vip": bool(is_vip),
            "event_timestamp": event_time,
            "created_timestamp": event_time,
        })

    df = pd.DataFrame(records)
    df.to_parquet(output_path, index=False)
    print(f"Generated {len(df)} customer records at {output_path}")
    return df


def bootstrap_feast_store() -> None:
    """
    Initializes and materializes the local Feast feature store.
    """
    from feast import FeatureStore

    features_dir = PROJECT_ROOT / "features"
    parquet_path = features_dir / "data" / "customer_features.parquet"

    print("=" * 60)
    print("PHASE 2: Bootstrapping Feast Feature Store")
    print("=" * 60)

    # 1. Generate Parquet Data
    generate_customer_parquet(parquet_path)

    # 2. Initialize FeatureStore
    store = FeatureStore(repo_path=str(features_dir))

    # 3. Apply feature definitions
    print("Applying Feast definitions to registry...")
    from features.feature_definitions import customer, customer_profile_features
    store.apply([customer, customer_profile_features])
    print("Feast schema applied successfully.")

    # 4. Materialize into SQLite Online Store
    end_date = datetime.now(timezone.utc) + timedelta(days=1)
    start_date = end_date - timedelta(days=180)
    print(f"Materializing features from {start_date.date()} to {end_date.date()} into SQLite online store...")
    store.materialize(start_date=start_date, end_date=end_date)
    print("Materialization complete. Online store is ready for real-time lookups.")


if __name__ == "__main__":
    bootstrap_feast_store()
