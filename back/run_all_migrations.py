import os
import sqlite3

def run_migration(script_name):
    print(f"\n--- Running {script_name} ---")
    try:
        # Load the script content
        with open(script_name, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Execute in a restricted scope but with access to sqlite3 and os
        # Most of these scripts likely have a `if __name__ == "__main__":` block
        # We can try to just run them using os.system or exec
        
        # Determine DB path relative to script
        db_path = 'shavzak.db' # The migration scripts usually assume same dir
        
        # We are running from 'back/' directory contexts, so scripts are in current dir
        ret = os.system(f'python {script_name}')
        if ret != 0:
            print(f"Items in {script_name} might have failed or it's not a runnable script.")
    except Exception as e:
        print(f"Error running {script_name}: {e}")

# List of migration scripts in order (approximate) - based on filename clues or just all of them
migration_scripts = [
    'migrate.py', # General migrate
    'migrate_add_hatash_2_days.py',
    'migrate_add_is_special.py',
    'migrate_add_reuse_soldiers.py',
    'migrate_add_reuse_to_templates.py',
    'migrate_add_special_to_assignments.py',
    'migrate_add_special_to_templates.py',
    'migrate_add_standby_to_templates.py',
    'migrate_add_start_hour.py',
    'migrate_remove_platoon_commander.py',
    'migrate_unavailable_dates.py'
]

if __name__ == "__main__":
    # Ensure we are in 'back' directory for this to work easily with the scripts as written
    if os.path.exists('server.py') and os.path.exists('shavzak.db'):
        print("Running in 'back' directory context.")
        for script in migration_scripts:
            if os.path.exists(script):
                run_migration(script)
            else:
                print(f"Script not found: {script}")
    else:
        print("Please run this script from the 'back' directory where 'shavzak.db' is located.")
