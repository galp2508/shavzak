# 🤖 הנחיות AI למערכת שיבוץ שבזק

## עקרונות יסוד למנוע השיבוץ החכם

המסמך מגדיר את כללי הליבה של מערכת ה-AI לשיבוץ אוטומטי של משימות צבאיות.
**כל מנוע AI, מודל ML, או אלגוריתם שיבוץ חייב לעמוד בכללים אלה.**

---

## 🎯 הכללים המרכזיים (5 עקרונות ברזל)

### 1️⃣ כלל הרוטציה לפי מחלקות
**🔄 שיבוץ מחלקתי עם רוטציה הוגנת**

#### עיקרון:
- **שואפים לשבץ לפי מחלקות** - כל משימה צריכה להיות ממחלקה אחת (כשאפשר)
- **רוטציה אוטומטית**: 1 → 2 → 3 → 4 → 1...
  - אם יש 4 מחלקות: רוטציה מלאה
  - אם יש 3 מחלקות: 1 → 2 → 3 → 1
  - אם יש 2 מחלקות: 1 → 2 → 1
  - אם יש יותר: מרחיבים את הרוטציה

#### מימוש:
```python
# assignment_logic.py - שורות 238-265
def get_next_mahlaka_rotation(self, mahalkot, assign_data, mahlaka_workload):
    """
    מחזיר מחלקות ממויינות לפי עומס עבודה (מי שעבד פחות קודם)
    זה מבטיח רוטציה הוגנת!
    """
    if mahlaka_workload is not None:
        sorted_mahalkot = sorted(
            mahalkot,
            key=lambda m: mahlaka_workload.get(m['id'], 0)
        )
        return sorted_mahalkot
```

#### יוצאים מן הכלל:
- **משימות פלוגתיות** (כוננות א', כוננות ב') - תמיד פלוגתיות ולא מחלקתיות
- **מצב חירום** - אם אין מספיק כוח אדם במחלקה אחת, עדיף לוותר על השיבוץ ולא לערבב מחלקות

#### קוד רלוונטי:
- `/back/assignment_logic.py:238-265` - `get_next_mahlaka_rotation()`
- `/back/assignment_logic.py:267-371` - `_try_assign_patrol_normal()`
- `/back/smart_scheduler.py:415-417` - עדכון `mahlaka_workload`

---

### 2️⃣ כלל מקסימום שעות מנוחה
**😴 עדיפות למי שנח הכי הרבה**

#### עיקרון:
- **תמיד להעדיף את מי שנח הכי הרבה זמן**
- לא מינימום מנוחה אלא **מקסימום מנוחה**!
- ככל שחייל נח יותר זמן, הוא מקבל עדיפות גבוהה יותר

#### מימוש:
```python
# assignment_logic.py
def calculate_rest_hours(self, schedule, current_day, current_start_hour):
    """
    מחשב כמה שעות מנוחה יש לחייל
    ערך גבוה יותר = יותר מנוחה = עדיפות גבוהה יותר
    """
    if not schedule:
        return float('inf')  # אין משימות = מנוחה אינסופית!

    # חישוב שעות מנוחה מהמשימה האחרונה...
```

#### שימוש בכל פונקציות השיבוץ:
```python
# מיון לפי מנוחה - מי שנח יותר קודם
available.sort(
    key=lambda x: self.calculate_rest_hours(
        schedules.get(x['id'], []),
        assign_data['day'],
        assign_data['start_hour']
    ),
    reverse=True  # ⬇️ מי שנח הכי הרבה קודם!
)
```

#### קוד רלוונטי:
- `/back/assignment_logic.py:34-53` - `calculate_rest_hours()`
- `/back/assignment_logic.py:459-467` - מיון שמירה לפי מנוחה
- `/back/assignment_logic.py:665-689` - מיון כוננות א' לפי מנוחה
- `/back/smart_scheduler.py:126-128` - משקל מנוחה במודל ML (2.0)

---

### 3️⃣ כלל האילוצים הקשיחים (Iron Rules)
**🔒 כלל ברזל - אסור להפר!**

#### עיקרון:
- **אילוצים הם כלל ברזל** - אסור להפר בשום תנאי
- אם משתמש סימן שחייל לא זמין → **אסור לשבץ אותו בכלל**
- אילוצים נבדקים **לפני** כל שיבוץ

#### סוגי אילוצים קשיחים:

1. **אי-זמינות (Unavailability)**
   - חופשה
   - ריתוק משמעתי
   - התש"ב (אימון צבאי)
   - מחלה
   - **אם סומן → אסור לשבץ!**

