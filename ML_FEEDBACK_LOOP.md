# 🔄 לולאת למידה אוטומטית - Model Training Feedback Loop

## תיאור כללי

מערכת השיבוץ כוללת עכשיו **לולאת למידה אוטומטית** שבה המודל לומד מפידבק המשתמש ומשתפר עם הזמן.

## 💡 איך זה עובד?

### 1. פידבק על שיבוץ

כאשר המשתמש מקבל שיבוץ מהמודל, הוא יכול לתת פידבק:

- **✅ אישור (Approved)**: השיבוץ טוב - המודל לומד שזה שיבוץ מוצלח
- **❌ דחייה (Rejected)**: השיבוץ לא טוב - המערכת מייצרת שיבוץ חדש אוטומטית
- **✏️ שינוי (Modified)**: המשתמש ערך את השיבוץ - המודל לומד מהשינויים

### 2. לולאת שיפור אוטומטית

```
┌─────────────────────────────────────────┐
│  1. המודל מייצר שיבוץ                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. המשתמש מקבל פידבק                   │
│     ✅ מאשר / ❌ דוחה / ✏️ מעדכן        │
└──────────────┬──────────────────────────┘
               │
               ▼
       ┌───────┴───────┐
       │               │
       ▼               ▼
   [מאשר]         [דוחה]
       │               │
       ▼               ▼
  המודל למד!    יצירה אוטומטית
                 של שיבוץ חדש
                       │
                       ▼
                ┌─────────────┐
                │  חזרה לשלב 2│
                └─────────────┘
```

### 3. למידה מתמשכת

המודל משפר את עצמו בכל פידבק:

- **פידבק חיובי**: מעלה את הציון של החיילים והשיבוצים הטובים
- **פידבק שלילי**: מוריד את הציון של החיילים והשיבוצים הגרועים
- **שינויים**: לומד מהבחירות של המשתמש

---

## 📊 טבלאות חדשות במסד הנתונים

### 1. **ScheduleIteration** - איטרציות שיבוץ

כל שיבוץ יכול לעבור מספר איטרציות עד שהמשתמש מרוצה:

| שדה | תיאור |
|-----|-------|
| `id` | מזהה ייחודי |
| `shavzak_id` | קישור לשיבוץ |
| `iteration_number` | מספר הניסיון (1, 2, 3...) |
| `is_active` | האם זו האיטרציה הפעילה |
| `status` | מצב: pending / approved / rejected / superseded |
| `created_at` | תאריך יצירה |

### 2. **FeedbackHistory** - היסטוריית פידבקים

שומר את כל הפידבקים שהמשתמש נתן:

| שדה | תיאור |
|-----|-------|
| `id` | מזהה ייחודי |
| `shavzak_id` | קישור לשיבוץ |
| `iteration_id` | קישור לאיטרציה |
| `assignment_id` | קישור למשימה ספציפית |
| `rating` | הדירוג: approved / rejected / modified |
| `feedback_text` | טקסט הפידבק (אופציונלי) |
| `changes` | JSON של השינויים |
| `user_id` | מי נתן את הפידבק |
| `created_at` | מתי |
| `triggered_new_iteration` | האם הפידבק יצר איטרציה חדשה |

---

## 🔌 API Endpoints חדשים

### 1. **POST /api/ml/feedback** (מעודכן)

הוספת פידבק עם לולאת למידה:

```json
{
  "assignment_id": 123,
  "shavzak_id": 456,
  "rating": "approved",  // או "rejected" / "modified"
  "changes": {
    "feedback_text": "החייל לא מתאים למשימה",
    "preferred_soldiers": [1, 2, 3]
  },
  "enable_auto_regeneration": true
}
```

**תגובה:**

```json
{
  "message": "תודה! המודל למד מהשיבוץ הטוב הזה",
  "stats": {...},
  "needs_regeneration": false,
  "iteration_status": "approved",
  "feedback_id": 789,
  "iteration_id": 1
}
```

### 2. **POST /api/ml/regenerate-schedule** (חדש!)

יצירת שיבוץ חדש אחרי פידבק שלילי:

```json
{
  "shavzak_id": 456,
  "reason": "פידבק שלילי - יצירת שיבוץ משופר"
}
```

**תגובה:**

```json
{
  "message": "נוצרה איטרציה חדשה (2) עם 42 משימות",
  "iteration_id": 2,
  "iteration_number": 2,
  "assignments_count": 42,
  "stats": {...}
}
```

### 3. **GET /api/ml/feedback-history/:shavzak_id** (חדש!)

קבלת היסטוריית פידבקים ואיטרציות:

**תגובה:**

```json
{
  "iterations": [
    {
      "id": 1,
      "iteration_number": 1,
      "status": "rejected",
      "is_active": false,
      "created_at": "2025-01-01T10:00:00",
      "feedbacks": [
        {
          "id": 1,
          "rating": "rejected",
          "feedback_text": "החייל לא מתאים",
          "created_at": "2025-01-01T10:05:00",
          "triggered_new_iteration": true
        }
      ],
      "feedbacks_count": 1
    },
    {
      "id": 2,
      "iteration_number": 2,
      "status": "approved",
      "is_active": true,
      "created_at": "2025-01-01T10:10:00",
      "feedbacks": [
        {
          "id": 2,
          "rating": "approved",
          "feedback_text": "מעולה!",
          "created_at": "2025-01-01T10:15:00",
          "triggered_new_iteration": false
        }
      ],
      "feedbacks_count": 1
    }
  ],
  "current_iteration": {...},
  "total_iterations": 2,
  "total_feedbacks": 2
}
```

---

## 🧠 SmartScheduler - פונקציות חדשות

