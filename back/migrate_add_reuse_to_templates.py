"""
Migration: הוסף עמודת reuse_soldiers_for_standby לטבלת assignment_templates
"""
import sqlite3

def migrate():
    """מוסיף עמודת reuse_soldiers_for_standby לטבלת assignment_templates"""
    try:
        conn = sqlite3.connect('shavzak.db')
        cursor = conn.cursor()

        # בדוק אם העמודה כבר קיימת
        cursor.execute("PRAGMA table_info(assignment_templates)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'reuse_soldiers_for_standby' not in columns:
            print("מוסיף עמודה reuse_soldiers_for_standby לטבלת assignment_templates...")

            # הוספת העמודה
            cursor.execute("""
                ALTER TABLE assignment_templates
                ADD COLUMN reuse_soldiers_for_standby BOOLEAN DEFAULT 0
            """)

            conn.commit()
            print("✅ העמודה reuse_soldiers_for_standby נוספה בהצלחה לטבלת assignment_templates")
        else:
            print("✅ העמודה reuse_soldiers_for_standby כבר קיימת בטבלת assignment_templates")

        conn.close()

    except Exception as e:
        print(f"❌ שגיאה במהלך המיגרציה: {e}")
        raise

if __name__ == '__main__':
    migrate()
