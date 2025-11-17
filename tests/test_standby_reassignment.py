#!/usr/bin/env python3
"""
טסט ללוגיקת שיבוץ כוננויות מאנשים שירדו ממשימות
"""
from back.assignment_logic import AssignmentLogic

def test_standby_a_from_patrols():
    """בדיקה שכוננות א' לוקחת אנשים מ-2 סיורים שהסתיימו"""

    logic = AssignmentLogic(min_rest_hours=8, reuse_soldiers_for_standby=False)

    # צור נתוני בדיקה
    # מחלקה 1
    commanders = [
        {'id': 1, 'name': 'מכ אחד', 'role': 'מכ', 'certifications': []},
        {'id': 2, 'name': 'מכ שתיים', 'role': 'מכ', 'certifications': []},
        {'id': 3, 'name': 'סמל', 'role': 'סמל', 'certifications': []},
    ]

    drivers = [
        {'id': 10, 'name': 'נהג 1', 'role': 'לוחם', 'certifications': ['נהג']},
        {'id': 11, 'name': 'נהג 2', 'role': 'לוחם', 'certifications': ['נהג']},
        {'id': 12, 'name': 'נהג 3', 'role': 'לוחם', 'certifications': ['נהג']},
    ]

    soldiers = [
        {'id': 20 + i, 'name': f'לוחם {i}', 'role': 'לוחם', 'certifications': []}
        for i in range(15)
    ]

    # בנה לוח זמנים: 2 סיורים שהסתיימו בשעה 10:00 ביום 0
    # סיור 41: מפקד 1 + נהג 1 + לוחמים 0-3 (4 לוחמים)
    # סיור 42: מפקד 2 + נהג 2 + לוחמים 4-7 (4 לוחמים)
    # סה"כ: 8 לוחמים (יותר מ-7 שצריך)
    schedules = {
        1: [(0, 8, 10, 'דורס 41', 'סיור')],  # מכ אחד
        10: [(0, 8, 10, 'דורס 41', 'סיור')],  # נהג 1
        20: [(0, 8, 10, 'דורס 41', 'סיור')],  # לוחם 0
        21: [(0, 8, 10, 'דורס 41', 'סיור')],  # לוחם 1
        22: [(0, 8, 10, 'דורס 41', 'סיור')],  # לוחם 2
        23: [(0, 8, 10, 'דורס 41', 'סיור')],  # לוחם 3

        2: [(0, 8, 10, 'דורס 42', 'סיור')],  # מכ שתיים
        11: [(0, 8, 10, 'דורס 42', 'סיור')],  # נהג 2
        24: [(0, 8, 10, 'דורס 42', 'סיור')],  # לוחם 4
        25: [(0, 8, 10, 'דורס 42', 'סיור')],  # לוחם 5
        26: [(0, 8, 10, 'דורס 42', 'סיור')],  # לוחם 6
        27: [(0, 8, 10, 'דורס 42', 'סיור')],  # לוחם 7
    }

    # כוננות א' מתחילה בשעה 11:00 (שעה אחרי שהסיורים הסתיימו)
    assign_data = {
        'day': 0,
        'start_hour': 11,
        'length_in_hours': 8,
        'reuse_soldiers_for_standby': True  # מסומן!
    }

    print("🔍 בדיקה: כוננות א' עם reuse_soldiers_for_standby=True")
    print("=" * 70)
    print("📋 סיורים שהסתיימו:")
    print("   • דורס 41: מכ אחד (id=1) + לוחמים 0,1,2,3 (4 לוחמים)")
    print("   • דורס 42: מכ שתיים (id=2) + לוחמים 4,5,6,7 (4 לוחמים)")
    print("   • סה\"כ: 8 לוחמים (נהגים לא נספרים!)")
    print()

    result = logic.assign_standby_a(assign_data, commanders, drivers, soldiers, schedules)

    print("✅ תוצאה:")
    print(f"   מפקדים: {result.get('commanders', [])}")
    print(f"   נהגים: {result.get('drivers', [])}")
    print(f"   לוחמים: {result.get('soldiers', [])}")
    print()

    # בדיקות
    if not result['commanders']:
        print("❌ FAIL: אין מפקד!")
        return False

    # המפקד הבכיר צריך להיות מכ (id=1 או id=2)
    commander_id = result['commanders'][0]
    if commander_id not in [1, 2]:
        print(f"❌ FAIL: המפקד ({commander_id}) לא מהסיורים!")
        return False

    print(f"✅ מפקד הככ\"א: {commander_id} ({'מכ אחד' if commander_id == 1 else 'מכ שתיים'})")

    # צריכים להיות 7 לוחמים מהסיורים (20-27 = 8 לוחמים, נקח 7)
    soldiers_from_patrols = set(range(20, 28))
    assigned_soldiers = set(result['soldiers'][:7])

    if len(assigned_soldiers) != 7:
        print(f"❌ FAIL: רק {len(assigned_soldiers)} לוחמים, צריך 7")
        return False

    overlap = assigned_soldiers & soldiers_from_patrols
    if len(overlap) != 7:
        print(f"❌ FAIL: רק {len(overlap)} לוחמים מהסיורים, צריך 7")
        return False

    print(f"✅ לוחמים: {len(overlap)}/7 מהסיורים")

    # נהג צריך להיות זמין (לא מהסיורים!)
    if not result['drivers']:
        print("❌ FAIL: אין נהג!")
        return False

    driver_id = result['drivers'][0]
    if driver_id in [10, 11]:  # נהגים שהיו בסיורים
        print(f"⚠️  WARNING: הנהג ({driver_id}) היה בסיור (אמור להיות זמין)")

    print(f"✅ נהג: {driver_id}")
    print()
    print("=" * 70)
    print("✨ הטסט עבר בהצלחה!")
    return True