### 1. **add_feedback_with_learning_loop()**

מקבלת פידבק ומחזירה האם צריך ליצור שיבוץ חדש:

```python
result = smart_scheduler.add_feedback_with_learning_loop(
    shavzak_id=456,
    assignment=assignment_data,
    rating='rejected',
    changes={'reason': 'החייל עייף'}
)

# result = {
#     'needs_regeneration': True,
#     'feedback_saved': True,
#     'message': 'השיבוץ נדחה. המערכת תיצור שיבוץ חדש אוטומטית',
#     'iteration_status': 'rejected'
# }
```

### 2. **_penalize_rejected_assignment()**

מורידה ציון לשיבוצים שנדחו:

```python
# אם שיבוץ נדחה, המודל לומד להימנע מחיילים אלו במשימות דומות
smart_scheduler._penalize_rejected_assignment(
    assignment={'type': 'סיור', 'soldiers': [1, 2, 3]},
    changes={'reason': 'לא מתאים'}
)
```

### 3. **_learn_from_modifications()**

לומדת מהשינויים שהמשתמש עשה:

```python
# אם המשתמש החליף חיילים, המודל לומד מזה
smart_scheduler._learn_from_modifications(
    original_assignment={'type': 'סיור', 'soldiers': [1, 2, 3]},
    changes={
        'old_soldiers': [2, 3],
        'new_soldiers': [4, 5]
    }
)
```

---

## 📈 דוגמה מלאה לשימוש

### תרחיש: שיבוץ שנדחה ונוצר מחדש

#### שלב 1: המודל יוצר שיבוץ
```bash
POST /api/ml/smart-schedule
{
  "pluga_id": 1,
  "start_date": "2025-01-01",
  "days_count": 7
}
```

#### שלב 2: המשתמש דוחה את השיבוץ
```bash
POST /api/ml/feedback
{
  "assignment_id": 123,
  "shavzak_id": 456,
  "rating": "rejected",
  "changes": {
    "feedback_text": "החייל לא מתאים לסיור"
  },
  "enable_auto_regeneration": true
}

# Response:
# {
#   "message": "השיבוץ נדחה. המערכת תיצור שיבוץ חדש אוטומטית",
#   "needs_regeneration": true,
#   "iteration_status": "rejected"
# }
```

#### שלב 3: המערכת יוצרת שיבוץ חדש אוטומטית
```bash
POST /api/ml/regenerate-schedule
{
  "shavzak_id": 456,
  "reason": "פידבק שלילי - יצירת שיבוץ משופר"
}

# Response:
# {
#   "message": "נוצרה איטרציה חדשה (2) עם 42 משימות",
#   "iteration_number": 2
# }
```

#### שלב 4: המשתמש מאשר את השיבוץ החדש
```bash
POST /api/ml/feedback
{
  "assignment_id": 456,
  "shavzak_id": 456,
  "rating": "approved"
}

# Response:
# {
#   "message": "תודה! המודל למד מהשיבוץ הטוב הזה",
#   "needs_regeneration": false,
#   "iteration_status": "approved"
# }
```

#### שלב 5: צפייה בהיסטוריה
```bash
GET /api/ml/feedback-history/456

# Response:
# {
#   "iterations": [
#     {"iteration_number": 1, "status": "rejected", ...},
#     {"iteration_number": 2, "status": "approved", ...}
#   ],
#   "total_iterations": 2,
#   "total_feedbacks": 2
# }
```

---

## 🎯 יתרונות המערכת

1. **שיפור מתמיד**: המודל משתפר עם כל פידבק
2. **אוטומציה מלאה**: אין צורך ליצור שיבוץ חדש ידנית
3. **היסטוריה מלאה**: כל הפידבקים והאיטרציות נשמרים
4. **למידה מהירה**: המודל לומד מטעויות ומצלחות
5. **שקיפות**: המשתמש רואה את כל התהליך

---

## 🚀 שימוש עתידי

### UI Integration (הבא בתור)

בממשק המשתמש ניתן להוסיף:

1. **כפתורי פידבק**: 👍 👎 ✏️ על כל שיבוץ
2. **הצגת איטרציות**: הצגה של כל הניסיונות
3. **התראות**: "המודל יוצר שיבוץ חדש..."
4. **אנליטיקה**: גרפים של שיפור המודל עם הזמן

### דוגמת קוד React:

```jsx
const handleFeedback = async (assignmentId, rating) => {
  const response = await api.post('/ml/feedback', {
    assignment_id: assignmentId,
    shavzak_id: currentShavzakId,
    rating: rating
  });

  if (response.data.needs_regeneration) {
    // הצג הודעה: "יוצר שיבוץ חדש..."
    await api.post('/ml/regenerate-schedule', {
      shavzak_id: currentShavzakId
    });
    // רענן את הדף
    loadSchedule();
  }
};
```

---

## 📝 הערות חשובות

1. **שמירת המודל**: המודל נשמר אוטומטית אחרי כל פידבק
2. **ביצועים**: כל איטרציה משתמשת בדפוסים שנלמדו מהאיטרציות הקודמות
3. **אבטחה**: רק משתמשים מורשים יכולים לתת פידבק
4. **מסד נתונים**: הטבלאות החדשות נוצרות אוטומטית

---

## 🔧 תחזוקה

### עדכון מסד הנתונים

```bash
cd /home/user/shavzak/back
python3 update_db.py
```

### בדיקת סטטוס המודל

```bash
GET /api/ml/stats
```

---

**מערכת זו מאפשרת למודל ללמוד ולהשתפר באופן אוטומטי, יוצרת שיבוצים טובים יותר עם הזמן!** 🎉
