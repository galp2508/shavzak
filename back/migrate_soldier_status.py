#!/usr/bin/env python3
"""
Migration script to add start_date and end_date columns to soldier_status table
"""

import sys
import os
import sqlite3

# הוסף את התיקייה הנוכחית ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_soldier_status():
    """הוסף עמודות start_date ו-end_date לטבלת soldier_status"""
    print("🔄 מתחיל מיגרציה של טבלת soldier_status...")

    db_path = 'shavzak.db'

    if not os.path.exists(db_path):
        print(f"❌ לא נמצא קובץ מסד הנתונים: {db_path}")
        print("ℹ️  אם מסד הנתונים נמצא במיקום אחר, העתק אותו לתיקייה הנוכחית")
        return False

    try:
        # התחבר למסד הנתונים
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # בדוק אילו עמודות קיימות בטבלה
        cursor.execute("PRAGMA table_info(soldier_status)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 עמודות קיימות בטבלת soldier_status: {columns}")

        columns_added = []

        # הוסף start_date אם לא קיימת
        if 'start_date' not in columns:
            print("➕ מוסיף עמודה start_date...")
            cursor.execute("ALTER TABLE soldier_status ADD COLUMN start_date DATE")
            columns_added.append('start_date')
        else:
            print("ℹ️  עמודה start_date כבר קיימת")

        # הוסף end_date אם לא קיימת
        if 'end_date' not in columns:
            print("➕ מוסיף עמודה end_date...")
            cursor.execute("ALTER TABLE soldier_status ADD COLUMN end_date DATE")
            columns_added.append('end_date')
        else:
            print("ℹ️  עמודה end_date כבר קיימת")

        # שמור שינויים
        conn.commit()

        # בדוק שוב אחרי השינויים
        cursor.execute("PRAGMA table_info(soldier_status)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 עמודות אחרי המיגרציה: {new_columns}")

        if columns_added:
            print(f"✅ נוספו עמודות: {columns_added}")
        else:
            print("ℹ️  לא היה צורך להוסיף עמודות - כל העמודות כבר קיימות")

        conn.close()
        print("✅ מיגרציה הושלמה בהצלחה!")
        return True

    except sqlite3.Error as e:
        print(f"❌ שגיאת SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ שגיאה כללית: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate_soldier_status()
    sys.exit(0 if success else 1)
