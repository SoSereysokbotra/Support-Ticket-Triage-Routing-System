from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IFeatureStore(ABC):
    """
    Abstract Port (Interface) for retrieving customer profile features.
    Domain and Application layers depend ONLY on this abstraction.
    Infrastructure adapters (Feast, Redis, PostgreSQL) implement this.
    """

    @abstractmethod
    def get_online_features(self, customer_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve real-time features for a list of customer IDs."""
        pass

    @abstractmethod
    def get_customer_feature(self, customer_id: Optional[str]) -> Dict[str, Any]:
        """Retrieve real-time features for a single customer ID."""
        pass
