#!/usr/bin/env python3
"""
סקריפט לעדכון מסד הנתונים - הוספת טבלאות חדשות ועמודות חסרות
"""

import sys
import os
import sqlite3

# הוסף את התיקייה הנוכחית ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_db, get_session, Base
from sqlalchemy import inspect

def migrate_columns(db_path='shavzak.db'):
    """הוסף עמודות חסרות לטבלאות קיימות"""
    print("\n🔄 בודק עמודות חסרות...")

    try:
        # התחבר למסד הנתונים
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # בדוק עמודות בטבלת soldier_status
        cursor.execute("PRAGMA table_info(soldier_status)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 עמודות קיימות בטבלת soldier_status: {columns}")

        columns_added = []

        # הוסף start_date אם לא קיימת
        if 'start_date' not in columns:
            print("➕ מוסיף עמודה start_date לטבלת soldier_status...")
            cursor.execute("ALTER TABLE soldier_status ADD COLUMN start_date DATE")
            columns_added.append('start_date')

        # הוסף end_date אם לא קיימת
        if 'end_date' not in columns:
            print("➕ מוסיף עמודה end_date לטבלת soldier_status...")
            cursor.execute("ALTER TABLE soldier_status ADD COLUMN end_date DATE")
            columns_added.append('end_date')

        # שמור שינויים
        conn.commit()
        conn.close()

        if columns_added:
            print(f"✅ נוספו עמודות: {columns_added}")
        else:
            print("ℹ️  כל העמודות הנדרשות כבר קיימות")

        return True

    except sqlite3.Error as e:
        print(f"❌ שגיאת SQLite בעת הוספת עמודות: {e}")
        return False
    except Exception as e:
        print(f"❌ שגיאה כללית בעת הוספת עמודות: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_database():
    """עדכן את מסד הנתונים עם טבלאות חדשות ועמודות חסרות"""
    print("🔄 מתחיל עדכון מסד הנתונים...")

    db_path = 'shavzak.db'

    # אתחל את המנוע
    engine = init_db(db_path)

    # בדוק אילו טבלאות קיימות
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print(f"📋 טבלאות קיימות: {existing_tables}")

    # צור את כל הטבלאות (זה לא ישנה טבלאות קיימות)
    Base.metadata.create_all(engine)

    # בדוק שוב אחרי היצירה
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()

    print(f"📋 טבלאות אחרי עדכון: {new_tables}")

    # בדוק אילו טבלאות נוספו
    added_tables = set(new_tables) - set(existing_tables)

    if added_tables:
        print(f"✅ נוספו טבלאות חדשות: {added_tables}")
    else:
        print("ℹ️  לא נוספו טבלאות חדשות (כל הטבלאות כבר קיימות)")

    # בדוק את העמודות בטבלאות החדשות
    if 'schedule_iterations' in new_tables:
        columns = [col['name'] for col in inspector.get_columns('schedule_iterations')]
        print(f"   📊 עמודות ב-schedule_iterations: {columns}")

    if 'feedback_history' in new_tables:
        columns = [col['name'] for col in inspector.get_columns('feedback_history')]
        print(f"   📊 עמודות ב-feedback_history: {columns}")

    # הוסף עמודות חסרות לטבלאות קיימות
    migrate_columns(db_path)

    print("\n✅ עדכון מסד הנתונים הושלם בהצלחה!")

if __name__ == '__main__':
    try:
        update_database()
    except Exception as e:
        print(f"❌ שגיאה בעדכון מסד הנתונים: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