2. **מנוחה מינימלית**
   - 8 שעות (רגיל)
   - 4 שעות (מצב חירום)
   - **אסור לשבץ אם אין מנוחה מספקת**

3. **הסמכות נדרשות**
   - חמל → דורש הסמכת "חמל"
   - נהג → דורש הסמכת "נהג"
   - **אסור לשבץ בלי הסמכה**

4. **מניעת חפיפות**
   - **אסור לשבץ חייל ל-2 משימות בו-זמנית**

#### מימוש:
```python
# smart_scheduler.py:54-91
def check_availability(self, soldier, day, start_hour, length, schedules):
    """
    בדיקת זמינות חייל - אילוץ קשיח

    בודק:
    1. לא משובץ בו-זמנית
    2. מנוחה מינימלית (8 שעות)
    3. אי-זמינות (חופשות, ריתוק, התש"ב)
    """
    # בדיקת חפיפה
    if soldier_id in schedules:
        for assign_day, assign_start, assign_end, _, _ in schedules[soldier_id]:
            if assign_day == day:
                if not (end_hour <= assign_start or start_hour >= assign_end):
                    return False  # ❌ חפיפה!

    # בדיקת מנוחה מינימלית
    if start_hour < last_end + self.min_rest_hours:
        return False  # ❌ מנוחה לא מספקת!

    return True
```

#### כלל חשוב:
**אם המשתמש בחר שחייל ירד ממשימה (או לא זמין) → זה כלל ברזל!**
המערכת לא תשבץ אותו גם אם אין כוח אדם מספיק.

#### קוד רלוונטי:
- `/back/smart_scheduler.py:54-91` - `check_availability()`
- `/back/smart_scheduler.py:93-104` - `has_certification()`, `is_commander()`, `is_driver()`
- `/back/assignment_logic.py:55-79` - `can_assign_at()`
- `/back/models.py` - טבלת `SchedulingConstraint`

---

### 4️⃣ כלל הפידבק המיידי
**⚡ פידבק = שינוי מיידי בשיבוץ**

#### עיקרון:
- **ברגע שמשתמש נותן פידבק** → המערכת מעדכנת את השיבוץ **באותו רגע**
- הפידבק משפיע על:
  1. **השיבוץ הספציפי** (אישור/דחייה/שינוי)
  2. **המודל ML** (לומד מהפידבק לעתיד)

#### סוגי פידבק:

1. **Approved (אושר) ✅**
   - המשתמש מאשר את השיבוץ
   - המודל לומד: "שיבוץ כזה טוב!"
   - מעלה את הציון של דפוס זה

2. **Rejected (נדחה) ❌**
   - המשתמש דוחה את השיבוץ
   - המודל לומד: "שיבוץ כזה רע!"
   - מוריד את הציון של דפוס זה
   - **השיבוץ מבוטל מיידית**

3. **Modified (שונה) 🔧**
   - המשתמש שינה את השיבוץ
   - המודל לומד מהשינויים
   - **השיבוץ מתעדכן לפי השינויים**

#### מימוש:
```python
# smart_scheduler.py:284-334
def add_feedback(self, assignment, rating, changes=None):
    """
    הוסף פידבק מהמשתמש על שיבוץ

    rating: 'approved', 'rejected', 'modified'
    changes: מה השתנה (אם המשתמש ערך)
    """
    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'assignment_id': assignment.get('id'),
        'task_type': assignment['type'],
        'soldier_id': assignment.get('soldiers', []),
        'rating': rating,
        'changes': changes
    }

    self.user_feedback.append(feedback_entry)

    # עדכן סטטיסטיקות
    if rating == 'approved':
        self.stats['user_approvals'] += 1
    elif rating == 'rejected':
        self.stats['user_rejections'] += 1
        self.rejected_assignments.append(assignment)
    elif rating == 'modified':
        self.stats['manual_changes'] += 1

    # למד מהפידבק! ⚡
    self._learn_from_feedback(feedback_entry)
```

#### משקל פידבק במודל:
```python
# smart_scheduler.py:145-146
feedback_score = self._get_feedback_score(soldier, task)
score += feedback_score * 4.0  # ⭐ משקל הכי גבוה!
```

**פידבק הוא המשקל הכי חשוב במערכת! (4.0)**

#### קוד רלוונטי:
- `/back/smart_scheduler.py:284-334` - `add_feedback()`
- `/back/smart_scheduler.py:314-334` - `_learn_from_feedback()`
- `/back/smart_scheduler.py:203-224` - `_get_feedback_score()`
- `/back/api.py` - endpoint `POST /api/ml/feedback`

