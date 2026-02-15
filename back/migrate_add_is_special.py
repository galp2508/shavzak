import sqlite3
import os

def migrate_database(db_path='shavzak.db'):
    """
    מוסיף את העמודה is_special לטבלת mahalkot
    """
    print(f"Starting migration for {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # בדיקה אם העמודה קיימת
        cursor.execute("PRAGMA table_info(mahalkot)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_special' not in columns:
            print("Adding 'is_special' column to 'mahalkot' table...")
            try:
                cursor.execute("ALTER TABLE mahalkot ADD COLUMN is_special BOOLEAN DEFAULT 0")
                print("Added 'is_special' column")
            except Exception as e:
                print(f"Error adding column: {e}")
                conn.close()
                return False
        else:
            print("'is_special' column already exists")
            
        conn.commit()
        conn.close()
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
