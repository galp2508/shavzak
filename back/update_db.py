#!/usr/bin/env python3
"""
סקריפט לעדכון מסד הנתונים - הוספת טבלאות FeedbackHistory ו-ScheduleIteration
"""

import sys
import os

# הוסף את התיקייה הנוכחית ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_db, get_session, Base
from sqlalchemy import inspect

def update_database():
    """עדכן את מסד הנתונים עם הטבלאות החדשות"""
    print("🔄 מתחיל עדכון מסד הנתונים...")

    # אתחל את המנוע
    engine = init_db('shavzak.db')

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

    print("✅ עדכון מסד הנתונים הושלם בהצלחה!")

if __name__ == '__main__':
    try:
        update_database()
    except Exception as e:
        print(f"❌ שגיאה בעדכון מסד הנתונים: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