---

### 5️⃣ כלל אי-הכישלון
**✅ המערכת תמיד מצליחה!**

#### עיקרון:
- **אף פעם לא להחזיר שגיאה/Exception**
- **תמיד למצוא פתרון** - גם אם לא אידיאלי
- **מערכת Fallback** עם 3 שכבות:
  1. ניסיון רגיל (מנוחה מלאה 8 שעות)
  2. מצב חירום (מנוחה מופחתת 4 שעות)
  3. **שכבת גיבוי** - מצא כל פתרון אפשרי (גם בלי מנוחה)

#### מימוש - דוגמה מסיור:
```python
# assignment_logic.py:183-220
def assign_patrol(self, assign_data, mahalkot, schedules, mahlaka_workload):
    """שיבוץ סיור - תמיד מצליח!"""

    # 🔵 שלב 1: ניסיון רגיל (מנוחה 8 שעות)
    result = self._try_assign_patrol_normal(...)
    if result:
        return result

    # 🟡 שלב 2: מצב חירום (מנוחה 4 שעות)
    if self.emergency_mode:
        result = self._try_assign_patrol_emergency(...)
        if result:
            return result

    # 🟢 שלב 3: 🔧 המערכת תמיד מצליחה!
    # אם אין פתרון אידיאלי - נמצא כל פתרון
    for mahlaka_info in mahalkot:
        if len(commanders) > 0 and len(soldiers) >= 2:
            return {
                'commanders': [commanders[0]['id']],
                'drivers': [drivers[0]['id']] if drivers else [],
                'soldiers': [s['id'] for s in soldiers[:2]],
                'mahlaka_id': mahlaka_info['id']
            }

    # גם אם זה לא מושלם - לפחות מחזירים משהו
    return {
        'commanders': [all_commanders[0]['id']] if all_commanders else [],
        'drivers': [all_drivers[0]['id']] if all_drivers else [],
        'soldiers': [...],
        'mahlaka_id': mahalkot[0]['id'] if mahalkot else None
    }
```

#### אסטרטגיות Fallback לפי סוג משימה:

1. **סיור**:
   - רגיל: מחלקה שלמה + מנוחה 8 שעות
   - חירום: מחלקה שלמה + מנוחה 4 שעות
   - גיבוי: כל מפקד + 2 לוחמים זמינים (גם בלי מנוחה)

2. **שמירה**:
   - רגיל: 1 לוחם עם מנוחה 8 שעות
   - חירום: 1 לוחם עם מנוחה 4 שעות
   - גיבוי: כל לוחם זמין (גם בלי מנוחה, רק לא משובץ)

3. **כוננות א'/ב'**:
   - רגיל: לפי מספרים מלאים + מנוחה 8 שעות
   - חירום: מנוחה 4 שעות
   - גיבוי: כל מי שזמין (גם פחות אנשים מהנדרש)

4. **חמל**:
   - רגיל: מוסמך חמל + מנוחה 8 שעות
   - חירום: מוסמך חמל + מנוחה 4 שעות
   - גיבוי: **כל מי שזמין** (גם בלי הסמכה!)

#### הודעות למשתמש:
במקרה של Fallback, המערכת מוסיפה אזהרות:
```python
self.warnings.append(f"⚠️ {assign_data['name']}: שובצו רק {num} מתוך {needed}")
```

#### כלל הזהב:
**עדיף שיבוץ לא מושלם מאשר כישלון!**

#### קוד רלוונטי:
- `/back/assignment_logic.py:183-220` - `assign_patrol()` - דוגמה מלאה
- `/back/assignment_logic.py:448-517` - `assign_guard()` - Fallback לשמירה
- `/back/assignment_logic.py:622-746` - `assign_standby_a()` - Fallback לכוננות
- `/back/assignment_logic.py:12-13` - `emergency_mode` flag

---

## 📊 משקולות ציון במודל ML

הנוסחה המלאה לחישוב ציון חייל למשימה:

```python
score = (
    rest_hours        * 2.0 +    # 😴 מנוחה (כלל 2)
    -workload         * 1.5 +    # 💼 עומס עבודה
    pattern_score     * 3.0 +    # 🎯 דפוסים שנלמדו
    -mahlaka_workload * 0.5 +    # 🔄 עומס מחלקה (כלל 1)
    feedback_score    * 4.0      # ⚡ פידבק משתמש (כלל 4) - הכי חשוב!
)
```

**ציון גבוה יותר = מתאים יותר למשימה**

