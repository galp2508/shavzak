# 🎖️ Shavzak System - Project Index

## תיאור הפרויקט
מערכת ניהול שיבוצים (תורנויות) צבאית מקצועית עם:
- ✅ **API Server מלא** (Flask + SQLite)
- ✅ **מערכת הרשאות** (3 רמות: מ"פ, מ"מ, מ"כ)
- ✅ **JWT Authentication**
- ✅ **אלגוריתם שיבוץ חכם**
- ✅ **תמיכה מלאה בעברית**

---

## 📁 קבצי הפרויקט

### קבצי קוד ראשיים:

| קובץ | תיאור | חשיבות |
|------|--------|---------|
| **api.py** | השרת הראשי - כל ה-endpoints | ⭐⭐⭐⭐⭐ |
| **models.py** | מבנה מסד הנתונים (SQLAlchemy) | ⭐⭐⭐⭐⭐ |
| **auth.py** | מערכת אימות והרשאות (JWT) | ⭐⭐⭐⭐⭐ |
| **config.py** | הגדרות המערכת | ⭐⭐⭐ |
| **requirements.txt** | תלויות Python | ⭐⭐⭐⭐⭐ |

### קבצי עזר:

| קובץ | תיאור |
|------|--------|
| **setup.py** | סקריפט התקנה אוטומטי |
| **example_usage.py** | דוגמה מלאה לשימוש |
| **.env.example** | דוגמה למשתני סביבה |
| **.gitignore** | קבצים להתעלם מהם ב-Git |

### תיעוד:

| קובץ | תיאור | למי? |
|------|--------|------|
| **README.md** | מדריך מקיף מלא | כולם |
| **QUICKSTART.md** | התחלה מהירה (5 דקות) | מתחילים |
| **API_DOCUMENTATION.md** | תיעוד מפורט של כל endpoint | מפתחים |
| **API_REQUESTS_RESPONSES.md** | סיכום בקשות/תגובות | מפתחים |

---

## 🚀 התחלה מהירה

### אופציה 1: התקנה אוטומטית
```bash
python setup.py
python api.py
```

### אופציה 2: ידני
```bash
pip install -r requirements.txt
python api.py
```

### אופציה 3: דוגמה מלאה
```bash
python setup.py
python api.py  # בטרמינל אחד
python example_usage.py  # בטרמינל אחר
```

---

## 📊 מבנה מסד הנתונים

```
users (משתמשים)
├── id, username, password_hash, full_name, role
├── pluga_id, mahlaka_id, kita
└── created_at, last_login

plugot (פלוגות)
├── id, name, gdud, color
└── created_at

mahalkot (מחלקות)
├── id, number, color
└── pluga_id [FK]

soldiers (חיילים)
├── id, name, idf_id, personal_id
├── role, kita, sex
├── phone_number, address, emergency contacts
├── pakal, dates (recruit, birth, home_round)
├── is_platoon_commander, has_hatashab
└── mahlaka_id [FK]

certifications (הסמכות)
├── id, soldier_id [FK]
└── certification_name, date_acquired

unavailable_dates (תאריכים לא זמינים)
├── id, soldier_id [FK]
├── date, reason, status
└── (סבבי בית, התשב, בקשות יציאה)

assignment_templates (תבניות משימות)
├── id, pluga_id [FK]
├── name, assignment_type
├── length_in_hours, times_per_day
└── requirements (commanders, drivers, soldiers)

shavzakim (שיבוצים)
├── id, pluga_id [FK]
├── name, start_date, days_count
├── created_by [FK], created_at
└── min_rest_hours, emergency_mode

assignments (משימות בשיבוץ)
├── id, shavzak_id [FK]
├── name, assignment_type
├── day, start_hour, length_in_hours
└── assigned_mahlaka_id [FK]

assignment_soldiers (קישור חיילים למשימות)
├── id, assignment_id [FK]
├── soldier_id [FK]
└── role_in_assignment
```

---

## 🔐 הרשאות

### מ"פ (מפקד פלוגה)
```
✅ מנהל הכל בפלוגה
✅ יוצר משתמשים (מ"מ, מ"כ)
✅ יוצר מחלקות, חיילים, תבניות, שיבוצים
✅ עורך הכל
```

### מ"מ (מפקד מחלקה)
```
✅ רואה כל הפלוגה
✅ מנהל את המחלקה שלו
✅ יוצר מ"כ במחלקה שלו
✅ יוצר שיבוצים
❌ לא יכול לערוך מחלקות אחרות
```

### מ"כ (מפקד כיתה)
```
✅ רואה כל הפלוגה
✅ מנהל את הכיתה שלו
❌ לא יכול ליצור משתמשים
❌ לא יכול ליצור שיבוצים
```

---

## 🔌 35+ API Endpoints

### Authentication (3)
- POST `/api/register` - רישום
- POST `/api/login` - התחברות
- POST `/api/users` - יצירת משתמש

### Plugot (3)
- POST `/api/plugot` - יצירה
- GET `/api/plugot/{id}` - קריאה
- PUT `/api/plugot/{id}` - עדכון

### Mahalkot (3)
- POST `/api/mahalkot` - יצירה
- GET `/api/mahalkot/{id}` - קריאה
- GET `/api/plugot/{id}/mahalkot` - רשימה

### Soldiers (5)
- POST `/api/soldiers` - יצירה
- GET `/api/soldiers/{id}` - קריאה
- PUT `/api/soldiers/{id}` - עדכון
- DELETE `/api/soldiers/{id}` - מחיקה
- GET `/api/mahalkot/{id}/soldiers` - רשימה

### Certifications & Unavailability (3)
- POST `/api/soldiers/{id}/certifications` - הוספת הסמכה
- POST `/api/soldiers/{id}/unavailable` - תאריך לא זמין
- DELETE `/api/unavailable/{id}` - מחיקת תאריך

### Assignment Templates (2)
- POST `/api/plugot/{id}/assignment-templates` - יצירה
- GET `/api/plugot/{id}/assignment-templates` - רשימה

### Shavzakim (4)
- POST `/api/shavzakim` - יצירת שיבוץ
- POST `/api/shavzakim/{id}/generate` - הרצת אלגוריתם
- GET `/api/shavzakim/{id}` - קריאת שיבוץ
- GET `/api/plugot/{id}/shavzakim` - רשימת שיבוצים

### Utilities (3)
- GET `/api/me` - מידע משתמש
- GET `/api/stats` - סטטיסטיקות
- GET `/api/health` - בדיקת תקינות

---

## 🛠️ טכנולוגיות

| קטגוריה | טכנולוגיה |
|----------|-----------|
| **Backend** | Python 3.8+, Flask 3.0 |
| **Database** | SQLite3, SQLAlchemy 2.0 |
| **Auth** | JWT (PyJWT), bcrypt |
| **CORS** | Flask-CORS |
| **Environment** | python-dotenv |

---

## 📖 איך להשתמש בתיעוד?

### אם אתה חדש:
1. קרא **QUICKSTART.md** (5 דקות)
2. הרץ **setup.py** ו-**example_usage.py**
3. התחל לעבוד!

### אם אתה מפתח:
1. קרא **README.md** - מדריך מלא
2. קרא **API_DOCUMENTATION.md** - כל ה-endpoints
3. השתמש ב-**API_REQUESTS_RESPONSES.md** כ-cheatsheet

### אם אתה מבצע deploy:
1. שנה את `SECRET_KEY` ב-.env
2. הגדר `DEBUG=False`
3. השתמש ב-HTTPS
4. הגדר backup ל-DB

---

## 🎯 תכונות מיוחדות

### אלגוריתם שיבוץ חכם:
- ✅ מאזן עומס בין חיילים
- ✅ שומר על מנוחה מינימלית (8 שעות)
- ✅ מעדיף מחלקות שעבדו פחות
- ✅ מצב חירום אוטומטי אם אין מספיק כוח אדם
- ✅ אזהרות על מצבים חריגים

### ניהול זמינות מתקדם:
- ✅ סבבי בית אוטומטיים (כל 21-24 יום)
- ✅ התש"ב (ימים ה', ו', שבת)
- ✅ בקשות יציאה
- ✅ הפניות רפואיות
- ✅ תאריכים מותאמים אישית

### אבטחה:
- ✅ הצפנת סיסמאות (bcrypt)
- ✅ JWT tokens עם תפוגה
- ✅ בדיקת הרשאות בכל endpoint
- ✅ CORS מוגדר
- ✅ SQL Injection protected (SQLAlchemy)

---

## 🐛 פתרון בעיות

### השרת לא עולה:
```bash
# בדוק שהפורט 5000 פנוי
lsof -ti:5000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :5000   # Windows
```

### שגיאת תלויות:
```bash
pip install -r requirements.txt --upgrade
```

### בעיות DB:
```bash
# אתחל מחדש
rm shavzak.db
python setup.py
```

### Token לא עובד:
- וודא שהוא מתחיל ב-"Bearer "
- Token פג תוקף אחרי 7 ימים
- עשה login מחדש

---

## 📞 תמיכה

**יש שאלה?**
1. חפש ב-**API_DOCUMENTATION.md**
2. בדוק ב-**README.md**
3. הרץ את **example_usage.py**
4. פתח Issue

---

## 🔮 תכונות עתידיות

- [ ] Frontend (React/Vue)
- [ ] אפליקציית מובייל
- [ ] יצוא ל-Excel/PDF
- [ ] התראות במייל/SMS
- [ ] דשבורד אנליטי
- [ ] אינטגרציה עם מערכות צה"ל

---

## 📝 רשיון
פרויקט Open Source לשימוש צבאי/ארגוני

---

## 🎖️ סיכום

**הפרויקט מוכן לשימוש מיידי!**

✅ כל הקוד מוכן  
✅ מסד נתונים מוגדר  
✅ API מלא ומתועד  
✅ דוגמאות שימוש  
✅ מערכת הרשאות מלאה  
✅ אבטחה מובנית  

**התחל עכשיו:**
```bash
python setup.py && python api.py
```

**בהצלחה! 🚀**

---

נבנה בגאווה לצה"ל 🇮🇱
