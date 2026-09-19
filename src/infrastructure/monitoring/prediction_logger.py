"""
Prediction Logger Infrastructure
Asynchronously and persistently logs incoming inference requests, predictions,
customer metadata, and latency metrics to a dedicated SQLite store.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DEFAULT_MONITORING_DB_PATH = Path("data/monitoring/inference_logs.db")


class PredictionLogger:
    """
    Lightweight, thread-safe inference logger using SQLite in WAL mode for
    high-concurrency, low-latency writes.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or DEFAULT_MONITORING_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS inference_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        text TEXT NOT NULL,
                        text_length INTEGER NOT NULL,
                        word_count INTEGER NOT NULL,
                        predicted_category TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        probabilities_json TEXT,
                        latency_ms REAL NOT NULL,
                        customer_id TEXT,
                        customer_tier TEXT,
                        is_vip INTEGER,
                        model_version TEXT
                    );
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON inference_logs(timestamp);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_logs_category ON inference_logs(predicted_category);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_logs_customer ON inference_logs(customer_id);"
                )
                conn.commit()

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
        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        text_len = len(text)
        word_cnt = len(text.split())
        probs_json = json.dumps(probabilities or {})
        vip_int = 1 if is_vip else 0 if is_vip is not None else None

        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO inference_logs (
                        ticket_id, timestamp, text, text_length, word_count,
                        predicted_category, confidence, probabilities_json,
                        latency_ms, customer_id, customer_tier, is_vip, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        ticket_id,
                        ts,
                        text,
                        text_len,
                        word_cnt,
                        predicted_category,
                        float(confidence),
                        probs_json,
                        float(latency_ms),
                        customer_id,
                        customer_tier,
                        vip_int,
                        model_version,
                    ),
                )
                conn.commit()

    def log_batch(self, records: List[Dict[str, Any]]) -> None:
        """Batch insert for high-throughput prediction logs."""
        if not records:
            return

        rows = []
        for r in records:
            ts = (r.get("timestamp") or datetime.now(timezone.utc))
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            txt = r.get("text", "")
            probs_json = json.dumps(r.get("probabilities", {}))
            vip_val = r.get("is_vip")
            vip_int = 1 if vip_val else 0 if vip_val is not None else None

            rows.append(
                (
                    r.get("ticket_id", "unknown"),
                    ts_str,
                    txt,
                    len(txt),
                    len(txt.split()),
                    r.get("predicted_category", "Unknown"),
                    float(r.get("confidence", 0.0)),
                    probs_json,
                    float(r.get("latency_ms", 0.0)),
                    r.get("customer_id"),
                    r.get("customer_tier"),
                    vip_int,
                    r.get("model_version"),
                )
            )

        with self._lock:
            with self._get_connection() as conn:
                conn.executemany(
                    """
                    INSERT INTO inference_logs (
                        ticket_id, timestamp, text, text_length, word_count,
                        predicted_category, confidence, probabilities_json,
                        latency_ms, customer_id, customer_tier, is_vip, model_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    rows,
                )
                conn.commit()

    def get_recent_logs(
        self,
        limit: int = 1000,
        since_timestamp: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Fetches recent prediction records as a pandas DataFrame."""
        query = "SELECT * FROM inference_logs"
        params: List[Any] = []

        if since_timestamp:
            query += " WHERE timestamp >= ?"
            params.append(since_timestamp.isoformat())

        query += " ORDER BY id DESC LIMIT ?;"
        params.append(limit)

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        if not df.empty and "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("id", ascending=True).reset_index(drop=True)

        return df

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates live summary KPIs across logged inference traffic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), AVG(confidence), AVG(latency_ms) FROM inference_logs;")
            total_count, avg_conf, avg_lat = cursor.fetchone()

            if total_count == 0:
                return {
                    "total_requests": 0,
                    "avg_confidence": 0.0,
                    "avg_latency_ms": 0.0,
                    "category_distribution": {},
                }

            cursor.execute(
                """
                SELECT predicted_category, COUNT(*)
                FROM inference_logs
                GROUP BY predicted_category;
                """
            )
            cat_dist = dict(cursor.fetchall())

        return {
            "total_requests": int(total_count),
            "avg_confidence": round(float(avg_conf or 0.0), 4),
            "avg_latency_ms": round(float(avg_lat or 0.0), 2),
            "category_distribution": cat_dist,
        }

    def clear_logs(self) -> None:
        """Clears all logged records (used for isolated testing)."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM inference_logs;")
                conn.commit()
