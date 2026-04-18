"""
Migration v3 — Adds new tables and columns for comprehensive PE system upgrade.
Run: python scripts/migrate_v3.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "pe_assessment.db")

MIGRATIONS = [
    # New columns on assessments
    "ALTER TABLE assessments ADD COLUMN plank_hold_seconds FLOAT DEFAULT 0.0",
    "ALTER TABLE assessments ADD COLUMN breath_hold_seconds FLOAT DEFAULT 0.0",

    # Attendance table
    """CREATE TABLE IF NOT EXISTS attendance (
        id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES students(student_id) ON DELETE CASCADE,
        class_id VARCHAR(36) REFERENCES classes(id),
        date DATE DEFAULT CURRENT_DATE,
        status VARCHAR(10) DEFAULT 'present',
        linked_assessment_id VARCHAR(36) REFERENCES assessments(assessment_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # Teacher notes
    """CREATE TABLE IF NOT EXISTS teacher_notes (
        id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES students(student_id) ON DELETE CASCADE,
        teacher_id VARCHAR(36) REFERENCES students(student_id),
        content TEXT NOT NULL,
        category VARCHAR(30) DEFAULT 'general',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # Student goals
    """CREATE TABLE IF NOT EXISTS student_goals (
        id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES students(student_id) ON DELETE CASCADE,
        title VARCHAR(200) NOT NULL,
        target_value FLOAT,
        current_value FLOAT DEFAULT 0.0,
        metric_type VARCHAR(50),
        deadline DATE,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # Badges
    """CREATE TABLE IF NOT EXISTS badges (
        id VARCHAR(36) PRIMARY KEY,
        student_id VARCHAR(36) REFERENCES students(student_id) ON DELETE CASCADE,
        badge_type VARCHAR(50) NOT NULL,
        badge_name VARCHAR(100) NOT NULL,
        description VARCHAR(255),
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # Notifications
    """CREATE TABLE IF NOT EXISTS notifications (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) REFERENCES students(student_id) ON DELETE CASCADE,
        title VARCHAR(200) NOT NULL,
        message TEXT,
        type VARCHAR(30) DEFAULT 'info',
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",

    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_attendance_class ON attendance(class_id)",
    "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
    "CREATE INDEX IF NOT EXISTS idx_notes_student ON teacher_notes(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_goals_student ON student_goals(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_badges_student ON badges(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
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
            action = sql.strip().split()[0:3]
            print(f"  ✅ {' '.join(action)}...")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                skipped += 1
                print(f"  ⏭️  Skipped (already exists)")
            else:
                print(f"  ❌ Error: {e}")
                print(f"     SQL: {sql[:80]}...")

    conn.commit()
    conn.close()
    print(f"\n✅ Migration complete: {success} applied, {skipped} skipped")


if __name__ == "__main__":
    print(f"🔄 Running migration v3 on: {DB_PATH}")
    run()
