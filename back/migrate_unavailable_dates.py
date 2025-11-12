"""
Migration script to add new fields to unavailable_dates table
הוספת שדות חדשים לטבלת תאריכי אי זמינות
"""
import sqlite3
import sys
import os

def migrate_database(db_path='shavzak.db'):
    """הוספת שדות חדשים לטבלת unavailable_dates"""

    # בדיקה שקובץ המסד נתונים קיים
    if not os.path.exists(db_path):
        print(f"שגיאה: קובץ מסד הנתונים {db_path} לא נמצא")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("מתחיל migration...")

        # בדיקה אם השדות כבר קיימים
        cursor.execute("PRAGMA table_info(unavailable_dates)")
        columns = [column[1] for column in cursor.fetchall()]

        # הוספת שדה end_date אם לא קיים
        if 'end_date' not in columns:
            print("מוסיף שדה end_date...")
            cursor.execute("""
                ALTER TABLE unavailable_dates
                ADD COLUMN end_date DATE
            """)
            print("✓ שדה end_date נוסף בהצלחה")
        else:
            print("שדה end_date כבר קיים")

        # הוספת שדה unavailability_type אם לא קיים
        if 'unavailability_type' not in columns:
            print("מוסיף שדה unavailability_type...")
            cursor.execute("""
                ALTER TABLE unavailable_dates
                ADD COLUMN unavailability_type VARCHAR(20) DEFAULT 'חופשה'
            """)
            print("✓ שדה unavailability_type נוסף בהצלחה")
        else:
            print("שדה unavailability_type כבר קיים")

        # הוספת שדה quantity אם לא קיים
        if 'quantity' not in columns:
            print("מוסיף שדה quantity...")
            cursor.execute("""
                ALTER TABLE unavailable_dates
                ADD COLUMN quantity INTEGER
            """)
            print("✓ שדה quantity נוסף בהצלחה")
        else:
            print("שדה quantity כבר קיים")

        # עדכון רשומות קיימות עם ערכי ברירת מחדל
        print("מעדכן רשומות קיימות...")
        cursor.execute("""
            UPDATE unavailable_dates
            SET unavailability_type = 'חופשה'
            WHERE unavailability_type IS NULL
        """)

        # עדכון 'חק"ש' ל'בקשת יציאה' ברשומות קיימות
        print("מעדכן חק\"ש לחק\"צ...")
        cursor.execute("""
            UPDATE unavailable_dates
            SET unavailability_type = 'בקשת יציאה'
            WHERE unavailability_type = 'חק"ש'
        """)

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
