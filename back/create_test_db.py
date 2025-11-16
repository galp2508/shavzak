#!/usr/bin/env python3
"""
יצירת מסד נתונים עם הנתונים האמיתיים של המשתמש
"""
import os
import sys

# הוסף את תיקיית back ל-path
sys.path.insert(0, os.path.dirname(__file__))

from models import (
    init_db, get_session, User, Pluga, Mahlaka, Soldier,
    Certification, AssignmentTemplate, Shavzak
)
from datetime import datetime

# מחק DB קיים אם יש
DB_PATH = os.path.join(os.path.dirname(__file__), 'shavzak.db')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"🗑️  מחק DB קיים: {DB_PATH}")

# יצירת DB חדש
engine = init_db(DB_PATH)
session = get_session(engine)

print("🚀 יוצר מסד נתונים עם הנתונים שלך...")

# יצירת משתמש
user = User(
    username='test',
    full_name='Test User',
    role='מפ'
)
user.set_password('test123')
session.add(user)
session.flush()

# יצירת פלוגה
pluga = Pluga(
    name='פלוגה ניסוי'
)
session.add(pluga)
session.flush()

# קישור המשתמש לפלוגה
user.pluga_id = pluga.id
session.flush()

print(f"✅ נוצר משתמש ופלוגה (ID: {pluga.id})")

# יצירת 4 מחלקות
mahalkot = []
for i in range(1, 5):
    mahlaka = Mahlaka(
        number=i,
        pluga_id=pluga.id
    )
    session.add(mahlaka)
    session.flush()
    mahalkot.append(mahlaka)

print(f"✅ נוצרו 4 מחלקות")

