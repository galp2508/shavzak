"""
Migration script to add hatash_2_days field to soldiers table
הוספת שדה hatash_2_days לטבלת soldiers
"""
import sqlite3
import sys
import os

def migrate_database(db_path='shavzak.db'):
    """הוספת שדה hatash_2_days לטבלת soldiers"""

    # בדיקה שקובץ המסד נתונים קיים
    if not os.path.exists(db_path):
        print(f"שגיאה: קובץ מסד הנתונים {db_path} לא נמצא")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("מתחיל migration...")

        # בדיקה אם השדה כבר קיים
        cursor.execute("PRAGMA table_info(soldiers)")
        columns = [column[1] for column in cursor.fetchall()]

        # הוספת שדה hatash_2_days אם לא קיים
        if 'hatash_2_days' not in columns:
            print("מוסיף שדה hatash_2_days...")
            cursor.execute("""
                ALTER TABLE soldiers
                ADD COLUMN hatash_2_days VARCHAR(50)
            """)
            print("✓ שדה hatash_2_days נוסף בהצלחה")
        else:
            print("שדה hatash_2_days כבר קיים")

        conn.commit()
        print("\n✓ Migration הושלם בהצלחה!")
        return True

    except Exception as e:
        print(f"\n✗ שגיאה במהלך migration: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    # שימוש באותו נתיב DB כמו בapi.py
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'shavzak.db')

    print(f"מריץ migration על: {db_path}")
    print("-" * 50)

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
