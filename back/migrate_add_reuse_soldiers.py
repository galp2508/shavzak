import sqlite3
import os

def migrate():
    # server.py calls migrate() without args, implies it knows DB_PATH?
    # No, server.py imports 'migrate' and calls it.
    # Wait, server.py defines DB_PATH globally but imports module.
    # The module needs to know the path or find it.
    # Let's check server.py again.
    # It calls: migrate()
    # So we must assume default path 'shavzak.db' relative to CWD or pass nothing.
    
    db_path = os.path.join(os.path.dirname(__file__), 'shavzak.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE shavzakim ADD COLUMN reuse_soldiers_for_standby BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