def test_standby_b_from_tasks():
    """בדיקה שכוננות ב' לוקחת מפקד מסיור 3 + שומרים מ-3 שמירות"""

    logic = AssignmentLogic(min_rest_hours=8, reuse_soldiers_for_standby=False)

    # צור נתוני בדיקה
    commanders = [
        {'id': 1, 'name': 'מכ 1', 'role': 'מכ', 'certifications': []},
        {'id': 2, 'name': 'מכ 2', 'role': 'מכ', 'certifications': []},
        {'id': 3, 'name': 'מכ 3', 'role': 'מכ', 'certifications': []},
        {'id': 4, 'name': 'מכ 4', 'role': 'מכ', 'certifications': []},
    ]

    soldiers = [
        {'id': 20 + i, 'name': f'לוחם {i}', 'role': 'לוחם', 'certifications': []}
        for i in range(20)
    ]

    # בנה לוח זמנים:
    # 3 סיורים שהסתיימו:
    #   סיור 41: מכ 1 + לוחמים 0-2 (8:00-10:00)
    #   סיור 42: מכ 2 + לוחמים 3-5 (8:00-10:00)
    #   סיור 43: מכ 3 + לוחמים 6-8 (8:00-10:00)
    # 3 שמירות שהסתיימו:
    #   שמירה 1: לוחם 10 (6:00-10:00)
    #   שמירה 2: לוחם 11 (6:00-10:00)
    #   שמירה 3: לוחם 12 (6:00-10:00)
    schedules = {
        # סיורים
        1: [(0, 8, 10, 'דורס 41', 'סיור')],
        20: [(0, 8, 10, 'דורס 41', 'סיור')],
        21: [(0, 8, 10, 'דורס 41', 'סיור')],
        22: [(0, 8, 10, 'דורס 41', 'סיור')],

        2: [(0, 8, 10, 'דורס 42', 'סיור')],
        23: [(0, 8, 10, 'דורס 42', 'סיור')],
        24: [(0, 8, 10, 'דורס 42', 'סיור')],
        25: [(0, 8, 10, 'דורס 42', 'סיור')],

        3: [(0, 8, 10, 'דורס 43', 'סיור')],  # הסיור השלישי!
        26: [(0, 8, 10, 'דורס 43', 'סיור')],
        27: [(0, 8, 10, 'דורס 43', 'סיור')],
        28: [(0, 8, 10, 'דורס 43', 'סיור')],

        # שמירות
        30: [(0, 6, 10, 'שמירה 1', 'שמירה')],
        31: [(0, 6, 10, 'שמירה 2', 'שמירה')],
        32: [(0, 6, 10, 'שמירה 3', 'שמירה')],
    }

    # כוננות ב' מתחילה בשעה 11:00
    assign_data = {
        'day': 0,
        'start_hour': 11,
        'length_in_hours': 8,
        'reuse_soldiers_for_standby': True  # מסומן!
    }

    print("\n🔍 בדיקה: כוננות ב' עם reuse_soldiers_for_standby=True")
    print("=" * 70)
    print("📋 משימות שהסתיימו:")
    print("   סיורים:")
    print("   • דורס 41: מכ 1")
    print("   • דורס 42: מכ 2")
    print("   • דורס 43: מכ 3 (הסיור השלישי!)")
    print("   שמירות:")
    print("   • שמירה 1: לוחם 30")
    print("   • שמירה 2: לוחם 31")
    print("   • שמירה 3: לוחם 32")
    print()

    result = logic.assign_standby_b(assign_data, commanders, soldiers, schedules)

    print("✅ תוצאה:")
    print(f"   מפקדים: {result.get('commanders', [])}")
    print(f"   לוחמים: {result.get('soldiers', [])}")
    print()

    # בדיקות
    if not result['commanders']:
        print("❌ FAIL: אין מפקד!")
        return False

    # המפקד צריך להיות מכ 3 (מהסיור השלישי!)
    commander_id = result['commanders'][0]
    if commander_id != 3:
        print(f"❌ FAIL: המפקד ({commander_id}) לא מכ 3 (הסיור השלישי)!")
        return False

    print(f"✅ מפקד: {commander_id} (מכ 3 מהסיור השלישי)")

    # צריכים להיות 3 שומרים מהשמירות (30, 31, 32)
    expected_guards = {30, 31, 32}
    assigned_soldiers = set(result['soldiers'][:3])

    if len(assigned_soldiers) != 3:
        print(f"❌ FAIL: {len(assigned_soldiers)} לוחמים, צריך 3")
        return False

    if assigned_soldiers != expected_guards:
        print(f"❌ FAIL: לוחמים {assigned_soldiers} לא תואמים לשומרים {expected_guards}")
        return False

    print(f"✅ לוחמים: {assigned_soldiers} (3 שומרים מהשמירות)")

    print()
    print("=" * 70)
    print("✨ הטסט עבר בהצלחה!")
    return True


