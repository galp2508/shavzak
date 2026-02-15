import sys
import os

# Ensuring we can import from back
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'back'))

try:
    from back.smart_scheduler import SmartScheduler
except ImportError:
    from smart_scheduler import SmartScheduler

print("Initializing Scheduler...")
scheduler = SmartScheduler(min_rest_hours=8) # Using 8 hours as min rest for strict check

# Dummy Soldiers
soldiers = [
    {
        'id': 1, 'name': 'Soldier 1', 'role': 'לוחם', 'mahlaka_id': 1, 
        'certifications': [], 'unavailable_dates': []
    },
    {
        'id': 2, 'name': 'Soldier 2', 'role': 'לוחם', 'mahlaka_id': 1,
        'certifications': [], 'unavailable_dates': []
    }
]

# Schedule state
schedules = {1: [], 2: []}
mahlaka_workload = {1: 0}

# 1. Assign Guard Task (0:00 - 8:00)
print("\n--- Assigning Guard Task (0-8) ---")
guard_task = {
    'name': 'Guard', 'type': 'שמירה', 'day': 0, 'start_hour': 0, 'length_in_hours': 8,
    'soldiers_needed': 2, 'commanders_needed': 0
}
# Manually assigning to simulate previous assignments
schedules[1].append((0, 0, 8, 'Guard', 'שמירה'))
schedules[2].append((0, 0, 8, 'Guard', 'שמירה'))
print("Assigned Soldier 1 and 2 to Guard (0-8)")

# 2. Try Assign Standby Task (8:00 - 16:00)
print("\n--- Attempting Standby Task (8-16) with Reuse=True ---")
standby_task = {
    'name': 'Konenut', 'type': 'כוננות א', 'day': 0, 'start_hour': 8, 'length_in_hours': 8,
    'soldiers_needed': 2, 'commanders_needed': 0, 'drivers_needed': 0,
    'reuse_soldiers_for_standby': True, # Crucial flag
    'same_mahlaka_required': False
}

# We need to test if they are considered available
# We can use _assign_standby_a directly or get_available_soldiers_with_fallback
# But since smart_scheduler is a class, we need to access its methods properly.

# Let's verify via get_available_soldiers_with_fallback directly first
print("Checking availability via get_available_soldiers_with_fallback...")
available = scheduler.get_available_soldiers_with_fallback(soldiers, standby_task, schedules)
print(f"Available soldiers count: {len(available)}")
if len(available) == 2:
    print("SUCCESS: Soldiers are available for Standby immediately after Guard.")
else:
    print("FAILURE: Soldiers are NOT available. Rest constraint likely blocked them.")

# Also test assign_task just in case
print("\nRunning full assign_task...")
result = scheduler._assign_standby_a(standby_task, soldiers, schedules, mahlaka_workload)
if result:
    print("SUCCESS: Assignment created.")
else:
    print("FAILURE: Assignment returned None.")
