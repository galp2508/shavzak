"""
Migration: הוסף עמודת start_hour לטבלת assignment_templates
"""
import sqlite3

def migrate_database(db_path):
    """מוסיף עמודת start_hour לטבלת assignment_templates"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # בדוק אם העמודה כבר קיימת
        cursor.execute("PRAGMA table_info(assignment_templates)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'start_hour' not in columns:
            print("  ➕ מוסיף עמודה start_hour...")
            cursor.execute("""
                ALTER TABLE assignment_templates
                ADD COLUMN start_hour INTEGER
            """)
            conn.commit()
            print("  ✅ עמודת start_hour נוספה בהצלחה")
        else:
            print("  ℹ️  עמודת start_hour כבר קיימת")

        conn.close()
        return True

    except Exception as e:
        print(f"  ❌ שגיאה ב-migration: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False


if __name__ == '__main__':
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'shavzak.db')
    migrate_database(db_path)