def test_no_reuse():
    """בדיקה ששיבוץ רגיל עובד כשהאופציה לא מסומנת"""

    logic = AssignmentLogic(min_rest_hours=8, reuse_soldiers_for_standby=False)

    commanders = [
        {'id': 1, 'name': 'מכ', 'role': 'מכ', 'certifications': []},
    ]

    drivers = [
        {'id': 10, 'name': 'נהג', 'role': 'לוחם', 'certifications': ['נהג']},
    ]

    soldiers = [
        {'id': 20 + i, 'name': f'לוחם {i}', 'role': 'לוחם', 'certifications': []}
        for i in range(10)
    ]

    # אין משימות קודמות
    schedules = {}

    # כוננות א' עם reuse=False (שיבוץ רגיל)
    assign_data = {
        'day': 0,
        'start_hour': 11,
        'length_in_hours': 8,
        'reuse_soldiers_for_standby': False  # לא מסומן!
    }

    print("\n🔍 בדיקה: שיבוץ רגיל עם reuse_soldiers_for_standby=False")
    print("=" * 70)

    result = logic.assign_standby_a(assign_data, commanders, drivers, soldiers, schedules)

    print("✅ תוצאה:")
    print(f"   מפקדים: {result.get('commanders', [])}")
    print(f"   נהגים: {result.get('drivers', [])}")
    print(f"   לוחמים: {result.get('soldiers', [])}")
    print()

    # בדיקות - שיבוץ רגיל צריך להצליח
    if not result['commanders']:
        print("❌ FAIL: אין מפקד!")
        return False

    if not result['drivers']:
        print("❌ FAIL: אין נהג!")
        return False

    if len(result['soldiers']) != 7:
        print(f"❌ FAIL: {len(result['soldiers'])} לוחמים, צריך 7")
        return False

    print("✅ שיבוץ רגיל עובד כראוי")
    print()
    print("=" * 70)
    print("✨ הטסט עבר בהצלחה!")
    return True


if __name__ == '__main__':
    print("🚀 מתחיל טסטים ללוגיקת שיבוץ כוננויות מאנשים שירדו ממשימות")
    print("=" * 70)
    print()

    success = True

    # טסט 1: כוננות א' מסיורים
    if not test_standby_a_from_patrols():
        success = False

    # טסט 2: כוננות ב' מסיור 3 + שמירות
    if not test_standby_b_from_tasks():
        success = False

    # טסט 3: שיבוץ רגיל
    if not test_no_reuse():
        success = False

    print()
    print("=" * 70)
    if success:
        print("✅ כל הטסטים עברו בהצלחה!")
    else:
        print("❌ חלק מהטסטים נכשלו")
    print("=" * 70)
