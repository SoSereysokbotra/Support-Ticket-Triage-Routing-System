"""
Prediction Logger Infrastructure
Logs incoming inference requests, predictions, customer metadata, and latency metrics
to either PostgreSQL (for high-concurrency production clusters) or SQLite (for local development).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
    func,
    select,
)

DEFAULT_MONITORING_DB_PATH = Path("data/monitoring/inference_logs.db")


class PredictionLogger:
    """
    Thread-safe, enterprise inference telemetry logger supporting PostgreSQL
    (with connection pooling) and SQLite (with WAL mode fallback).
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        db_url: Optional[str] = None,
    ) -> None:
        self._lock = threading.Lock()
        self.db_path: Optional[Path] = None

        env_url = os.getenv("POSTGRES_DB_URL") or os.getenv("DATABASE_URL")
        resolved_url = db_url or env_url

        if resolved_url:
            self.db_url = resolved_url
            self.is_postgres = self.db_url.startswith("postgres")
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                future=True,
            )
        else:
            self.db_path = Path(db_path or DEFAULT_MONITORING_DB_PATH)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db_url = f"sqlite:///{self.db_path.as_posix()}"
            self.is_postgres = False
            self.engine = create_engine(
                self.db_url,
                connect_args={"timeout": 20.0},
                future=True,
            )

            @event.listens_for(self.engine, "connect")
            def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.close()

        self._metadata = MetaData()
        self.logs_table = Table(
            "inference_logs",
            self._metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("ticket_id", String(100), nullable=False),
            Column("timestamp", DateTime(timezone=True), nullable=False),
            Column("text", Text, nullable=False),
            Column("text_length", Integer, nullable=False),
            Column("word_count", Integer, nullable=False),
            Column("predicted_category", String(100), nullable=False),
            Column("confidence", Float, nullable=False),
            Column("probabilities_json", Text, nullable=True),
            Column("latency_ms", Float, nullable=False),
            Column("customer_id", String(100), nullable=True),
            Column("customer_tier", String(50), nullable=True),
            Column("is_vip", Integer, nullable=True),
            Column("model_version", String(100), nullable=True),
            Index("idx_logs_timestamp", "timestamp"),
            Index("idx_logs_category", "predicted_category"),
            Index("idx_logs_customer", "customer_id"),
        )
        self._init_db()

    def _init_db(self) -> None:
        """Initializes tables and indexes idempotently."""
        with self._lock:
            self._metadata.create_all(self.engine)

    def log_prediction(
        self,
        ticket_id: str,
        text: str,
        predicted_category: str,
        confidence: float,
        latency_ms: float,
        probabilities: Optional[Dict[str, float]] = None,
        customer_id: Optional[str] = None,
        customer_tier: Optional[str] = None,
        is_vip: Optional[bool] = None,
        model_version: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Logs a single inference prediction record."""
        ts = timestamp or datetime.now(timezone.utc)
        text_len = len(text)
        word_cnt = len(text.split())
        probs_json = json.dumps(probabilities or {})
        vip_int = 1 if is_vip else 0 if is_vip is not None else None

        record = {
            "ticket_id": ticket_id,
            "timestamp": ts,
            "text": text,
            "text_length": text_len,
            "word_count": word_cnt,
            "predicted_category": predicted_category,
            "confidence": float(confidence),
            "probabilities_json": probs_json,
            "latency_ms": float(latency_ms),
            "customer_id": customer_id,
            "customer_tier": customer_tier,
            "is_vip": vip_int,
            "model_version": model_version,
        }

        with self._lock:
            with self.engine.begin() as conn:
                conn.execute(self.logs_table.insert(), [record])

    def log_batch(self, records: List[Dict[str, Any]]) -> None:
        """Batch insert for high-throughput prediction logs."""
        if not records:
            return

        rows: List[Dict[str, Any]] = []
        for r in records:
            ts = r.get("timestamp") or datetime.now(timezone.utc)
            txt = r.get("text", "")
            probs_json = json.dumps(r.get("probabilities", {}))
            vip_val = r.get("is_vip")
            vip_int = 1 if vip_val else 0 if vip_val is not None else None

            rows.append(
                {
                    "ticket_id": r.get("ticket_id", "unknown"),
                    "timestamp": ts,
                    "text": txt,
                    "text_length": len(txt),
                    "word_count": len(txt.split()),
                    "predicted_category": r.get("predicted_category", "Unknown"),
                    "confidence": float(r.get("confidence", 0.0)),
                    "probabilities_json": probs_json,
                    "latency_ms": float(r.get("latency_ms", 0.0)),
                    "customer_id": r.get("customer_id"),
                    "customer_tier": r.get("customer_tier"),
                    "is_vip": vip_int,
                    "model_version": r.get("model_version"),
                }
            )

        with self._lock:
            with self.engine.begin() as conn:
                conn.execute(self.logs_table.insert(), rows)

    def get_recent_logs(
        self,
        limit: int = 1000,
        since_timestamp: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Fetches recent prediction records as a pandas DataFrame."""
        stmt = select(self.logs_table)
        if since_timestamp:
            stmt = stmt.where(self.logs_table.c.timestamp >= since_timestamp)
        stmt = stmt.order_by(self.logs_table.c.id.desc()).limit(limit)

        with self.engine.connect() as conn:
            df = pd.read_sql_query(stmt, conn)

        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("id", ascending=True).reset_index(drop=True)

        return df

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates live summary KPIs across logged inference traffic."""
        with self.engine.connect() as conn:
            agg_stmt = select(
                func.count(self.logs_table.c.id),
                func.avg(self.logs_table.c.confidence),
                func.avg(self.logs_table.c.latency_ms),
            )
            total_count, avg_conf, avg_lat = conn.execute(agg_stmt).fetchone()

            if not total_count or total_count == 0:
                return {
                    "total_requests": 0,
                    "avg_confidence": 0.0,
                    "avg_latency_ms": 0.0,
                    "category_distribution": {},
                }

            cat_stmt = select(
                self.logs_table.c.predicted_category,
                func.count(self.logs_table.c.id),
            ).group_by(self.logs_table.c.predicted_category)
            cat_dist = dict(conn.execute(cat_stmt).fetchall())

        return {
            "total_requests": int(total_count),
            "avg_confidence": round(float(avg_conf or 0.0), 4),
            "avg_latency_ms": round(float(avg_lat or 0.0), 2),
            "category_distribution": cat_dist,
        }

    def clear_logs(self) -> None:
        """Clears all logged records (used for isolated testing)."""
        with self._lock:
            with self.engine.begin() as conn:
                conn.execute(self.logs_table.delete())
