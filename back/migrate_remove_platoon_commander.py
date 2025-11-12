"""
Migration Script: Remove is_platoon_commander column
מסיר את עמודת is_platoon_commander מהטבלה soldiers
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'shavzak.db')

def migrate_database(db_path=DB_PATH):
    """הסרת עמודת is_platoon_commander מטבלת soldiers"""
    try:
        print(f"🔧 מתחיל migration להסרת is_platoon_commander מ-{db_path}")

        if not os.path.exists(db_path):
            print(f"❌ מסד הנתונים לא נמצא: {db_path}")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # בדיקה אם העמודה קיימת
        cursor.execute("PRAGMA table_info(soldiers)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'is_platoon_commander' not in column_names:
            print("✅ העמודה is_platoon_commander כבר לא קיימת")
            conn.close()
            return True

        print("📋 העמודה is_platoon_commander נמצאה, מסיר...")

        # SQLite לא תומך ב-ALTER TABLE DROP COLUMN ישירות
        # צריך ליצור טבלה חדשה, להעתיק נתונים, ולמחוק את הישנה

        # 1. שמירת נתונים קיימים
        cursor.execute("SELECT * FROM soldiers")
        old_data = cursor.fetchall()

        # 2. קבלת מבנה הטבלה הנוכחי (ללא is_platoon_commander)
        cursor.execute("PRAGMA table_info(soldiers)")
        columns_info = cursor.fetchall()

        # 3. יצירת רשימת עמודות חדשה (ללא is_platoon_commander)
        new_columns = []
        old_columns_for_select = []

        for col in columns_info:
            col_name = col[1]
            if col_name != 'is_platoon_commander':
                col_type = col[2]
                col_notnull = col[3]
                col_default = col[4]
                col_pk = col[5]

                col_def = f"{col_name} {col_type}"
                if col_pk:
                    col_def += " PRIMARY KEY"
                if col_notnull:
                    col_def += " NOT NULL"
                if col_default is not None:
                    col_def += f" DEFAULT {col_default}"

                new_columns.append(col_def)
                old_columns_for_select.append(col_name)

        # 4. יצירת טבלה חדשה
        create_table_sql = f"""
        CREATE TABLE soldiers_new (
            {', '.join(new_columns)}
        )
        """

        cursor.execute(create_table_sql)

        # 5. העתקת נתונים (ללא is_platoon_commander)
        if old_data:
            select_columns = ', '.join(old_columns_for_select)
            placeholders = ', '.join(['?' for _ in old_columns_for_select])

            # מציאת אינדקסים של העמודות
            old_column_indices = {}
            for idx, col in enumerate(columns_info):
                old_column_indices[col[1]] = idx

            # יצירת רשימת אינדקסים לעמודות החדשות
            indices_to_copy = [old_column_indices[col_name] for col_name in old_columns_for_select]

            # העתקת שורות
            for row in old_data:
                new_row = tuple(row[i] for i in indices_to_copy)
                cursor.execute(f"INSERT INTO soldiers_new ({select_columns}) VALUES ({placeholders})", new_row)

        # 6. מחיקת טבלה ישנה ושינוי שם החדשה
        cursor.execute("DROP TABLE soldiers")
        cursor.execute("ALTER TABLE soldiers_new RENAME TO soldiers")

        conn.commit()
        print(f"✅ Migration הושלם בהצלחה! עמודת is_platoon_commander הוסרה")

        # בדיקת תקינות
        cursor.execute("PRAGMA table_info(soldiers)")
        final_columns = [col[1] for col in cursor.fetchall()]
        if 'is_platoon_commander' not in final_columns:
            print(f"✅ אימות: העמודה אכן הוסרה. עמודות קיימות: {', '.join(final_columns)}")
            conn.close()
            return True
        else:
            print("❌ שגיאה: העמודה עדיין קיימת לאחר migration")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ שגיאה במהלך migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("🗄️  Migration: הסרת is_platoon_commander")
    print("=" * 70)

    if migrate_database():
        print("\n✅ Migration הושלם בהצלחה!")
        sys.exit(0)
    else:
        print("\n❌ Migration נכשל")
        sys.exit(1)
