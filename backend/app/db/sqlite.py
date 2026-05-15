import os
import sqlite3

from app.core.config import get_settings


def _ensure_db_dir(db_path: str) -> None:
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    _ensure_db_dir(settings.sqlite_path)
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        _create_tables(conn)
        conn.commit()
    finally:
        conn.close()


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            claim_id TEXT,
            received_at TEXT,
            claim_json TEXT,
            status TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            agent_name TEXT,
            ts_start TEXT,
            ts_end TEXT,
            status TEXT,
            latency_ms INTEGER,
            input_hash TEXT,
            output_json TEXT,
            errors TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trace_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            ts TEXT,
            node TEXT,
            event TEXT,
            details_json TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conflict_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            agent_a TEXT,
            agent_b TEXT,
            field TEXT,
            severity TEXT,
            description TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            coordination_score REAL,
            conflict_rate REAL,
            redundancy_score REAL,
            loop_risk REAL,
            latency_ms INTEGER,
            model_calls INTEGER,
            token_usage_json TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS emergence_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            ts TEXT,
            event_type TEXT,
            severity TEXT,
            details_json TEXT
        );
        """
    )
