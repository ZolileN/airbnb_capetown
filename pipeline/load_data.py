"""
load_data.py
────────────
Loads all CSV files into the SQLite database and adds indexes.
Run this once after cloning the repo, or whenever CSVs are updated.

Usage:
    python pipeline/load_data.py
"""

import os
import sqlite3
import logging
import pandas as pd
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR  = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR  = os.path.join(BASE_DIR, "data")
DB_PATH   = os.path.join(DATA_DIR, "airbnb_capetown.db")

TABLES = {
    "listings":  os.path.join(DATA_DIR, "listings.csv"),
    "hosts":     os.path.join(DATA_DIR, "hosts.csv"),
    "calendar":  os.path.join(DATA_DIR, "calendar.csv"),
    "reviews":   os.path.join(DATA_DIR, "reviews.csv"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Loader ────────────────────────────────────────────────────────────────────

def load_table(conn: sqlite3.Connection, name: str, path: str):
    if not os.path.exists(path):
        log.warning(f"  [{name}] CSV not found: {path}")
        return
    df = pd.read_csv(path)
    df.to_sql(name, conn, if_exists="replace", index=False)
    log.info(f"  [{name}] {len(df):,} rows loaded")


def add_indexes(conn: sqlite3.Connection):
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_listings_neighbourhood ON listings(neighbourhood)",
        "CREATE INDEX IF NOT EXISTS idx_listings_host         ON listings(host_id)",
        "CREATE INDEX IF NOT EXISTS idx_listings_price        ON listings(price_zar)",
        "CREATE INDEX IF NOT EXISTS idx_calendar_listing      ON calendar(listing_id)",
        "CREATE INDEX IF NOT EXISTS idx_calendar_date         ON calendar(date)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_listing       ON reviews(listing_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_date          ON reviews(date)",
    ]
    for idx in indexes:
        conn.execute(idx)
    conn.commit()
    log.info("  Indexes created")


def main():
    log.info("══════════════════════════════════════════════")
    log.info("  Airbnb Cape Town — Database Loader")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("══════════════════════════════════════════════")

    conn = sqlite3.connect(DB_PATH)

    for name, path in TABLES.items():
        load_table(conn, name, path)

    add_indexes(conn)
    conn.close()

    size_mb = os.path.getsize(DB_PATH) / 1024 / 1024
    log.info(f"\n  Database ready: {DB_PATH}")
    log.info(f"  Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
