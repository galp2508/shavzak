import sqlite3
import os

def migrate_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE unavailable_dates ADD COLUMN end_date DATE")
        except sqlite3.OperationalError:
            pass # Already exists
            
        try:
            cursor.execute("ALTER TABLE unavailable_dates ADD COLUMN unavailability_type TEXT DEFAULT 'חופשה'")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE unavailable_dates ADD COLUMN quantity INTEGER")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
