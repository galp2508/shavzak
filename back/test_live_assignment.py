#!/usr/bin/env python3
"""
בדיקה חיה של אלגוריתם השיבוץ - כמו שהשרת עושה
"""
import os
import sys
from datetime import datetime, timedelta

# הוסף את תיקיית back ל-path
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    init_db, get_session, Pluga, Mahlaka, Soldier,
    Certification, AssignmentTemplate, Shavzak, Assignment, AssignmentSoldier
)
from assignment_logic import AssignmentLogic

# חיבור ל-DB
DB_PATH = os.path.join(os.path.dirname(__file__), 'shavzak.db')
engine = init_db(DB_PATH)
session = get_session(engine)

print("🚀 מריץ שיבוץ אוטומטי כמו שהשרת עושה...")
print("=" * 80)

# טען את הפלוגה
pluga = session.query(Pluga).first()
if not pluga:
    print("❌ לא נמצאה פלוגה!")
    sys.exit(1)

print(f"✅ פלוגה: {pluga.name} (ID: {pluga.id})")

# בדוק אם יש שיבוצים קיימים
existing_shavzak = session.query(Shavzak).filter_by(pluga_id=pluga.id).first()
if existing_shavzak:
    print(f"\n⚠️  יש כבר שיבוץ קיים (ID: {existing_shavzak.id})")
    print(f"   תאריך התחלה: {existing_shavzak.start_date}")
    print(f"   מספר ימים: {existing_shavzak.days_count}")

    # מחק אותו לצורך הבדיקה
    session.query(AssignmentSoldier).filter(
        AssignmentSoldier.assignment_id.in_(
            session.query(Assignment.id).filter_by(shavzak_id=existing_shavzak.id)
        )
    ).delete(synchronize_session=False)
    session.query(Assignment).filter_by(shavzak_id=existing_shavzak.id).delete()
    session.delete(existing_shavzak)
    session.commit()
    print("   🗑️  מחק שיבוץ קיים לצורך הבדיקה")

# יצירת שיבוץ חדש (master shavzak)
start_date = datetime(2024, 1, 1).date()  # תאריך התחלה
master_shavzak = Shavzak(
    pluga_id=pluga.id,
    name='שיבוץ בדיקה',
    start_date=start_date,
    days_count=7,  # שבוע
    created_by=1
)
session.add(master_shavzak)
session.commit()

print(f"\n✅ נוצר שיבוץ חדש (ID: {master_shavzak.id})")
print(f"   תאריך התחלה: {master_shavzak.start_date}")
print(f"   מספר ימים: {master_shavzak.days_count}")

# טען תבניות משימות
templates = session.query(AssignmentTemplate).filter_by(pluga_id=pluga.id).all()
print(f"\n📋 נמצאו {len(templates)} תבניות משימות:")
for t in templates:
    print(f"   • {t.name} ({t.assignment_type}) - שעה {t.start_hour:02d}:00")

# טען מחלקות וחיילים
mahalkot = session.query(Mahlaka).filter_by(pluga_id=pluga.id).all()
print(f"\n👥 נמצאו {len(mahalkot)} מחלקות:")

mahalkot_data = []
for mahlaka in mahalkot:
    soldiers = session.query(Soldier).filter_by(mahlaka_id=mahlaka.id).all()

    commanders = []
    drivers = []
    regular_soldiers = []

    for soldier in soldiers:
        # טען הסמכות
        certifications = session.query(Certification).filter_by(soldier_id=soldier.id).all()
        cert_names = [c.certification_name for c in certifications]

        soldier_dict = {
            'id': soldier.id,
            'name': soldier.name,
            'role': soldier.role,
            'certifications': cert_names
        }

        if soldier.role in ['ממ', 'סמל', 'מכ']:
            commanders.append(soldier_dict)
        elif soldier.role == 'נהג':
            drivers.append(soldier_dict)
        else:
            regular_soldiers.append(soldier_dict)

    mahlaka_dict = {
        'id': mahlaka.id,
        'commanders': commanders,
        'drivers': drivers,
        'soldiers': regular_soldiers
    }
    mahalkot_data.append(mahlaka_dict)

    print(f"   • מחלקה {mahlaka.number}: {len(commanders)} מפקדים, {len(drivers)} נהגים, {len(regular_soldiers)} לוחמים")

# אתחול אלגוריתם שיבוץ
logic = AssignmentLogic(min_rest_hours=8, reuse_soldiers_for_standby=False)

# מבני נתונים למעקב
schedules = {}  # {soldier_id: [(day, start, end, task_name, mahlaka_id)]}
mahlaka_workload = {m['id']: 0 for m in mahalkot_data}

print("\n" + "=" * 80)
print("🔄 מריץ אלגוריתם שיבוץ ליום ראשון (יום 0)...")
print("=" * 80)

# שבץ כל משימה ליום 0
day = 0
assignments_created = []
failed_assignments = []

