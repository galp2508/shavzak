import os
print("Setting environment variables...")
os.environ['SECRET_KEY'] = 'debug_key'
os.environ['DEBUG'] = 'True'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AssignmentTemplate, Base

# SQLite path from config
db_path = 'sqlite:///shavzak.db'
if os.path.exists('back/shavzak.db'):
    db_path = 'sqlite:///back/shavzak.db'

print(f"Connecting to DB at: {db_path}")
engine = create_engine(db_path)
Session = sessionmaker(bind=engine)
session = Session()

print("\n--- Checking for 'Standby' (Konenut) Templates ---")
templates = session.query(AssignmentTemplate).all()
found = False

for t in templates:
    if 'כוננות' in t.assignment_type or 'Standby' in t.assignment_type:
        found = True
        print(f"\n[Template ID: {t.id}] Name: {t.name}")
        print(f"  - Type: {t.assignment_type}")
        print(f"  - Commanders Needed: {t.commanders_needed}")
        print(f"  - Soldiers Needed: {t.soldiers_needed}")
        print(f"  - Drivers Needed: {t.drivers_needed}")
        print(f"  - Reuse Soldiers? {t.reuse_soldiers_for_standby}")
        print(f"  - Duration: {t.length_in_hours} hours")
        print(f"  - Times per day: {t.times_per_day}")

if not found:
    print("\nNo templates found with 'כוננות' or 'Standby' in type.")
    print("Available types:")
    types = set([t.assignment_type for t in templates])
    for type_name in types:
        print(f"  - {type_name}")

print("\nDone.")