### הסברים:
- `rest_hours * 2.0`: מעודד שיבוץ של מי שנח הרבה (כלל 2)
- `-workload * 1.5`: מעניש חיילים שעבדו הרבה השבוע
- `pattern_score * 3.0`: מעודד דפוסים שעבדו טוב בעבר
- `-mahlaka_workload * 0.5`: מעודד רוטציה בין מחלקות (כלל 1)
- `feedback_score * 4.0`: **המשקל הגבוה ביותר!** (כלל 4)

---

## 🔄 תהליך השיבוץ - שלב אחר שלב

```
┌─────────────────────────────────────────┐
│  1. קבלת בקשה לשיבוץ חכם              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  2. בדיקת אילוצים קשיחים (כלל 3)      │
│     ✓ זמינות                            │
│     ✓ מנוחה מינימלית                   │
│     ✓ הסמכות                            │
│     ✓ ללא חפיפות                        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  3. סינון חיילים זמינים                │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  4. ניקוד חיילים (ML)                  │
│     • מנוחה (כלל 2)                    │
│     • עומס מחלקה (כלל 1)               │
│     • פידבק (כלל 4)                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  5. בחירת הטובים ביותר                 │
│     (ציון גבוה = עדיפות)               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  6. יצירת שיבוץ                        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  7. Fallback במידת הצורך (כלל 5)      │
│     רגיל → חירום → גיבוי               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  8. פידבק מהמשתמש (כלל 4)             │
│     → עדכון מודל ML                    │
└─────────────────────────────────────────┘
```

---

## 🎓 דוגמאות שימוש

### דוגמה 1: שיבוץ סיור
```python
# המערכת תבחר:
# 1. מחלקה שעבדה הכי פחות (כלל 1 - רוטציה)
# 2. מפקד + 2 לוחמים שנחו הכי הרבה (כלל 2 - מנוחה)
# 3. רק אם הם זמינים (כלל 3 - אילוצים)
# 4. אם אין - Fallback (כלל 5 - לא נכשל)

result = scheduler.assign_patrol(assign_data, mahalkot, schedules, mahlaka_workload)
# ✅ תמיד יחזיר תוצאה!
```

### דוגמה 2: פידבק מיידי
```python
# משתמש דוחה שיבוץ
scheduler.add_feedback(
    assignment={'type': 'סיור', 'soldiers': [1, 2, 3]},
    rating='rejected'
)
# ⚡ המודל לומד מיידית!
# הפעם הבאה הוא לא ישבץ את החיילים האלה יחד

# משתמש מאשר שיבוץ
scheduler.add_feedback(
    assignment={'type': 'שמירה', 'soldiers': [4]},
    rating='approved'
)
# ⚡ המודל לומד: "חייל 4 טוב לשמירות!"
```

### דוגמה 3: אילוץ קשיח
```python
# חייל בחופשה
unavailable_dates = [
    {'soldier_id': 5, 'date': '2025-01-15', 'reason': 'חופשה'}
]

# המערכת לא תשבץ אותו ב-15/1 - כלל ברזל! (כלל 3)
# גם אם אין כוח אדם מספיק
```

---

## 📝 סיכום - Checklist לפיתוח

כשמוסיפים/משנים תכונה במערכת, וודא:

- [ ] **כלל 1**: האם השיבוץ שומר על רוטציה בין מחלקות?
- [ ] **כלל 2**: האם מועדפים חיילים שנחו יותר זמן?
- [ ] **כלל 3**: האם כל האילוצים הקשיחים נבדקים?
- [ ] **כלל 4**: האם הפידבק משתלב ומעדכן את המודל?
- [ ] **כלל 5**: האם יש Fallback שמונע כישלון?

---

## 🔗 קבצים רלוונטיים

| קובץ | תיאור | כללים |
|------|-------|-------|
| `/back/smart_scheduler.py` | מנוע ML מרכזי | 2, 3, 4 |
| `/back/assignment_logic.py` | לוגיקת שיבוץ | 1, 2, 5 |
| `/back/api.py` | API endpoints | 4 |
| `/back/models.py` | מודל DB | 3 |
| `/back/config.py` | הגדרות | 3 |

---

## 🚨 אזהרות חשובות

1. **אסור לשנות את המשקולות** בלי לעדכן את המסמך הזה
2. **אסור להוסיף Exception** בפונקציות שיבוץ (כלל 5)
3. **אסור להתעלם מאילוצים קשיחים** (כלל 3)
4. **אסור לבטל פידבק** מהמשתמש (כלל 4)

---

**נוצר על ידי צוות פיתוח שבזק 🎖️**

**עדכון אחרון: 2025-01-17**
