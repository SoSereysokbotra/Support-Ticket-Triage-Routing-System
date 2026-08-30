from datetime import timedelta
from pathlib import Path

from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Bool, Float32, Int64

# 1. Define Entity
customer = Entity(
    name="customer_id",
    value_type=ValueType.STRING,
    description="Unique identifier for the customer or internal employee",
    join_keys=["customer_id"],
)

# 2. Define File Data Source
# Use relative path from the features/ directory or absolute
features_dir = Path(__file__).resolve().parent
parquet_path = (features_dir / "data" / "customer_features.parquet").as_posix()

customer_source = FileSource(
    name="customer_features_source",
    path=parquet_path,
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# 3. Define Batch Feature View (Single Source of Truth)
customer_profile_features = FeatureView(
    name="customer_profile_features",
    entities=[customer],
    ttl=timedelta(days=365),
    schema=[
        Field(name="customer_tier", dtype=Int64, description="0=Standard, 1=Premium, 2=Enterprise"),
        Field(name="past_ticket_count", dtype=Int64, description="Total historical tickets filed"),
        Field(name="avg_resolution_time_hours", dtype=Float32, description="Average resolution time in hours"),
        Field(name="is_vip", dtype=Bool, description="VIP account priority flag"),
    ],
    online=True,
    source=customer_source,
    tags={"team": "triage_mlops", "tier": "tier_1"},
)