# נתוני חיילים
soldiers_data = [
    {'id': 1, 'name': 'יהונתן גבע', 'role': 'ממ', 'mahlaka': 1, 'certifications': []},
    {'id': 2, 'name': 'יהודית סטילאהו', 'role': 'מכ', 'mahlaka': 1, 'certifications': []},
    {'id': 3, 'name': 'אגם אטל', 'role': 'מכ', 'mahlaka': 1, 'certifications': []},
    {'id': 4, 'name': 'טל עזר', 'role': 'מכ', 'mahlaka': 1, 'certifications': []},
    {'id': 5, 'name': 'שוהם כרמון', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 6, 'name': 'יאנה גרין', 'role': 'נהג', 'mahlaka': 1, 'certifications': []},
    {'id': 7, 'name': 'סתיו בן סימון', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 8, 'name': 'דוד בלאי', 'role': 'נהג', 'mahlaka': 1, 'certifications': []},
    {'id': 9, 'name': 'קורל מולנר', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 10, 'name': 'סופיה שקנבסקי', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 11, 'name': 'אוריה ונונו', 'role': 'לוחם', 'mahlaka': 1, 'certifications': ['חמליסט']},
    {'id': 12, 'name': 'לאה גרבי', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 13, 'name': 'יהלי אוסקר', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 14, 'name': 'אפרים מולויה', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 15, 'name': 'אביטל בן יהודה', 'role': 'נהג', 'mahlaka': 1, 'certifications': []},
    {'id': 16, 'name': 'איתי סעידיאן', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 17, 'name': 'יובל כהן', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 18, 'name': 'שחר לוי', 'role': 'לוחם', 'mahlaka': 1, 'certifications': []},
    {'id': 19, 'name': 'גל פחימה', 'role': 'ממ', 'mahlaka': 2, 'certifications': []},
    {'id': 20, 'name': 'רון רונן', 'role': 'סמל', 'mahlaka': 2, 'certifications': []},
    {'id': 21, 'name': 'עופרי אליעז', 'role': 'מכ', 'mahlaka': 2, 'certifications': []},
    {'id': 22, 'name': 'קורל עג\'מי', 'role': 'מכ', 'mahlaka': 2, 'certifications': []},
    {'id': 23, 'name': 'תהל דהן', 'role': 'מכ', 'mahlaka': 2, 'certifications': []},
    {'id': 24, 'name': 'אגם ממן', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 25, 'name': 'יובל לוי', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 26, 'name': 'בניה אשוח', 'role': 'לוחם', 'mahlaka': 2, 'certifications': ['חמליסט']},
    {'id': 27, 'name': 'נועם קליימן', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 28, 'name': 'ינון אברגל', 'role': 'נהג', 'mahlaka': 2, 'certifications': []},
    {'id': 29, 'name': 'נועה דרהם', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 30, 'name': 'תמר קראנץ', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 31, 'name': 'דניאל ידן', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 32, 'name': 'קרין זילבריס', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 33, 'name': 'אביב גמזו', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 34, 'name': 'יאיר אחינועם', 'role': 'נהג', 'mahlaka': 2, 'certifications': []},
    {'id': 35, 'name': 'אור יונגרמן', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 36, 'name': 'רותם עבודי', 'role': 'נהג', 'mahlaka': 2, 'certifications': []},
    {'id': 37, 'name': 'הודיה חזון', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 38, 'name': 'רונאל כהן', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 39, 'name': 'עהד דגש', 'role': 'נהג', 'mahlaka': 2, 'certifications': []},
    {'id': 40, 'name': 'יהלי ירושלמי', 'role': 'לוחם', 'mahlaka': 2, 'certifications': []},
    {'id': 41, 'name': 'עוזי שאול', 'role': 'נהג', 'mahlaka': 2, 'certifications': []},
    {'id': 42, 'name': 'אמין סבאח', 'role': 'ממ', 'mahlaka': 3, 'certifications': []},
    {'id': 43, 'name': 'שקד ביסטרה', 'role': 'סמל', 'mahlaka': 3, 'certifications': []},
    {'id': 44, 'name': 'עומר זהבי', 'role': 'מכ', 'mahlaka': 3, 'certifications': []},
    {'id': 45, 'name': 'תמר דר', 'role': 'מכ', 'mahlaka': 3, 'certifications': []},
    {'id': 46, 'name': 'גבריאלה גרייס בורנשטיין', 'role': 'מכ', 'mahlaka': 3, 'certifications': []},
    {'id': 47, 'name': 'אילנה הררה', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 48, 'name': 'כרמית לאסו', 'role': 'נהג', 'mahlaka': 3, 'certifications': []},
    {'id': 49, 'name': 'סרגיי איוונוב', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 50, 'name': 'אביאל צקולה', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 51, 'name': 'גיא מינביץ', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 52, 'name': 'אור שמש', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 53, 'name': 'ניקול סמסוננקו', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 54, 'name': 'דאניל', 'role': 'לוחם', 'mahlaka': 3, 'certifications': ['חמליסט']},
    {'id': 55, 'name': 'יותם סנדרוביץ', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 56, 'name': 'גאיה כהן עודי', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 57, 'name': 'אליה פין', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 58, 'name': 'נועם מלמד', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 59, 'name': 'איתמר כהן', 'role': 'נהג', 'mahlaka': 3, 'certifications': []},
    {'id': 60, 'name': 'ירוס אסמררה', 'role': 'נהג', 'mahlaka': 3, 'certifications': []},
    {'id': 61, 'name': 'ליאן טקלה', 'role': 'לוחם', 'mahlaka': 3, 'certifications': []},
    {'id': 62, 'name': 'אלדר חצבאני', 'role': 'לוחם', 'mahlaka': 3, 'certifications': ['חמליסט']},
    {'id': 63, 'name': 'מאי לוי', 'role': 'ממ', 'mahlaka': 4, 'certifications': []},
    {'id': 64, 'name': 'ים אנגלשטיין', 'role': 'מכ', 'mahlaka': 4, 'certifications': []},
    {'id': 65, 'name': 'בת חן האוקיף', 'role': 'מכ', 'mahlaka': 4, 'certifications': []},
    {'id': 66, 'name': 'בן פרנקל', 'role': 'מכ', 'mahlaka': 4, 'certifications': []},
    {'id': 67, 'name': 'איבונה מלך', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 68, 'name': 'אלינה צין', 'role': 'לוחם', 'mahlaka': 4, 'certifications': []},
    {'id': 69, 'name': 'אנסטסיה ויקול', 'role': 'לוחם', 'mahlaka': 4, 'certifications': []},
    {'id': 70, 'name': 'ליהיא אסרף', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 71, 'name': 'אושר חגבי', 'role': 'לוחם', 'mahlaka': 4, 'certifications': []},
    {'id': 72, 'name': 'אלנתן שוואט', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 73, 'name': 'דורון משה', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 74, 'name': 'מיטל פישמן', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 75, 'name': 'סעדיה מטטוב', 'role': 'נהג', 'mahlaka': 4, 'certifications': []},
    {'id': 76, 'name': 'בנימין בכר', 'role': 'לוחם', 'mahlaka': 4, 'certifications': []},
    {'id': 77, 'name': 'יהלי כהן', 'role': 'לוחם', 'mahlaka': 4, 'certifications': []},
]

