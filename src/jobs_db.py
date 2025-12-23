# src/jobs_db.py
import os
import sqlite3
import json
from typing import Optional

DB_PATH = os.getenv("JOBS_DB", "jobs.db")

def _connect():
    # allow longer timeout to reduce "database is locked" failures under concurrent access
    return sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)

def init_db():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        type TEXT,
        value TEXT,
        status TEXT,
        metadata TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def create_job(job_id: str, type_: str, value: str, metadata: Optional[dict] = None):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO jobs (id, type, value, status, metadata) VALUES (?, ?, ?, ?, ?)",
        (job_id, type_, value, "queued", json.dumps(metadata or {}))
    )
    conn.commit()
    conn.close()

def update_job_status(job_id: str, status: str, metadata: Optional[dict] = None):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT metadata FROM jobs WHERE id=?", (job_id,))
    row = cur.fetchone()
    try:
        old_meta = json.loads(row[0]) if row and row[0] else {}
    except Exception:
        old_meta = {}
    if metadata:
        old_meta.update(metadata)
    cur.execute("UPDATE jobs SET status=?, metadata=? WHERE id=?", (status, json.dumps(old_meta), job_id))
    conn.commit()
    conn.close()

def get_job(job_id: str):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT id, type, value, status, metadata, created_at FROM jobs WHERE id=?", (job_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "value": row[2],
        "status": row[3],
        "metadata": json.loads(row[4] or "{}"),
        "created_at": row[5],
    }
