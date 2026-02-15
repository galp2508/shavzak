import sqlite3

def migrate_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE assignment_templates ADD COLUMN start_hour INTEGER")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