# יצירת חיילים
for soldier_data in soldiers_data:
    soldier = Soldier(
        name=soldier_data['name'],
        role=soldier_data['role'],
        mahlaka_id=mahalkot[soldier_data['mahlaka'] - 1].id
    )
    session.add(soldier)
    session.flush()

    # הוספת הסמכות
    for cert_name in soldier_data['certifications']:
        cert = Certification(
            soldier_id=soldier.id,
            certification_name=cert_name
        )
        session.add(cert)

print(f"✅ נוצרו {len(soldiers_data)} חיילים")

# יצירת תבניות משימות
templates_data = [
    {'name': 'ש"ג', 'assignment_type': 'שמירה', 'start_hour': 4, 'length_in_hours': 6, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 1, 'reuse_soldiers_for_standby': False},
    {'name': 'דורס 41', 'assignment_type': 'סיור', 'start_hour': 8, 'length_in_hours': 3, 'times_per_day': 1,
     'commanders_needed': 1, 'drivers_needed': 1, 'soldiers_needed': 2, 'reuse_soldiers_for_standby': False},
    {'name': 'דורס 42', 'assignment_type': 'סיור', 'start_hour': 8, 'length_in_hours': 3, 'times_per_day': 1,
     'commanders_needed': 1, 'drivers_needed': 1, 'soldiers_needed': 2, 'reuse_soldiers_for_standby': True},
    {'name': 'מחפה ש"ג', 'assignment_type': 'שמירה', 'start_hour': 4, 'length_in_hours': 6, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 1, 'reuse_soldiers_for_standby': False},
    {'name': 'קצין תורן', 'assignment_type': 'קצין תורן', 'start_hour': 8, 'length_in_hours': 3, 'times_per_day': 1,
     'commanders_needed': 1, 'drivers_needed': 0, 'soldiers_needed': 0, 'reuse_soldiers_for_standby': False},
    {'name': 'שלז', 'assignment_type': 'שלז', 'start_hour': 14, 'length_in_hours': 1, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 1, 'reuse_soldiers_for_standby': False},
    {'name': 'דורס 43', 'assignment_type': 'סיור', 'start_hour': 8, 'length_in_hours': 3, 'times_per_day': 1,
     'commanders_needed': 1, 'drivers_needed': 1, 'soldiers_needed': 2, 'reuse_soldiers_for_standby': True},
    {'name': 'חפק גשש', 'assignment_type': 'חפק גשש', 'start_hour': 0, 'length_in_hours': 1, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 1, 'reuse_soldiers_for_standby': False},
    {'name': 'חמל', 'assignment_type': 'חמל', 'start_hour': 12, 'length_in_hours': 2, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 1, 'reuse_soldiers_for_standby': False,
     'requires_certification': 'חמליסט'},
    {'name': 'מטבח', 'assignment_type': 'תורן מטבח', 'start_hour': 16, 'length_in_hours': 1, 'times_per_day': 1,
     'commanders_needed': 0, 'drivers_needed': 0, 'soldiers_needed': 3, 'reuse_soldiers_for_standby': False},
]

for template_data in templates_data:
    template = AssignmentTemplate(
        pluga_id=pluga.id,
        **template_data
    )
    session.add(template)

print(f"✅ נוצרו {len(templates_data)} תבניות משימות")

session.commit()
session.close()

print("\n" + "=" * 80)
print("✅ מסד נתונים נוצר בהצלחה!")
print(f"📁 מיקום: {DB_PATH}")
print("=" * 80)
print("\nעכשיו תוכל להריץ את השרת:")
print("  python api.py")
