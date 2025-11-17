# 🎖️ Shavzak Backend - מערכת שיבוץ חכמה עם AI

מערכת API מתקדמת לניהול שיבוצים צבאיים המשלבת **למידת מכונה (Machine Learning)** לשיבוץ חכם ואוטומטי.

המערכת לומדת מדוגמאות שיבוץ קיימות ומשתפרת עם כל פידבק מהמשתמש! 🤖

---

## 📖 הנחיות AI

**חשוב!** המערכת פועלת לפי 5 כללים מרכזיים שמוגדרים בקובץ:
### **[📋 AI_GUIDELINES.md](./AI_GUIDELINES.md) - הנחיות מלאות למערכת AI**

הכללים המרכזיים:
1. 🔄 **רוטציה לפי מחלקות** - שיבוץ מחלקתי עם רוטציה הוגנת (1→2→3→4)
2. 😴 **מקסימום שעות מנוחה** - עדיפות למי שנח הכי הרבה
3. 🔒 **אילוצים כלל ברזל** - אסור להפר (זמינות, מנוחה, הסמכות)
4. ⚡ **פידבק מיידי** - שינוי מיידי בשיבוץ + למידה מהפידבק
5. ✅ **אף פעם לא נכשל** - תמיד למצוא פתרון (Fallback בשכבות)

**קרא את המסמך המלא לפני עבודה על המערכת!**

---

## 🚀 תכונות עיקריות

### 🧠 שיבוץ חכם עם AI
- **אלגוריתם ML** שלומד מ-20+ דוגמאות שיבוץ
- **משתפר אוטומטית** עם פידבק מהמשתמש
- **ניקוד חיילים** לפי מנוחה, עומס, ודפוסים שנלמדו
- **רוטציה הוגנת** בין מחלקות

