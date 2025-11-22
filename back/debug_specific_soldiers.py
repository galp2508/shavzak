
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Soldier, SoldierStatus
from config import Config
from datetime import datetime

# Setup DB connection
sys.path.append(os.getcwd())

try:
    db_path = Config.DATABASE_PATH
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), 'back', db_path)
        
    uri = f"sqlite:///{db_path}"
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()

    names_to_check = ["אגם אטל", "דוד בלאי"]
    
    print(f"--- Checking specific soldiers: {names_to_check} ---")
    
    for name in names_to_check:
        soldier = session.query(Soldier).filter(Soldier.name.like(f"%{name}%")).first()
        if soldier:
            print(f"\nFound Soldier: {soldier.name} (ID: {soldier.id})")
            print(f"  - Home Round Date: {soldier.home_round_date}")
            
            status = session.query(SoldierStatus).filter_by(soldier_id=soldier.id).first()
            if status:
                print(f"  - Status Type: '{status.status_type}'")
                print(f"  - Status Dates: {status.start_date} to {status.end_date}")
            else:
                print("  - No Status Record found (Defaults to 'In Base')")
                
            # Simulate Cycle Logic
            if soldier.home_round_date:
                check_date = datetime.now().date()
                days_diff = (check_date - soldier.home_round_date).days
                print(f"  - Days since home round: {days_diff}")
                
                # Default logic from code: 17-4 cycle
                # 0-3 = Home (Unavailable), 4-20 = Base (Available)
                cycle_position = days_diff % 21
                in_round = cycle_position < 4
                print(f"  - Cycle Position (mod 21): {cycle_position}")
                print(f"  - Is Home (Unavailable)? {in_round}")
                
                if in_round:
                    print("  -> Should be UNAVAILABLE due to cycle")
                else:
                    print("  -> Should be AVAILABLE due to cycle (currently in base part of cycle)")
            else:
                print("  - No home_round_date, cannot calculate cycle.")

        else:
            print(f"\nSoldier '{name}' not found in DB.")

except Exception as e:
    print(f"Error: {e}")
