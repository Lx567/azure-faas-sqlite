import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("SQLITE_PATH", "./data/serverless.db")

def ensure_parent():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    ensure_parent()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            sensor_id INTEGER NOT NULL,
            ts TEXT NOT NULL,
            temperature REAL NOT NULL,
            co2 REAL NOT NULL,
            humidity REAL NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            metric TEXT NOT NULL,
            min_val REAL NOT NULL,
            max_val REAL NOT NULL,
            avg_val REAL NOT NULL,
            count_val INTEGER NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            func_name TEXT NOT NULL,
            invocation_id TEXT NOT NULL,
            start_ts TEXT NOT NULL,
            end_ts TEXT NOT NULL,
            duration_ms REAL NOT NULL,
            cpu_user REAL,
            cpu_system REAL,
            rss_mb REAL,
            peak_py_mb REAL,
            extra TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS control (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn

def get_last_processed_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT v FROM control WHERE k='last_processed_id'")
    row = cur.fetchone()
    return int(row[0]) if row else 0

def set_last_processed_id(conn, last_id:int):
    cur = conn.cursor()
    cur.execute("INSERT INTO control(k, v) VALUES('last_processed_id', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v;", (str(last_id),))
    conn.commit()
