from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter


@pytest.fixture
def feature_store():
    project_root = Path(__file__).resolve().parents[2]
    return FeastFeatureStoreAdapter(repo_path=project_root / "features")


def test_feast_online_feature_retrieval(feature_store: FeastFeatureStoreAdapter):
    # Test known customer
    features = feature_store.get_customer_feature("CUST-1001")
    assert "customer_tier" in features
    assert "past_ticket_count" in features
    assert "avg_resolution_time_hours" in features
    assert "is_vip" in features
    assert features["is_vip"] is True  # CUST-1001 is set as VIP in generator

    # Test unknown customer fallback
    unknown_features = feature_store.get_customer_feature("CUST-UNKNOWN-999")
    assert unknown_features["customer_tier"] == 0
    assert unknown_features["is_vip"] is False


def test_feast_historical_feature_retrieval(feature_store: FeastFeatureStoreAdapter):
    entity_df = pd.DataFrame({
        "customer_id": ["CUST-1001", "CUST-2001"],
        "event_timestamp": [datetime.now(timezone.utc), datetime.now(timezone.utc)],
    })

    hist_df = feature_store.get_historical_features(entity_df)
    assert len(hist_df) == 2
    assert "customer_tier" in hist_df.columns
    assert "past_ticket_count" in hist_df.columns
    assert "is_vip" in hist_df.columns
    assert hist_df[hist_df["customer_id"] == "CUST-1001"]["is_vip"].iloc[0] == True
