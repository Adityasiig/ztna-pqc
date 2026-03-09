"""
database.py — SQLite persistence layer for ZTNA-PQC.

Creates/connects to `ztna.db` in the backend directory.
Tables: users, devices, audit_logs
"""

import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "ztna.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # safer concurrent writes
    return conn


def init_db():
    """Create tables and seed default data if the database is new."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username    TEXT PRIMARY KEY,
                pw_hash     TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'user'
            );

            CREATE TABLE IF NOT EXISTS devices (
                device_id       TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                os              TEXT NOT NULL,
                trusted         INTEGER NOT NULL DEFAULT 1,
                security_level  INTEGER NOT NULL DEFAULT 3
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          TEXT    NOT NULL,
                username    TEXT,
                event       TEXT    NOT NULL,
                result      TEXT    NOT NULL,
                ip          TEXT
            );
        """)

        # ── Seed users (only if table is empty) ─────────────────────────
        if not conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            def h(pw): return hashlib.sha256(pw.encode()).hexdigest()
            conn.executemany(
                "INSERT INTO users (username, pw_hash, role) VALUES (?,?,?)",
                [
                    ("admin",   h("password123"), "admin"),
                    ("analyst", h("securepass"),   "analyst"),
                ]
            )

        # ── Seed devices (only if table is empty) ────────────────────────
        if not conn.execute("SELECT 1 FROM devices LIMIT 1").fetchone():
            conn.executemany(
                "INSERT INTO devices (device_id, name, os, trusted, security_level) VALUES (?,?,?,?,?)",
                [
                    ("device01", "Admin Laptop",    "Ubuntu 24.04", 1, 5),
                    ("device02", "Analyst PC",      "Windows 11",   1, 4),
                    ("device03", "Guest Device",    "macOS 14",     0, 2),
                ]
            )


# ── User helpers ──────────────────────────────────────────────────────────────

def get_user(username: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

def add_user(username: str, password: str, role: str = "user") -> bool:
    """Returns False if username already exists."""
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, pw_hash, role) VALUES (?,?,?)",
                (username, pw_hash, role)
            )
        return True
    except sqlite3.IntegrityError:
        return False


# ── Device helpers ────────────────────────────────────────────────────────────

def get_all_devices() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM devices").fetchall()
    return [dict(r) for r in rows]

def get_device(device_id: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM devices WHERE device_id = ?", (device_id,)
        ).fetchone()

def enroll_device(device_id: str, name: str, os_name: str, security_level: int = 3) -> bool:
    """Returns False if device_id already exists."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO devices (device_id, name, os, trusted, security_level) VALUES (?,?,?,1,?)",
                (device_id, name, os_name, security_level)
            )
        return True
    except sqlite3.IntegrityError:
        return False

def remove_device(device_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
    return cur.rowcount > 0

def toggle_device_trust(device_id: str):
    """Flip trusted flag. Returns updated row dict or None."""
    dev = get_device(device_id)
    if dev is None:
        return None
    new_state = 0 if dev["trusted"] else 1
    with get_conn() as conn:
        conn.execute(
            "UPDATE devices SET trusted = ? WHERE device_id = ?",
            (new_state, device_id)
        )
    return {**dict(dev), "trusted": bool(new_state)}


# ── Audit log helpers ─────────────────────────────────────────────────────────

def write_log(event: str, result: str, username: str = None, ip: str = None):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_logs (ts, username, event, result, ip) VALUES (?,?,?,?,?)",
            (ts, username, event, result, ip)
        )

def get_audit_logs(limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# Initialise on import
init_db()
