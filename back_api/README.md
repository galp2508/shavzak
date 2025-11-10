# 🎖️ Shavzak - מערכת ניהול שיבוצים צבאית

מערכת מתקדמת לניהול שיבוצים (תורנויות) בפלוגה צבאית, עם API מלא ומערכת הרשאות מובנית.

## 🚀 תכונות עיקריות

- ✅ **API RESTful מלא** - ממשק שרת מקצועי
- ✅ **מערכת הרשאות** - 3 רמות: מ"פ, מ"מ, מ"כ
- ✅ **אבטחה מלאה** - JWT Authentication
- ✅ **מסד נתונים** - SQLite3 עם SQLAlchemy
- ✅ **אלגוריתם שיבוץ חכם** - כולל מצב חירום
- ✅ **ניהול זמינות** - סבבי בית, התש"ב, בקשות יציאה
- ✅ **הסמכות** - מעקב אחרי כישורים מיוחדים
- ✅ **תמיכה מלאה בעברית**

## 📋 דרישות מערכת

- Python 3.8+
- pip (Python package manager)
- SQLite3 (מובנה ב-Python)

## 🔧 התקנה

### 1. שכפול/הורדת הפרויקט

```bash
# אם יש Git
git clone <repository-url>
cd shavzak

# או פשוט הורד והוצא את הקבצים לתיקייה
```

### 2. יצירת סביבה וירטואלית (מומלץ)

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. התקנת תלויות

```bash
pip install -r requirements.txt
```

### 4. הגדרת משתני סביבה

```bash
# העתק את קובץ הדוגמה
cp .env.example .env

# ערוך את .env ושנה את SECRET_KEY בייצור!
nano .env  # או כל עורך טקסט
```

### 5. הפעלת השרת

```bash
python api.py
```

השרת יעלה ויהיה זמין בכתובת:
```
http://localhost:5000
```

## 📚 מבנה הפרויקט

```
shavzak/
│
├── api.py                      # שרת Flask הראשי
├── models.py                   # מודלים של מסד הנתונים
├── auth.py                     # מערכת אימות והרשאות
├── config.py                   # הגדרות
├── requirements.txt            # תלויות Python
├── .env.example               # דוגמה למשתני סביבה
├── API_DOCUMENTATION.md       # תיעוד מלא של ה-API
├── README.md                  # הקובץ הזה
│
├── shavzak.db                 # מסד הנתונים (ייווצר אוטומטית)
│
└── back/                      # קוד מקורי (לעיון)
    ├── assignment_logic.py
    ├── assignment_types.py
    ├── soldier.py
    └── ...
```

## 🎯 שימוש ראשוני - Quick Start

### שלב 1: הרשמה ויצירת מ"פ ראשון

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "commander1",
    "password": "securePassword123",
    "full_name": "משה כהן"
  }'
```

תקבל token - שמור אותו!

### שלב 2: יצירת פלוגה

```bash
curl -X POST http://localhost:5000/api/plugot \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "name": "פלוגה ב",
    "gdud": "גדוד פנתר",
    "color": "#BF092F"
  }'
```

### שלב 3: יצירת מחלקות

```bash
curl -X POST http://localhost:5000/api/mahalkot \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "number": 1,
    "color": "#FF5733",
    "pluga_id": 1
  }'
```

חזור על זה 4 פעמים למספרי מחלקות שונים.

### שלב 4: הוספת חיילים

```bash
curl -X POST http://localhost:5000/api/soldiers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "name": "דוד אברהם",
    "role": "לוחם",
    "mahlaka_id": 1,
    "kita": "א",
    "home_round_date": "2024-11-01"
  }'
```

### שלב 5: יצירת תבניות משימות

```bash
curl -X POST http://localhost:5000/api/plugot/1/assignment-templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "name": "סיור",
    "assignment_type": "סיור",
    "length_in_hours": 8,
    "times_per_day": 3,
    "commanders_needed": 1,
    "drivers_needed": 1,
    "soldiers_needed": 2,
    "same_mahlaka_required": true
  }'
```

### שלב 6: יצירת שיבוץ

```bash
curl -X POST http://localhost:5000/api/shavzakim \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "name": "שיבוץ שבוע 46",
    "start_date": "2024-11-10",
    "days_count": 7,
    "pluga_id": 1
  }'
