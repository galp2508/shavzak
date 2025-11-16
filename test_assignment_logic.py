#!/usr/bin/env python3
"""
בדיקת אלגוריתם השיבוץ עם הנתונים של המשתמש
"""
import sys
sys.path.append('/home/user/shavzak/back')

from assignment_logic import AssignmentLogic

# נתוני תבניות משימות
assignment_templates = [
    {'id': 1, 'pluga_id': 1, 'name': 'ש"ג', 'type': 'שמירה', 'start_hour': 4, 'length_in_hours': 6,
     'needs_commander': 0, 'needs_driver': 0, 'needs_soldiers': 1, 'reuse_soldiers_for_standby': 0},
    {'id': 2, 'pluga_id': 1, 'name': 'דורס 41', 'type': 'סיור', 'start_hour': 8, 'length_in_hours': 3,
     'needs_commander': 1, 'needs_driver': 1, 'needs_soldiers': 2, 'reuse_soldiers_for_standby': 0},
    {'id': 3, 'pluga_id': 1, 'name': 'דורס 42', 'type': 'סיור', 'start_hour': 8, 'length_in_hours': 3,
     'needs_commander': 1, 'needs_driver': 1, 'needs_soldiers': 2, 'reuse_soldiers_for_standby': 1},
    {'id': 6, 'pluga_id': 1, 'name': 'קצין תורן', 'type': 'קצין תורן', 'start_hour': 8, 'length_in_hours': 3,
     'needs_commander': 1, 'needs_driver': 0, 'needs_soldiers': 0, 'reuse_soldiers_for_standby': 0},
    {'id': 8, 'pluga_id': 1, 'name': 'שלז', 'type': 'שלז', 'start_hour': 14, 'length_in_hours': 1,
     'needs_commander': 0, 'needs_driver': 0, 'needs_soldiers': 1, 'reuse_soldiers_for_standby': 0},
    {'id': 11, 'pluga_id': 1, 'name': 'דורס 43', 'type': 'סיור', 'start_hour': 8, 'length_in_hours': 3,
     'needs_commander': 1, 'needs_driver': 1, 'needs_soldiers': 2, 'reuse_soldiers_for_standby': 1},
    {'id': 12, 'pluga_id': 1, 'name': 'חפק גשש', 'type': 'חפק גשש', 'start_hour': 24, 'length_in_hours': 1,
     'needs_commander': 0, 'needs_driver': 0, 'needs_soldiers': 1, 'reuse_soldiers_for_standby': 0},
    {'id': 13, 'pluga_id': 1, 'name': 'חמל', 'type': 'חמל', 'start_hour': 12, 'length_in_hours': 2,
     'needs_commander': 0, 'needs_driver': 0, 'needs_soldiers': 1, 'reuse_soldiers_for_standby': 0,
     'certification_required': 'חמליסט'},
    {'id': 15, 'pluga_id': 1, 'name': 'מטבח', 'type': 'תורן מטבח', 'start_hour': 16, 'length_in_hours': 1,
     'needs_commander': 0, 'needs_driver': 0, 'needs_soldiers': 3, 'reuse_soldiers_for_standby': 0},
]

