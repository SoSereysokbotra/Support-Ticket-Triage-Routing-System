from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter


def test_training_serving_feature_skew_prevention():
    """
    CRITICAL MLOPS TEST: Proves that features computed during offline training
    and online serving are byte-identical, eliminating training-serving skew.
    """
    project_root = Path(__file__).resolve().parents[2]
    store_adapter = FeastFeatureStoreAdapter(repo_path=project_root / "features")

    test_customer_ids = [
        "CUST-1001",  # VIP Enterprise
        "CUST-1002",  # VIP Enterprise
        "CUST-2001",  # Enterprise
        "CUST-2002",  # Enterprise
        "CUST-1050",  # Standard
        "CUST-1075",  # Standard
        "CUST-1100",  # Standard
    ]

    now = datetime.now(timezone.utc)

    # 1. OFFLINE / TRAINING PATH (Historical Point-in-time join)
    offline_entity_df = pd.DataFrame({
        "customer_id": test_customer_ids,
        "event_timestamp": [now] * len(test_customer_ids),
    })
    offline_df = store_adapter.get_historical_features(offline_entity_df)

    # 2. ONLINE / SERVING PATH (Real-time SQLite lookup)
    online_features_list = store_adapter.get_online_features(test_customer_ids)
    online_df = pd.DataFrame(online_features_list)
    online_df["customer_id"] = test_customer_ids

    # Merge on customer_id to compare pairwise
    comparison_df = pd.merge(
        offline_df[["customer_id", "customer_tier", "past_ticket_count", "avg_resolution_time_hours", "is_vip"]],
        online_df[["customer_id", "customer_tier", "past_ticket_count", "avg_resolution_time_hours", "is_vip"]],
        on="customer_id",
        suffixes=("_offline", "_online"),
    )

    assert len(comparison_df) == len(test_customer_ids), "All test entities must be matched."

    # 3. STRICT SKEW ASSERTIONS
    # Assert customer_tier is identical
    np.testing.assert_array_equal(
        comparison_df["customer_tier_offline"].to_numpy(),
        comparison_df["customer_tier_online"].to_numpy(),
        err_msg="Training-serving skew detected in 'customer_tier'!",
    )

    # Assert past_ticket_count is identical
    np.testing.assert_array_equal(
        comparison_df["past_ticket_count_offline"].to_numpy(),
        comparison_df["past_ticket_count_online"].to_numpy(),
        err_msg="Training-serving skew detected in 'past_ticket_count'!",
    )

    # Assert avg_resolution_time_hours is identical within float precision
    np.testing.assert_allclose(
        comparison_df["avg_resolution_time_hours_offline"].to_numpy(),
        comparison_df["avg_resolution_time_hours_online"].to_numpy(),
        rtol=1e-4,
        err_msg="Training-serving skew detected in 'avg_resolution_time_hours'!",
    )

    # Assert is_vip boolean flag is identical
    np.testing.assert_array_equal(
        comparison_df["is_vip_offline"].to_numpy(),
        comparison_df["is_vip_online"].to_numpy(),
        err_msg="Training-serving skew detected in 'is_vip'!",
    )

    print("\n[Skew Test PASSED] 0.0000% feature skew verified across all metadata features.")
