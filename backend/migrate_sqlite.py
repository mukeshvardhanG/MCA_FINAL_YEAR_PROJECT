import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pe_assessment.db")

def run_migrations():
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create classes table (SQLite syntax for default UUID is handled in app/models/__init__.py via Python, 
    # but for DB default we can't easily use gen_random_uuid(). Since we create classes via SQLAlchemy, 
    # the frontend will use the Python provided UUID. We just create the table without default functions.)
    print("Creating classes table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            teacher_id VARCHAR(36) REFERENCES students(student_id),
            semester VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Add class_id to students
    print("Adding class_id to students...")
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN class_id VARCHAR(36) REFERENCES classes(id);")
        print(" -> Added class_id column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(" -> class_id already exists.")
        else:
            raise e

    # Add locked to assessments
    print("Adding locked to assessments...")
    try:
        cursor.execute("ALTER TABLE assessments ADD COLUMN locked BOOLEAN DEFAULT 0;")
        print(" -> Added locked column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(" -> locked already exists.")
        else:
            raise e

    # Add locked to quiz_sessions
    print("Adding locked to quiz_sessions...")
    try:
        cursor.execute("ALTER TABLE quiz_sessions ADD COLUMN locked BOOLEAN DEFAULT 0;")
        print(" -> Added locked column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(" -> locked already exists.")
        else:
            raise e

    conn.commit()
    
    # Check if there's any user to promote to admin, for boostrapping
    cursor.execute("SELECT email FROM students LIMIT 1;")
    user = cursor.fetchone()
    if user:
        email = user[0]
        cursor.execute("UPDATE students SET role = 'admin' WHERE email = ?;", (email,))
        conn.commit()
        print(f"Bootstrapped admin account using existing email: {email}")
    else:
        print("No users found to bootstrap as admin. You will need to register a user first.")

    conn.close()
    print("Migrations complete.")

if __name__ == "__main__":
    run_migrations()
