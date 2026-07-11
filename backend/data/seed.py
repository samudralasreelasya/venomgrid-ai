"""
Run this once to create and populate the SQLite database from the
simulated CSV data.  Usage:  python backend/data/seed.py
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.db import get_connection, init_db  # noqa: E402

HERE = os.path.dirname(__file__)


def seed():
    init_db()
    conn = get_connection()

    hospitals = pd.read_csv(os.path.join(HERE, "hospitals.csv"))
    villages = pd.read_csv(os.path.join(HERE, "villages.csv"))

    hospitals.to_sql("hospitals", conn, if_exists="replace", index=False)
    villages.to_sql("villages", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()
    print(f"Seeded {len(hospitals)} hospitals and {len(villages)} villages.")


if __name__ == "__main__":
    seed()