# נתוני חיילים
soldiers_data = [
    {'id': 1, 'name': 'יהונתן גבע', 'role': 'ממ', 'mahlaka': 1, 'certifications': []},
    {'id': 2, 'name': 'יהודית סטילאהו', 'role': 'מכ', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 3, 'name': 'אגם אטל', 'role': 'מכ', 'mahlaka': 1, 'sub_mahlaka': '1ב', 'certifications': []},
    {'id': 4, 'name': 'טל עזר', 'role': 'מכ', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 5, 'name': 'שוהם כרמון', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 6, 'name': 'יאנה גרין', 'role': 'נהג', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 7, 'name': 'סתיו בן סימון', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 8, 'name': 'דוד בלאי', 'role': 'נהג', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 9, 'name': 'קורל מולנר', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 10, 'name': 'סופיה שקנבסקי', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1א', 'certifications': []},
    {'id': 11, 'name': 'אוריה ונונו', 'role': 'חמליסט', 'mahlaka': 1, 'sub_mahlaka': '1ב', 'certifications': ['חמל']},
    {'id': 12, 'name': 'לאה גרבי', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ב', 'certifications': []},
    {'id': 13, 'name': 'יהלי אוסקר', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 14, 'name': 'אפרים מולויה', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 15, 'name': 'אביטל בן יהודה', 'role': 'נהג', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 16, 'name': 'איתי סעידיאן', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 17, 'name': 'יובל כהן', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 18, 'name': 'שחר לוי', 'role': 'לוחם', 'mahlaka': 1, 'sub_mahlaka': '1ג', 'certifications': []},
    {'id': 19, 'name': 'גל פחימה', 'role': 'ממ', 'mahlaka': 2, 'certifications': []},
    {'id': 20, 'name': 'רון רונן', 'role': 'סמל', 'mahlaka': 2, 'certifications': []},
    {'id': 21, 'name': 'עופרי אליעז', 'role': 'מכ', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': []},
    {'id': 22, 'name': 'קורל עג\'מי', 'role': 'מכ', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 23, 'name': 'תהל דהן', 'role': 'מכ', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 24, 'name': 'אגם ממן', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': []},
    {'id': 25, 'name': 'יובל לוי', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': []},
    {'id': 26, 'name': 'בניה אשוח', 'role': 'חמליסט', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': ['חמל']},
    {'id': 27, 'name': 'נועם קליימן', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': []},
    {'id': 28, 'name': 'ינון אברגל', 'role': 'נהג', 'mahlaka': 2, 'sub_mahlaka': '2א', 'certifications': []},
    {'id': 29, 'name': 'נועה דרהם', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 30, 'name': 'תמר קראנץ', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 31, 'name': 'דניאל ידן', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 32, 'name': 'קרין זילבריס', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 33, 'name': 'אביב גמזו', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 34, 'name': 'יאיר אחינועם', 'role': 'נהג', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 35, 'name': 'אור יונגרמן', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ב', 'certifications': []},
    {'id': 36, 'name': 'רותם עבודי', 'role': 'נהג', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 37, 'name': 'הודיה חזון', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 38, 'name': 'רונאל כהן', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 39, 'name': 'עהד דגש', 'role': 'נהג', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 40, 'name': 'יהלי ירושלמי', 'role': 'לוחם', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 41, 'name': 'עוזי שאול', 'role': 'נהג', 'mahlaka': 2, 'sub_mahlaka': '2ג', 'certifications': []},
    {'id': 42, 'name': 'אמין סבאח', 'role': 'ממ', 'mahlaka': 3, 'certifications': []},
    {'id': 43, 'name': 'שקד ביסטרה', 'role': 'סמל', 'mahlaka': 3, 'certifications': []},
    {'id': 44, 'name': 'עומר זהבי', 'role': 'מכ', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 45, 'name': 'תמר דר', 'role': 'מכ', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 46, 'name': 'גבריאלה גרייס בורנשטיין', 'role': 'מכ', 'mahlaka': 3, 'sub_mahlaka': '3ג', 'certifications': []},
    {'id': 47, 'name': 'אילנה הררה', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 48, 'name': 'כרמית לאסו', 'role': 'נהג', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 49, 'name': 'סרגיי איוונוב', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 50, 'name': 'אביאל צקולה', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 51, 'name': 'גיא מינביץ', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 52, 'name': 'אור שמש', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3א', 'certifications': []},
    {'id': 53, 'name': 'ניקול סמסוננקו', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 54, 'name': 'דאניל', 'role': 'חמליסט', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': ['חמל']},
    {'id': 55, 'name': 'יותם סנדרוביץ', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 56, 'name': 'גאיה כהן עודי', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 57, 'name': 'אליה פין', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 58, 'name': 'נועם מלמד', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ב', 'certifications': []},
    {'id': 59, 'name': 'איתמר כהן', 'role': 'נהג', 'mahlaka': 3, 'sub_mahlaka': '3ג', 'certifications': []},
    {'id': 60, 'name': 'ירוס אסמררה', 'role': 'נהג', 'mahlaka': 3, 'sub_mahlaka': '3ג', 'certifications': []},
    {'id': 61, 'name': 'ליאן טקלה', 'role': 'לוחם', 'mahlaka': 3, 'sub_mahlaka': '3ג', 'certifications': []},
    {'id': 62, 'name': 'אלדר חצבאני', 'role': 'חמליסט', 'mahlaka': 3, 'sub_mahlaka': '3ג', 'certifications': ['חמל']},
    {'id': 63, 'name': 'מאי לוי', 'role': 'ממ', 'mahlaka': 4, 'certifications': []},
    {'id': 64, 'name': 'ים אנגלשטיין', 'role': 'מכ', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 65, 'name': 'בת חן האוקיף', 'role': 'מכ', 'mahlaka': 4, 'sub_mahlaka': '4ב', 'certifications': []},
    {'id': 66, 'name': 'בן פרנקל', 'role': 'מכ', 'mahlaka': 4, 'sub_mahlaka': '4ג', 'certifications': []},
    {'id': 67, 'name': 'איבונה מלך', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 68, 'name': 'אלינה צין', 'role': 'לוחם', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 69, 'name': 'אנסטסיה ויקול', 'role': 'לוחם', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 70, 'name': 'ליהיא אסרף', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 71, 'name': 'אושר חגבי', 'role': 'לוחם', 'mahlaka': 4, 'sub_mahlaka': '4א', 'certifications': []},
    {'id': 72, 'name': 'אלנתן שוואט', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4ב', 'certifications': []},
    {'id': 73, 'name': 'דורון משה', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4ב', 'certifications': []},
    {'id': 74, 'name': 'מיטל פישמן', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4ב', 'certifications': []},
    {'id': 75, 'name': 'סעדיה מטטוב', 'role': 'נהג', 'mahlaka': 4, 'sub_mahlaka': '4ג', 'certifications': []},
    {'id': 76, 'name': 'בנימין בכר', 'role': 'לוחם', 'mahlaka': 4, 'sub_mahlaka': '4ג', 'certifications': []},
    {'id': 77, 'name': 'יהלי כהן', 'role': 'לוחם', 'mahlaka': 4, 'sub_mahlaka': 'ג', 'certifications': []},
]

def organize_mahalkot():
    """ארגון חיילים למחלקות"""
    mahalkot = {}

    for soldier in soldiers_data:
        mahlaka_id = soldier['mahlaka']
        if mahlaka_id not in mahalkot:
            mahalkot[mahlaka_id] = {
                'id': mahlaka_id,
                'commanders': [],
                'drivers': [],
                'soldiers': []
            }

        if soldier['role'] in ['ממ', 'סמל', 'מכ']:
            mahalkot[mahlaka_id]['commanders'].append(soldier)
        elif soldier['role'] == 'נהג':
            mahalkot[mahlaka_id]['drivers'].append(soldier)
        else:  # לוחם, חמליסט
            mahalkot[mahlaka_id]['soldiers'].append(soldier)

    return list(mahalkot.values())

def run_assignment_test():
    """הרצת בדיקה של אלגוריתם השיבוץ"""
    print("🚀 מתחיל בדיקת אלגוריתם שיבוץ...")
    print("=" * 80)

    # יצירת אובייקט אלגוריתם
    logic = AssignmentLogic(min_rest_hours=8, reuse_soldiers_for_standby=False)

    # ארגון מחלקות
    mahalkot = organize_mahalkot()

    print(f"\n📊 סטטיסטיקה:")
    print(f"  • מספר מחלקות: {len(mahalkot)}")
    for m in mahalkot:
        print(f"  • מחלקה {m['id']}: {len(m['commanders'])} מפקדים, {len(m['drivers'])} נהגים, {len(m['soldiers'])} לוחמים")

    print(f"\n  • מספר תבניות משימות: {len(assignment_templates)}")
    print()

    # מבנה נתונים לשיבוץ - רישום של מי שובץ למה
    schedules = {}  # {soldier_id: [(day, start_hour, end_hour, task_name, mahlaka_id)]}
    mahlaka_workload = {m['id']: 0 for m in mahalkot}

    # ניסיון לשבץ כל משימה ליום 0 (יום הראשון)
    day = 0

    print("🔄 מריץ שיבוץ ליום 0...")
    print("=" * 80)

    results = []

    for template in assignment_templates:
        print(f"\n📌 משימה: {template['name']} ({template['type']})")
        print(f"   ⏰ שעה: {template['start_hour']:02d}:00 - {template['start_hour'] + template['length_in_hours']:02d}:00")

        assign_data = {
            'day': day,
            'name': template['name'],
            'type': template['type'],
            'start_hour': template['start_hour'],
            'length_in_hours': template['length_in_hours'],
            'needs_commander': template['needs_commander'],
            'needs_driver': template['needs_driver'],
            'needs_soldiers': template['needs_soldiers'],
            'reuse_soldiers_for_standby': template['reuse_soldiers_for_standby']
        }

        # בחירת פונקציית שיבוץ לפי סוג המשימה
        result = None

        try:
            if template['type'] == 'סיור':
                result = logic.assign_patrol(assign_data, mahalkot, schedules, mahlaka_workload)
            elif template['type'] == 'שמירה':
                all_soldiers = [s for m in mahalkot for s in m['soldiers']]
                result = logic.assign_guard(assign_data, all_soldiers, schedules)
            elif template['type'] == 'קצין תורן':
                all_commanders = [c for m in mahalkot for c in m['commanders']]
                result = logic.assign_duty_officer(assign_data, all_commanders, schedules)
            elif template['type'] == 'שלז':
                all_soldiers = [s for m in mahalkot for s in m['soldiers']]
                result = logic.assign_shalaz(assign_data, all_soldiers, schedules)
            elif template['type'] == 'חפק גשש':
                all_people = soldiers_data
                result = logic.assign_hafak_gashash(assign_data, all_people, schedules)
            elif template['type'] == 'חמל':
                all_people = soldiers_data
                result = logic.assign_operations(assign_data, all_people, schedules)
            elif template['type'] == 'תורן מטבח':
                all_soldiers = [s for m in mahalkot for s in m['soldiers']]
                result = logic.assign_kitchen(assign_data, all_soldiers, schedules)
            else:
                print(f"   ⚠️  סוג משימה לא מוכר: {template['type']}")
                continue

            if result:
                # הצלחה! עדכון לוח הזמנים
                assigned_people = []

                if 'commanders' in result and result['commanders']:
                    for cmd_id in result['commanders']:
                        soldier = next((s for s in soldiers_data if s['id'] == cmd_id), None)
                        if soldier:
                            assigned_people.append(f"{soldier['name']} (מפקד)")
                            if cmd_id not in schedules:
                                schedules[cmd_id] = []
                            schedules[cmd_id].append((
                                day,
                                template['start_hour'],
                                template['start_hour'] + template['length_in_hours'],
                                template['name'],
                                result.get('mahlaka_id')
                            ))

                if 'drivers' in result and result['drivers']:
                    for drv_id in result['drivers']:
                        soldier = next((s for s in soldiers_data if s['id'] == drv_id), None)
                        if soldier:
                            assigned_people.append(f"{soldier['name']} (נהג)")
                            if drv_id not in schedules:
                                schedules[drv_id] = []
                            schedules[drv_id].append((
                                day,
                                template['start_hour'],
                                template['start_hour'] + template['length_in_hours'],
                                template['name'],
                                result.get('mahlaka_id')
                            ))

                if 'soldiers' in result and result['soldiers']:
                    for sol_id in result['soldiers']:
                        soldier = next((s for s in soldiers_data if s['id'] == sol_id), None)
                        if soldier:
                            assigned_people.append(f"{soldier['name']} (לוחם)")
                            if sol_id not in schedules:
                                schedules[sol_id] = []
                            schedules[sol_id].append((
                                day,
                                template['start_hour'],
                                template['start_hour'] + template['length_in_hours'],
                                template['name'],
                                result.get('mahlaka_id')
                            ))

                print(f"   ✅ שובץ בהצלחה:")
                for person in assigned_people:
                    print(f"      • {person}")

                results.append({
                    'task': template['name'],
                    'success': True,
                    'assigned': assigned_people
                })
            else:
                print(f"   ❌ נכשל - לא נמצא פתרון")
                results.append({
                    'task': template['name'],
                    'success': False,
                    'assigned': []
                })

        except Exception as e:
            print(f"   ❌ שגיאה: {e}")
            results.append({
                'task': template['name'],
                'success': False,
                'error': str(e)
            })

    # סיכום
    print("\n" + "=" * 80)
    print("📊 סיכום:")
    print("=" * 80)

    successful = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\n✅ הצלחות: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"❌ כישלונות: {total - successful}/{total}")

    if logic.warnings:
        print(f"\n⚠️  אזהרות ({len(logic.warnings)}):")
        for warning in logic.warnings:
            print(f"   • {warning}")

    print("\n" + "=" * 80)
    print("✨ בדיקה הושלמה!")
    print("=" * 80)

if __name__ == '__main__':
    run_assignment_test()
