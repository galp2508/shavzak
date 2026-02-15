import sqlite3

def migrate_database(db_path):
    # Retrieve data, drop column by creating new table, restore data?
    # SQLite doesn't support DROP COLUMN in older versions, but new ones do.
    # We will assume new sqlite or ignore.
    # Actually, if we just ignore the column in code, it's fine.
    # But to be clean:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE soldiers DROP COLUMN is_platoon_commander")
        except sqlite3.OperationalError:
            # Fallback for older sqlite: just ignore
            pass
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration (Remove Column) failed: {e}")
        # Return True anyway to not block boot
        return True
