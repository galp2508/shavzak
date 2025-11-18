#!/usr/bin/env python3
"""
תיקון סכמת טבלת soldier_status - הוספת עמודות start_date ו-end_date

סקריפט זה פותר את השגיאה:
sqlite3.OperationalError: no such column: soldier_status.start_date

הסקריפט מוסיף את העמודות החסרות לטבלת soldier_status במסד הנתונים.
"""

import sys
import os
import sqlite3
from datetime import datetime

def fix_soldier_status_schema(db_path='shavzak.db'):
    """תיקון סכמת טבלת soldier_status"""

    print("=" * 70)
    print("🔧 תיקון סכמת טבלת soldier_status")
    print("=" * 70)
    print()

    # בדוק שמסד הנתונים קיים
    if not os.path.exists(db_path):
        print(f"❌ שגיאה: לא נמצא קובץ מסד הנתונים: {db_path}")
        print()
        print("💡 פתרונות אפשריים:")
        print(f"   1. ודא שאתה רץ בתיקייה הנכונה (צריך להיות ב-back/)")
        print(f"   2. אם מסד הנתונים נמצא במיקום אחר, העבר את הסקריפט לשם")
        print(f"   3. או הרץ עם: python fix_soldier_status_schema.py <נתיב_למסד_נתונים>")
        print()
        return False

    try:
        # גבה את מסד הנתונים
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📦 יוצר גיבוי של מסד הנתונים...")
        print(f"   {db_path} -> {backup_path}")

        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ גיבוי נוצר בהצלחה!")
        print()

        # התחבר למסד הנתונים
        print("🔌 מתחבר למסד הנתונים...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ התחברות הצליחה!")
        print()

        # בדוק את המבנה הנוכחי של הטבלה
        print("📋 בודק מבנה נוכחי של טבלת soldier_status...")
        cursor.execute("PRAGMA table_info(soldier_status)")
        columns_info = cursor.fetchall()
        columns = {col[1]: col for col in columns_info}

        print(f"   עמודות קיימות ({len(columns)}):")
        for col_name in sorted(columns.keys()):
            col_info = columns[col_name]
            col_type = col_info[2]
            print(f"      • {col_name} ({col_type})")
        print()

        # רשימת העמודות שצריכות להיות בטבלה
        required_columns = {
            'start_date': 'DATE',
            'end_date': 'DATE'
        }

        # הוסף עמודות חסרות
        columns_added = []
        columns_skipped = []

        print("🔍 בודק אילו עמודות חסרות...")
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                print(f"   ❌ עמודה חסרה: {col_name}")
                columns_added.append(col_name)
            else:
                print(f"   ✅ עמודה קיימת: {col_name}")
                columns_skipped.append(col_name)
        print()

        # הוסף את העמודות החסרות
        if columns_added:
            print(f"➕ מוסיף {len(columns_added)} עמודות חסרות...")
            for col_name in columns_added:
                col_type = required_columns[col_name]
                print(f"   • מוסיף {col_name} ({col_type})...")
                try:
                    cursor.execute(f"ALTER TABLE soldier_status ADD COLUMN {col_name} {col_type}")
                    print(f"   ✅ {col_name} נוספה בהצלחה!")
                except sqlite3.OperationalError as e:
                    print(f"   ⚠️  שגיאה בהוספת {col_name}: {e}")
            print()
        else:
            print("ℹ️  כל העמודות הנדרשות כבר קיימות - אין צורך בשינויים")
            print()

        # שמור שינויים
        if columns_added:
            print("💾 שומר שינויים...")
            conn.commit()
            print("✅ שינויים נשמרו!")
            print()

        # אמת את השינויים
        print("🔍 מאמת את השינויים...")
        cursor.execute("PRAGMA table_info(soldier_status)")
        new_columns_info = cursor.fetchall()
        new_columns = {col[1]: col for col in new_columns_info}

        print(f"   עמודות אחרי התיקון ({len(new_columns)}):")
        for col_name in sorted(new_columns.keys()):
            col_info = new_columns[col_name]
            col_type = col_info[2]
            status = "🆕" if col_name in columns_added else "  "
            print(f"      {status} {col_name} ({col_type})")
        print()

        # סגור את החיבור
        conn.close()

        # סיכום
        print("=" * 70)
        print("✅ התיקון הושלם בהצלחה!")
        print("=" * 70)
        if columns_added:
            print(f"📊 נוספו {len(columns_added)} עמודות: {', '.join(columns_added)}")
        if columns_skipped:
            print(f"ℹ️  {len(columns_skipped)} עמודות כבר היו קיימות: {', '.join(columns_skipped)}")
        print(f"📦 גיבוי נשמר ב: {backup_path}")
        print()
        print("🎯 כעת אפשר להפעיל מחדש את השרת - הבעיה אמורה להיפתר!")
        print()

        return True

    except sqlite3.Error as e:
        print(f"❌ שגיאת SQLite: {e}")
        print()
        return False
    except Exception as e:
        print(f"❌ שגיאה כללית: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # אם הועבר נתיב למסד נתונים כארגומנט, השתמש בו
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'shavzak.db'

    print()
    print("🚀 מתחיל תיקון סכמת soldier_status...")
    print(f"📁 מסד נתונים: {db_path}")
    print()

    success = fix_soldier_status_schema(db_path)

    if not success:
        print()
        print("=" * 70)
        print("❌ התיקון נכשל")
        print("=" * 70)
        print()
        print("💡 אנא בדוק את השגיאות למעלה ונסה שוב")
        print("   או פנה לתמיכה טכנית")
        print()

    sys.exit(0 if success else 1)