```

## 🔐 מערכת ההרשאות

### מ"פ (מפקד פלוגה)
- מנהל **הכל** בפלוגה
- יכול ליצור משתמשים (מ"מ, מ"כ)
- מנהל כל המחלקות והחיילים
- יוצר תבניות משימות ושיבוצים

### מ"מ (מפקד מחלקה)
- רואה את **כל** הפלוגה
- מנהל את **המחלקה שלו בלבד**
- יכול ליצור מ"כ במחלקה שלו
- יכול ליצור שיבוצים

### מ"כ (מפקד כיתה)
- רואה את **כל** הפלוגה
- מנהל את **הכיתה שלו בלבד**
- לא יכול ליצור משתמשים או שיבוצים

## 📖 תיעוד API מלא

ראה את הקובץ [API_DOCUMENTATION.md](API_DOCUMENTATION.md) לתיעוד מפורט של כל ה-endpoints.

### Endpoints עיקריים:

- **Authentication**: `/api/register`, `/api/login`
- **Plugot**: `/api/plugot/*`
- **Mahalkot**: `/api/mahalkot/*`
- **Soldiers**: `/api/soldiers/*`
- **Shavzakim**: `/api/shavzakim/*`
- **Utilities**: `/api/me`, `/api/stats`, `/api/health`

## 🧪 בדיקות

### בדיקת תקינות השרת:

```bash
curl http://localhost:5000/api/health
```

אמור להחזיר:
```json
{
  "status": "healthy",
  "message": "Shavzak API is running"
}
```

## 🐛 פתרון בעיות נפוצות

### שגיאה: "ModuleNotFoundError"
```bash
# וודא שהתקנת את כל התלויות
pip install -r requirements.txt
```

### שגיאה: "Port 5000 is already in use"
```bash
# שנה את הפורט ב-.env או הרוג את התהליך שתופס את 5000
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### שגיאה: "Database is locked"
```bash
# סגור את כל החיבורים למסד הנתונים
# אם צריך, מחק את shavzak.db ותתחיל מחדש
rm shavzak.db
```

### בעיות עם Token
- וודא שה-Token מתחיל ב-"Bearer "
- Token פג תוקף אחרי 7 ימים - עשה Login מחדש
- שמור את ה-SECRET_KEY קבוע (אל תשנה בין הרצות)

## 🔄 עדכון המערכת

```bash
# משוך עדכונים אם יש
git pull

# עדכן תלויות
pip install -r requirements.txt --upgrade

# הפעל מחדש את השרת
python api.py
```

## 🛡️ אבטחה - חשוב!

⚠️ **לפני ייצור (Production):**

1. שנה את `SECRET_KEY` ב-.env למשהו ארוך ואקראי
2. הגדר `DEBUG=False`
3. השתמש ב-HTTPS (לא HTTP)
4. הגדר מגבלות rate-limiting
5. שמור על גיבוי של מסד הנתונים
6. אל תעלה את .env ל-Git!

## 📊 מסד הנתונים

המערכת משתמשת ב-SQLite3 עם המבנה הבא:

- **users** - משתמשים (מפקדים)
- **plugot** - פלוגות
- **mahalkot** - מחלקות
- **soldiers** - חיילים
- **certifications** - הסמכות
- **unavailable_dates** - תאריכים לא זמינים
- **assignment_templates** - תבניות משימות
- **shavzakim** - שיבוצים
- **assignments** - משימות בשיבוץ
- **assignment_soldiers** - קישור חיילים למשימות

## 🤝 תרומה

אם אתה רוצה לתרום לפרויקט:

1. Fork את הפרויקט
2. צור branch חדש (`git checkout -b feature/amazing-feature`)
3. Commit השינויים (`git commit -m 'Add amazing feature'`)
4. Push ל-branch (`git push origin feature/amazing-feature`)
5. פתח Pull Request

## 📝 רישיון

פרויקט זה הוא open source ונועד לשימוש צבאי/ארגוני.

## 📞 תמיכה

יש בעיה? שאלה?

1. בדוק את [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. חפש ב-Issues קיימים
3. פתח Issue חדש

## 🎯 תכונות עתידיות (Roadmap)

- [ ] ממשק גרפי (Frontend) - React/Vue
- [ ] יצוא לקבצים (Excel, PDF)
- [ ] התראות וסיכומים במייל
- [ ] אפליקציית מובייל
- [ ] תמיכה במספר פלוגות במקביל
- [ ] מערכת דיווחים מתקדמת
- [ ] אינטגרציה עם מערכות צה"ל

## ⭐ תודות

פרויקט זה מבוסס על הצורך האמיתי לפתור את בעיית השיבוצים בצה"ל.
תודה לכל המפקדים שסייעו בהבנת הצרכים!

---

**נבנה בגאווה לצה"ל 🇮🇱**