for template in templates:
    print(f"\n📌 משימה: {template.name} ({template.assignment_type})")
    print(f"   ⏰ שעה: {template.start_hour:02d}:00 - {template.start_hour + template.length_in_hours:02d}:00")

    assign_data = {
        'day': day,
        'name': template.name,
        'type': template.assignment_type,
        'start_hour': template.start_hour,
        'length_in_hours': template.length_in_hours,
        'needs_commander': template.commanders_needed,
        'needs_driver': template.drivers_needed,
        'needs_soldiers': template.soldiers_needed,
        'reuse_soldiers_for_standby': template.reuse_soldiers_for_standby,
        'requires_certification': template.requires_certification if template.requires_certification else None
    }

    # בחירת פונקציית שיבוץ
    result = None

    try:
        if template.assignment_type == 'סיור':
            result = logic.assign_patrol(assign_data, mahalkot_data, schedules, mahlaka_workload)
        elif template.assignment_type == 'שמירה':
            all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]
            result = logic.assign_guard(assign_data, all_soldiers, schedules)
        elif template.assignment_type == 'קצין תורן':
            all_commanders = [c for m in mahalkot_data for c in m['commanders']]
            result = logic.assign_duty_officer(assign_data, all_commanders, schedules)
        elif template.assignment_type == 'שלז':
            all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]
            result = logic.assign_shalaz(assign_data, all_soldiers, schedules)
        elif template.assignment_type == 'חפק גשש':
            all_people = [c for m in mahalkot_data for c in m['commanders']] + \
                        [d for m in mahalkot_data for d in m['drivers']] + \
                        [s for m in mahalkot_data for s in m['soldiers']]
            result = logic.assign_hafak_gashash(assign_data, all_people, schedules)
        elif template.assignment_type == 'חמל':
            all_people = [c for m in mahalkot_data for c in m['commanders']] + \
                        [d for m in mahalkot_data for d in m['drivers']] + \
                        [s for m in mahalkot_data for s in m['soldiers']]
            result = logic.assign_operations(assign_data, all_people, schedules)
        elif template.assignment_type == 'תורן מטבח':
            all_soldiers = [s for m in mahalkot_data for s in m['soldiers']]
            result = logic.assign_kitchen(assign_data, all_soldiers, schedules)
        else:
            print(f"   ⚠️  סוג משימה לא מוכר: {template.assignment_type}")
            failed_assignments.append(template.name)
            continue

        if result:
            # הצלחה! עדכן schedules
            assigned_people = []

            if 'commanders' in result and result['commanders']:
                for cmd_id in result['commanders']:
                    soldier = session.query(Soldier).get(cmd_id)
                    if soldier:
                        assigned_people.append(f"{soldier.name} (מפקד)")
                        if cmd_id not in schedules:
                            schedules[cmd_id] = []
                        schedules[cmd_id].append((
                            day,
                            template.start_hour,
                            template.start_hour + template.length_in_hours,
                            template.name,
                            result.get('mahlaka_id')
                        ))

            if 'drivers' in result and result['drivers']:
                for drv_id in result['drivers']:
                    soldier = session.query(Soldier).get(drv_id)
                    if soldier:
                        assigned_people.append(f"{soldier.name} (נהג)")
                        if drv_id not in schedules:
                            schedules[drv_id] = []
                        schedules[drv_id].append((
                            day,
                            template.start_hour,
                            template.start_hour + template.length_in_hours,
                            template.name,
                            result.get('mahlaka_id')
                        ))

            if 'soldiers' in result and result['soldiers']:
                for sol_id in result['soldiers']:
                    soldier = session.query(Soldier).get(sol_id)
                    if soldier:
                        assigned_people.append(f"{soldier.name} (לוחם)")
                        if sol_id not in schedules:
                            schedules[sol_id] = []
                        schedules[sol_id].append((
                            day,
                            template.start_hour,
                            template.start_hour + template.length_in_hours,
                            template.name,
                            result.get('mahlaka_id')
                        ))

            print(f"   ✅ שובץ בהצלחה:")
            for person in assigned_people:
                print(f"      • {person}")

            assignments_created.append(template.name)
        else:
            print(f"   ❌ נכשל - לא נמצא פתרון")
            failed_assignments.append(template.name)

    except Exception as e:
        print(f"   ❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
        failed_assignments.append(template.name)

# סיכום
print("\n" + "=" * 80)
print("📊 סיכום:")
print("=" * 80)

print(f"\n✅ הצלחות: {len(assignments_created)}/{len(templates)} ({len(assignments_created)/len(templates)*100:.1f}%)")
print(f"❌ כישלונות: {len(failed_assignments)}/{len(templates)}")

if failed_assignments:
    print("\n❌ משימות שנכשלו:")
    for task in failed_assignments:
        print(f"   • {task}")

if logic.warnings:
    print(f"\n⚠️  אזהרות ({len(logic.warnings)}):")
    for warning in logic.warnings:
        print(f"   • {warning}")

print("\n" + "=" * 80)
print("✨ בדיקה הושלמה!")
print("=" * 80)

session.close()
