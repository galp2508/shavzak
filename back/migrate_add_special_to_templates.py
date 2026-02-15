import sqlite3
import os

def migrate_database(db_path='shavzak.db'):
    """
    מוסיף את העמודה requires_special_mahlaka לטבלת assignment_templates
    """
    print(f"Starting migration for {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # בדיקה אם העמודה קיימת
        cursor.execute("PRAGMA table_info(assignment_templates)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'requires_special_mahlaka' not in columns:
            print("Adding 'requires_special_mahlaka' column to 'assignment_templates' table...")
            try:
                cursor.execute("ALTER TABLE assignment_templates ADD COLUMN requires_special_mahlaka BOOLEAN DEFAULT 0")
                print("Added 'requires_special_mahlaka' column")
            except Exception as e:
                print(f"Error adding column: {e}")
                conn.close()
                return False
        else:
            print("'requires_special_mahlaka' column already exists")
            
        conn.commit()
        conn.close()
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
