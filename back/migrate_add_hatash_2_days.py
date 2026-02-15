import sqlite3

def migrate_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE soldiers ADD COLUMN hatash_2_days TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
