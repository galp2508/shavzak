#!/usr/bin/env python3
"""
Migration script to add is_ai_generated column to assignments table
"""

import sys
import os
import sqlite3

# הוסף את התיקייה הנוכחית ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database(db_path='shavzak.db'):
    """הוסף עמודה is_ai_generated לטבלת assignments"""
    print("🔄 מתחיל מיגרציה של טבלת assignments...")

    if not os.path.exists(db_path):
        print(f"❌ לא נמצא קובץ מסד הנתונים: {db_path}")
        print("ℹ️  אם מסד הנתונים נמצא במיקום אחר, העתק אותו לתיקייה הנוכחית")
        return False

    try:
        # התחבר למסד הנתונים
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # בדוק אילו עמודות קיימות בטבלה
        cursor.execute("PRAGMA table_info(assignments)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 עמודות קיימות בטבלת assignments: {columns}")

        # הוסף is_ai_generated אם לא קיימת
        if 'is_ai_generated' not in columns:
            print("➕ מוסיף עמודה is_ai_generated...")
            cursor.execute("ALTER TABLE assignments ADD COLUMN is_ai_generated BOOLEAN DEFAULT 0")

            # שמור שינויים
            conn.commit()

            # בדוק שוב אחרי השינויים
            cursor.execute("PRAGMA table_info(assignments)")
            new_columns = [col[1] for col in cursor.fetchall()]
            print(f"📋 עמודות אחרי המיגרציה: {new_columns}")

            print("✅ עמודה is_ai_generated נוספה בהצלחה")
        else:
            print("ℹ️  עמודה is_ai_generated כבר קיימת")

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
    success = migrate_database()
    sys.exit(0 if success else 1)
