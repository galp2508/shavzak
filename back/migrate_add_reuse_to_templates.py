import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'shavzak.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE assignment_templates ADD COLUMN reuse_soldiers_for_standby BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