### ✅ אילוצים קשיחים
- מנוחה מינימלית (8 שעות)
- בדיקת זמינות (חופשות, ריתוק, התש"ב)
- דרישות הסמכה (נהג, חמל, וכו')
- מניעת חפיפות

### 📊 למידה מתמשכת
- אימון מדוגמאות שיבוץ טובות
- שמירת דפוסים שנלמדו
- מעקב אחרי הצלחות/כישלונים
- סטטיסטיקות ביצועים בזמן אמת

### 🎯 תכונות נוספות
- API RESTful מלא (40+ endpoints)
- מערכת הרשאות (מפ/ממ/מכ)
- JWT Authentication
- SQLite Database
- ניהול זמינות מתקדם

---

## ⚡ התקנה והפעלה

### דרישות מקדימות
```bash
Python >= 3.8
pip
numpy, scikit-learn (יותקן אוטומטית)
```

### התקנה
```bash
cd back
pip install -r requirements.txt
python setup.py  # יצירת מסד נתונים
```

### הפעלה
```bash
python api.py
```

השרת יעלה על: `http://localhost:5000`

אתה תראה:
```
✅ Smart Scheduler: מודל נטען מ-ml_model.pkl
או
⚠️ Smart Scheduler: אין מודל קיים - יש לאמן תחילה
```

---

## 🧠 מערכת ML - איך זה עובד?

### 1. **אילוצים קשיחים (Hard Constraints)**
דברים שאסור להפר:
```
✅ מנוחה מינימלית
✅ אי-זמינות (חופשות, התש"ב, ריתוק)
✅ הסמכות נדרשות
✅ ללא חפיפות בזמן
```

### 2. **העדפות רכות (Soft Preferences) - ML**
המודל לומד:
```
🎯 מי שנח יותר מקבל עדיפות
🎯 רוטציה הוגנת בין מחלקות
🎯 דפוסים (איזה חיילים טובים למשימה)
🎯 פידבק מהמשתמש (👍 / 👎)
```

### 3. **ניקוד חיילים**
כל חייל מקבל ציון למשימה לפי:

```python
score = (
    rest_hours * 2.0 +        # מנוחה
    -workload * 1.5 +          # עומס
    pattern_score * 3.0 +      # דפוסים שנלמדו
    -mahlaka_work * 0.5 +      # עומס מחלקה
    feedback_score * 4.0       # פידבק משתמש ⭐
)
```

**הציון הגבוה ביותר נבחר למשימה!**

---

## 🔌 API Endpoints החדשים

### `POST /api/ml/smart-schedule`
יצירת שיבוץ חכם עם ML

**Request:**
```json
{
  "pluga_id": 1,
  "start_date": "2025-01-01",
  "days_count": 7
}
```

**Response:**
```json
{
  "message": "נוצרו 42 משימות בהצלחה",
  "assignments": [...],
  "stats": {
    "total_assignments": 42,
    "approval_rate": 85.5,
    "patterns_learned": 47
  }
}
```

### `POST /api/ml/train`
אימון המודל מדוגמאות

**Request:**
```json
{
  "examples": [
    {
      "assignments": [
        {
          "type": "סיור",
          "soldiers": [1, 2, 3, 4],
          "day": 0,
          "start_hour": 8
        }
      ],
      "rating": "excellent"  // או "good" / "bad"
    }
  ]
}
```

### `POST /api/ml/feedback`
הוספת פידבק על שיבוץ

**Request:**
```json
{
  "assignment_id": 123,
  "rating": "approved",  // או "rejected" / "modified"
  "changes": {}
}
```

### `GET /api/ml/stats`
קבלת סטטיסטיקות ML

**Response:**
```json
{
  "stats": {
    "total_assignments": 150,
    "user_approvals": 128,
    "user_rejections": 14,
    "approval_rate": 85.3,
    "patterns_learned": 47,
    "feedback_count": 142
  }
}
```

### `POST /api/ml/upload-example`
העלאת דוגמת שיבוץ מתמונה

**Request:**
```json
{
  "image": "base64_encoded_image",
  "rating": "excellent"
}
```

---

## 📚 מדריך שימוש מלא

### שלב 1: הקמת מערכת
```bash
# 1. הרשמה כמפקד
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"commander1","password":"pass123","full_name":"משה כהן"}'

# 2. יצירת פלוגה
curl -X POST http://localhost:5000/api/plugot \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"פלוגה ב","gdud":"גדוד פנתר"}'

# 3. יצירת מחלקות (4 מחלקות)
curl -X POST http://localhost:5000/api/mahalkot \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number":1,"color":"#FF0000","pluga_id":1}'

# 4. הוספת חיילים
curl -X POST http://localhost:5000/api/soldiers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"דוד אברהם","role":"לוחם","mahlaka_id":1,"kita":"א"}'
```

### שלב 2: הגדרת תבניות משימות
```bash
curl -X POST http://localhost:5000/api/plugot/1/assignment-templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"סיור",
    "assignment_type":"סיור",
    "length_in_hours":8,
    "times_per_day":3,
    "commanders_needed":1,
    "drivers_needed":1,
    "soldiers_needed":2,
    "same_mahlaka_required":true
  }'
```

### שלב 3: אימון המודל (אופציונלי)
אם יש לך דוגמאות שיבוץ טובות:

```bash
curl -X POST http://localhost:5000/api/ml/train \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "examples": [
      {
        "assignments": [...],
        "rating": "excellent"
      }
    ]
  }'
```

### שלב 4: יצירת שיבוץ חכם
```bash
curl -X POST http://localhost:5000/api/ml/smart-schedule \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pluga_id": 1,
    "start_date": "2025-01-01",
    "days_count": 7
  }'
```

### שלב 5: מתן פידבק (שיפור המודל)
```bash
curl -X POST http://localhost:5000/api/ml/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assignment_id": 123,
    "rating": "approved"
  }'
```

---

## 📁 מבנה הקבצים

```
back/
├── api.py                    # Flask API server
├── smart_scheduler.py        # 🤖 ML Engine
├── models.py                 # Database models
├── auth.py                   # Authentication
├── config.py                 # Configuration
├── setup.py                  # DB setup
├── ml_model.pkl             # המודל השמור (נוצר אחרי אימון)
├── assignment_logic.py.backup  # גיבוי לוגיקה ישנה
└── README.md                 # המסמך הזה
```

---

## 🔧 קונפיגורציה

### הגדרות ML
ניתן לשנות ב-`smart_scheduler.py`:

```python
scheduler = SmartScheduler(
    min_rest_hours=8  # שעות מנוחה מינימליות
)
```

### כוונון משקולות
ניתן לכוונן את המשקולות ב-`calculate_soldier_score()`:

```python
score += rest_hours * 2.0       # משקל מנוחה
score -= workload * 1.5         # משקל עומס
score += pattern_score * 3.0    # משקל דפוסים
score += feedback_score * 4.0   # משקל פידבק
```

**משקל גבוה יותר = חשיבות רבה יותר**

---

## 📊 סטטיסטיקות ומעקב

המודל שומר ומעקב:
- ✅ כמות שיבוצים שנוצרו
- ✅ אישורים/דחיות מהמשתמש
- ✅ דירוג הצלחה (approval rate)
- ✅ דפוסים שנלמדו
- ✅ היסטוריית פידבק

גישה דרך:
```bash
GET /api/ml/stats
```

---

## 🐛 Debugging והדרכה

### לוגים
המערכת מדפיסה לוגים מפורטים:

```
🎖️  Shavzak API Server Starting...
✅ Smart Scheduler: מודל נטען מ-ml_model.pkl
📊 47 דפוסים נלמדו
🎓 מאמן מודל מ-20 דוגמאות...
✅ אימון הושלם!
```

### בדיקת מודל (Python)
```python
from smart_scheduler import SmartScheduler

scheduler = SmartScheduler()
scheduler.load_model('ml_model.pkl')

# סטטיסטיקות
print(scheduler.get_stats())

# דפוסים שנלמדו
print(scheduler.learned_patterns)

# היסטוריית פידבק
print(scheduler.user_feedback)
```

### פתרון בעיות נפוצות

**מודל לא נטען:**
```
⚠️ Smart Scheduler: אין מודל קיים
```
**פתרון:** אמן את המודל דרך `/api/ml/train`

**פורט תפוס:**
```bash
lsof -ti:5000 | xargs kill -9  # Linux/Mac
```

**Token לא עובד:**
- Token פג תוקף אחרי 7 ימים
- וודא שיש "Bearer " בתחילת ה-Token

---

## 🎯 תרומה לשיפור המודל

רוצה לשפר את ביצועי המודל?

1. **הוסף דוגמאות טובות** דרך `/api/ml/train`
2. **תן פידבק** על כל שיבוץ דרך `/api/ml/feedback`
3. **כוונן משקולות** ב-`smart_scheduler.py`
4. **בדוק סטטיסטיקות** דרך `/api/ml/stats`

**ככל שהמערכת תלמד יותר, היא תשתפר!** 🚀

---

## 🔐 אבטחה

⚠️ **לפני ייצור:**
1. שנה `SECRET_KEY` בקובץ `.env`
2. הגדר `DEBUG=False`
3. השתמש ב-HTTPS
4. עשה backup קבוע למסד הנתונים ול-`ml_model.pkl`

---

## 📊 מבנה מסד הנתונים

```
users               → משתמשים (מפקדים)
plugot              → פלוגות
mahalkot            → מחלקות
soldiers            → חיילים
certifications      → הסמכות
unavailable_dates   → תאריכים לא זמינים
assignment_templates → תבניות משימות
shavzakim           → שיבוצים
assignments         → משימות בשיבוץ
assignment_soldiers → קישור חיילים למשימות
soldier_status      → סטטוס חיילים
```

---

## 📝 רישיון

MIT License - ראה קובץ LICENSE

---

## 📞 תמיכה

שאלות? בעיות?
1. בדוק את `/api/health`
2. בדוק סטטיסטיקות ML ב-`/api/ml/stats`
3. ראה Debug למעלה
4. פתח issue ב-GitHub

---

**נבנה עם ❤️ ו-AI בישראל 🇮🇱**

**POWERED BY MACHINE LEARNING 🤖**
