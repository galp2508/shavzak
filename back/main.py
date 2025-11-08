
import pluga
from datetime import datetime, timedelta
import sqlite3

db_name = "pluga_database.db"

def main():
    table_name = input("please enter your pluga name: ")
    try:
        # Connect to the SQLite database. If the file doesn't exist, it will be created.
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        # SQL query to check for table existence in SQLite
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        cursor.execute(query, (table_name,))
        
        result = cursor.fetchone()

        if result:
            pass
        else:
            print("here we go to create the table")
            query = f'''CREATE TABLE {table_name} (
                            key INTEGER PRIMARY KEY AUTOINCREMENT,
                            mahalka_number INTEGER,
                            name TEXT,
                            idf_id INTEGER,
                            kita TEXT,
                            id TEXT,
                            role TEXT,
                            sex TEXT,
                            phone_number TEXT,
                            address TEXT,
                            emergency_contact_name TEXT,
                            emergency_contact_number TEXT,
                            pakal TEXT,
                            birth_date TEXT,
                            recruit_date TEXT,
                            home_round TEXT
                        );'''
            cursor.execute(query)
            conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()

    my_pluga = pluga.pluga(name="פלוגה ב", gdud="פנתר", color="#BF092F", number_of_mahalkha=1)

if __name__ == "__main__":
    main()