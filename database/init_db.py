"""
init_db.py — Run this once to create and seed the database.

Usage:
    python init_db.py           # create tables only
    python init_db.py --seed    # create tables + load sample data
    python init_db.py --reset   # drop and recreate everything (DEV only)
"""

import sys
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'labkit.db')
SCHEMA   = os.path.join(BASE_DIR, 'schema.sql')
SEED     = os.path.join(BASE_DIR, 'seed.sql')


def run_script(conn, path):
    with open(path, 'r') as f:
        conn.executescript(f.read())
    print(f"  [ok] Ran {os.path.basename(path)}")


def init(seed=False, reset=False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  [reset] Deleted existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    print("Creating tables...")
    run_script(conn, SCHEMA)

    if seed:
        print("Loading seed data...")
        run_script(conn, SEED)

    conn.close()
    print(f"\nDatabase ready: {DB_PATH}")

    if seed:
        verify()


def verify():
    """Print a quick row-count summary so you can confirm everything loaded."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    tables = [
        'users', 'courses', 'lab_kits', 'kit_components',
        'checkouts', 'lab_assignments', 'damage_reports', 'inventory'
    ]

    print("\n--- Row counts ---")
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<20} {count} rows")

    inv = conn.execute("SELECT * FROM inventory WHERE inventory_id = 1").fetchone()
    print(f"\n--- Inventory ---")
    print(f"  Total kits:     {inv['total_kits']}")
    print(f"  Available kits: {inv['available_kits']}")
    print(f"  Last updated:   {inv['last_updated']}")

    conn.close()


if __name__ == '__main__':
    args = sys.argv[1:]
    init(
        seed  = '--seed'  in args,
        reset = '--reset' in args
    )
