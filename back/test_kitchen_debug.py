#!/usr/bin/env python3
"""בדיקת משימת מטבח"""
import sys
sys.path.insert(0, '/home/user/shavzak/back')

from assignment_logic import AssignmentLogic

# יצירת אלגוריתם
logic = AssignmentLogic(min_rest_hours=8)

# נתונים למשימה
assign_data = {
    'day': 0,
    'name': 'מטבח',
    'type': 'תורן מטבח',
    'start_hour': 16,
    'length_in_hours': 1,
    'needs_commander': 0,
    'needs_driver': 0,
    'needs_soldiers': 3,  # 3 חיילים!!!
    'reuse_soldiers_for_standby': False
}

# חיילים דמה
all_soldiers = [
    {'id': 1, 'name': 'חייל 1', 'role': 'לוחם'},
    {'id': 2, 'name': 'חייל 2', 'role': 'לוחם'},
    {'id': 3, 'name': 'חייל 3', 'role': 'לוחם'},
    {'id': 4, 'name': 'חייל 4', 'role': 'לוחם'},
    {'id': 5, 'name': 'חייל 5', 'role': 'לוחם'},
]

schedules = {}

print(f"📋 assign_data: {assign_data}")
print(f"👥 מספר חיילים זמינים: {len(all_soldiers)}")
print(f"🎯 מספר חיילים נדרשים: {assign_data['needs_soldiers']}")

result = logic.assign_kitchen(assign_data, all_soldiers, schedules)

print(f"\n✅ תוצאה: {result}")
print(f"👥 מספר חיילים שהוקצו: {len(result.get('soldiers', []))}")

if result.get('soldiers'):
    print("\n👤 חיילים שהוקצו:")
    for sol_id in result['soldiers']:
        soldier = next((s for s in all_soldiers if s['id'] == sol_id), None)
        if soldier:
            print(f"   • {soldier['name']}")
