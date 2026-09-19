from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from feast import FeatureStore

from src.domain.interfaces.feature_store_interface import IFeatureStore


class FeastFeatureStoreAdapter(IFeatureStore):
    """
    Adapter for Feast Feature Store implementing IFeatureStore.
    Provides a unified interface for both offline historical training joins
    and low-latency online serving queries, preventing training-serving skew.
    """

    FEATURE_REFS = [
        "customer_profile_features:customer_tier",
        "customer_profile_features:past_ticket_count",
        "customer_profile_features:avg_resolution_time_hours",
        "customer_profile_features:is_vip",
    ]

    DEFAULT_CUSTOMER_FEATURES = {
        "customer_tier": 0,
        "past_ticket_count": 0,
        "avg_resolution_time_hours": 12.0,
        "is_vip": False,
    }

    def __init__(self, repo_path: Optional[Path] = None) -> None:
        self.repo_path = repo_path or (Path(__file__).resolve().parents[3] / "features")
        self._store: Optional[FeatureStore] = None

    @property
    def store(self) -> FeatureStore:
        if self._store is None:
            self._store = FeatureStore(repo_path=str(self.repo_path))
        return self._store

    def get_historical_features(
        self,
        entity_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Retrieves historical features for training datasets with point-in-time correctness.
        entity_df must contain 'customer_id' and 'event_timestamp'.
        """
        df = entity_df.copy()
        if "event_timestamp" not in df.columns:
            df["event_timestamp"] = datetime.now(timezone.utc)

        training_data = self.store.get_historical_features(
            entity_df=df,
            features=self.FEATURE_REFS,
        )
        result_df = training_data.to_df()

        # Fill NaNs with standard defaults for unknown customers
        for col, default_val in self.DEFAULT_CUSTOMER_FEATURES.items():
            if col in result_df.columns:
                result_df[col] = result_df[col].fillna(default_val)

        return result_df

    def get_online_features(
        self,
        customer_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real-time features for incoming tickets from the online SQLite store.
        Returns a list of feature dictionaries matching the input customer_ids order.
        """
        if not customer_ids:
            return []

        entity_rows = [{"customer_id": cid} for cid in customer_ids]
        response = self.store.get_online_features(
            features=self.FEATURE_REFS,
            entity_rows=entity_rows,
        )
        response_dict = response.to_dict()

        results: List[Dict[str, Any]] = []
        num_entities = len(customer_ids)

        for i in range(num_entities):
            feat_dict = {}
            for col in ["customer_tier", "past_ticket_count", "avg_resolution_time_hours", "is_vip"]:
                val = response_dict.get(col, [None])[i]
                if val is None or pd.isna(val):
                    val = self.DEFAULT_CUSTOMER_FEATURES[col]
                feat_dict[col] = val
            results.append(feat_dict)

        return results

    def get_customer_feature(self, customer_id: Optional[str]) -> Dict[str, Any]:
        """Convenience method for fetching features for a single customer."""
        if not customer_id:
            return dict(self.DEFAULT_CUSTOMER_FEATURES)
        features_list = self.get_online_features([customer_id])
        return features_list[0] if features_list else dict(self.DEFAULT_CUSTOMER_FEATURES)
