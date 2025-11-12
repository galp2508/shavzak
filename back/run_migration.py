#!/usr/bin/env python3
"""
Quick migration runner for fixing unavailable_dates schema
מריץ migration לתיקון סכימת unavailable_dates
"""
import os
import sys

# הוספת נתיב התיקייה הנוכחית
sys.path.insert(0, os.path.dirname(__file__))

from migrate_unavailable_dates import migrate_database

def main():
    """Run the migration"""
    # שימוש באותו נתיב DB כמו בapi.py
    db_path = os.path.join(os.path.dirname(__file__), 'shavzak.db')

    print("=" * 70)
    print("🔧 Shavzak - Database Migration")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print()

    if not os.path.exists(db_path):
        print("❌ שגיאה: קובץ מסד הנתונים לא נמצא")
        print(f"   נתיב: {db_path}")
        print("\nהאם יצרת את מסד הנתונים? הרץ:")
        print("   python setup.py")
        return False

    success = migrate_database(db_path)

    print("\n" + "=" * 70)
    if success:
        print("✅ Migration הושלם בהצלחה!")
        print("\nכעת ניתן להפעיל את השרת:")
        print("   python api.py")
    else:
        print("❌ Migration נכשל - בדוק את השגיאות למעלה")
    print("=" * 70)

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
