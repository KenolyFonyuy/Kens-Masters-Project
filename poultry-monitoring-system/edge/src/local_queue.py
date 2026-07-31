"""Durable local queue (SQLite) for unsent records with idempotency keys.

Records survive restarts. Each row has a unique idempotency_key so retries and
server-side dedup cannot create duplicates.
"""
from __future__ import annotations

import json
import sqlite3
import time


class LocalQueue:
    def __init__(self, path="edge_queue.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS outbox (
                idempotency_key TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at REAL NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                sent INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self.conn.commit()

    def enqueue(self, idempotency_key, endpoint, payload):
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO outbox(idempotency_key, endpoint, payload, created_at) VALUES (?,?,?,?)",
                (idempotency_key, endpoint, json.dumps(payload), time.time()),
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def pending(self, limit=100):
        cur = self.conn.execute(
            "SELECT idempotency_key, endpoint, payload, attempts FROM outbox WHERE sent=0 ORDER BY created_at LIMIT ?",
            (limit,),
        )
        return [
            {"idempotency_key": k, "endpoint": e, "payload": json.loads(p), "attempts": a}
            for (k, e, p, a) in cur.fetchall()
        ]

    def mark_sent(self, idempotency_key):
        self.conn.execute("UPDATE outbox SET sent=1 WHERE idempotency_key=?", (idempotency_key,))
        self.conn.commit()

    def mark_attempt(self, idempotency_key):
        self.conn.execute("UPDATE outbox SET attempts=attempts+1 WHERE idempotency_key=?", (idempotency_key,))
        self.conn.commit()

    def pending_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM outbox WHERE sent=0").fetchone()[0]

    def close(self):
        self.conn.close()
