"""
Migration: הוסף עמודת reuse_soldiers_for_standby לטבלת shavzakim
"""
import sqlite3

def migrate():
    """מוסיף עמודת reuse_soldiers_for_standby לטבלת shavzakim"""

    conn = sqlite3.connect('shavzak.db')
    cursor = conn.cursor()

    try:
        # בדוק אם העמודה כבר קיימת
        cursor.execute("PRAGMA table_info(shavzakim)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'reuse_soldiers_for_standby' not in columns:
            print("מוסיף עמודה reuse_soldiers_for_standby...")
            cursor.execute("""
                ALTER TABLE shavzakim
                ADD COLUMN reuse_soldiers_for_standby BOOLEAN DEFAULT 0
            """)
            conn.commit()
            print("✅ עמודה נוספה בהצלחה")
        else:
            print("✅ העמודה כבר קיימת")

    except Exception as e:
        print(f"❌ שגיאה: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
