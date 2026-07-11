import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "venomgrid.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id TEXT PRIMARY KEY,
            name TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            antivenom_stock INTEGER,
            daily_usage_rate REAL,
            capacity INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            village TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            rainfall_mm REAL,
            vegetation_index REAL,
            historical_bites_per_year INTEGER,
            season_factor REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reported_at TEXT,
            village TEXT,
            symptoms TEXT,
            severity_score REAL,
            severity_label TEXT,
            assigned_hospital TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("DB initialized at", DB_PATH)
