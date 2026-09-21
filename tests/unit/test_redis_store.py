"""
Unit Tests for Redis-backed FeastFeatureStoreAdapter configuration
"""

from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter


def test_feast_adapter_redis_configuration():
    """Verifies FeastFeatureStoreAdapter configures Redis when parameters are passed."""
    adapter = FeastFeatureStoreAdapter(redis_host="test-redis.internal", redis_port=6379)

    assert adapter.is_redis is True
    assert adapter.redis_host == "test-redis.internal"
    assert adapter.redis_port == 6379

    # Verify Feast repo_config reflects redis online_store
    store = adapter.store
    assert store.config.online_store.type == "redis"
    assert store.config.online_store.connection_string == "test-redis.internal:6379"


def test_feast_adapter_default_sqlite_fallback():
    """Verifies FeastFeatureStoreAdapter falls back to SQLite when no redis is configured."""
    adapter = FeastFeatureStoreAdapter(redis_host=None)

    assert adapter.is_redis is False
    store = adapter.store
    assert store.config.online_store.type == "sqlite"
