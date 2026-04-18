"""
Migration v4 — Adds new Tier 1 physical metric columns to assessments table.
Run: python scripts/migrate_v4.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pe_assessment.db")

MIGRATIONS = [
    "ALTER TABLE assessments ADD COLUMN push_ups INTEGER DEFAULT 0",
    "ALTER TABLE assessments ADD COLUMN squats INTEGER DEFAULT 0",
    "ALTER TABLE assessments ADD COLUMN sit_ups INTEGER DEFAULT 0",
    "ALTER TABLE assessments ADD COLUMN height_cm FLOAT DEFAULT 170.0",
    "ALTER TABLE assessments ADD COLUMN weight_kg FLOAT DEFAULT 65.0",
]


def run():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    success = 0
    skipped = 0

    for sql in MIGRATIONS:
        try:
            cursor.execute(sql)
            success += 1
            col = sql.split("ADD COLUMN")[1].strip().split()[0]
            print(f"  ✅ Added column: {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                skipped += 1
                print(f"  ⏭️  Skipped (already exists)")
            else:
                print(f"  ❌ Error: {e}")
                print(f"     SQL: {sql}")

    conn.commit()
    conn.close()
    print(f"\n✅ Migration v4 complete: {success} applied, {skipped} skipped")


if __name__ == "__main__":
    print(f"🔄 Running migration v4 on: {DB_PATH}")
    run()
