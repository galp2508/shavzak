# 🎖️ Shavzak - מערכת ניהול שיבוצים צבאית

מערכת API מלאה לניהול שיבוצים (תורנויות) בפלוגה צבאית עם אלגוריתם שיבוץ חכם.

## ⚡ התחלה מהירה

```bash
# התקנה
pip install -r requirements.txt

# הפעלה
python api.py
```

או:
```bash
python setup.py  # התקנה אוטומטית
python api.py    # הפעלה
```

**השרת רץ על:** `http://localhost:5000`

---

## 🎯 תכונות עיקריות

✅ **API RESTful מלא** - 35+ endpoints  
✅ **מערכת הרשאות** - 3 רמות: מ"פ, מ"מ, מ"כ  
✅ **אלגוריתם שיבוץ חכם** - עם מצב חירום אוטומטי  
✅ **JWT Authentication** - אבטחה מלאה  
✅ **SQLite Database** - מסד נתונים מקומי  
✅ **ניהול זמינות** - סבבי בית, התש"ב, בקשות יציאה  
✅ **הסמכות** - מעקב אחרי כישורים מיוחדים  

---

## 📋 דרישות

- Python 3.8+
- pip

---

## 🚀 שימוש ראשון

### 1. רישום מ"פ
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"commander1","password":"pass123","full_name":"משה כהן"}'
```

**📌 שמור את ה-Token שחוזר!**

### 2. יצירת פלוגה
```bash
curl -X POST http://localhost:5000/api/plugot \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"פלוגה ב","gdud":"גדוד פנתר","color":"#BF092F"}'
```

### 3. יצירת מחלקות (4 מחלקות)
```bash
curl -X POST http://localhost:5000/api/mahalkot \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number":1,"color":"#FF0000","pluga_id":1}'
```

### 4. הוספת חיילים
```bash
curl -X POST http://localhost:5000/api/soldiers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"דוד אברהם","role":"לוחם","mahlaka_id":1,"kita":"א","home_round_date":"2024-11-01"}'
```

### 5. יצירת תבניות משימות
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

### 6. יצירת שיבוץ
```bash
curl -X POST http://localhost:5000/api/shavzakim \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"שיבוץ שבוע 46","start_date":"2024-11-10","days_count":7,"pluga_id":1}'
```

### 7. הרצת אלגוריתם השיבוץ
```bash
curl -X POST http://localhost:5000/api/shavzakim/1/generate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔐 הרשאות

| תפקיד | הרשאות |
|-------|---------|
| **מ"פ** | מנהל הכל בפלוגה, יוצר משתמשים, מחלקות, שיבוצים |
| **מ"מ** | רואה הכל, מנהל את המחלקה שלו, יוצר מ"כ, יוצר שיבוצים |
| **מ"כ** | רואה הכל, מנהל את הכיתה שלו |

---

## 📡 API Endpoints

### Authentication
- `POST /api/register` - רישום
- `POST /api/login` - התחברות
- `POST /api/users` - יצירת משתמש

### Pluga (פלוגה)
- `POST /api/plugot` - יצירה
- `GET /api/plugot/{id}` - קריאה

### Mahalkot (מחלקות)
- `POST /api/mahalkot` - יצירה
- `GET /api/plugot/{id}/mahalkot` - רשימה

### Soldiers (חיילים)
- `POST /api/soldiers` - יצירה
- `GET /api/soldiers/{id}` - קריאה
- `DELETE /api/soldiers/{id}` - מחיקה
- `GET /api/mahalkot/{id}/soldiers` - רשימה
- `POST /api/soldiers/{id}/certifications` - הוספת הסמכה
- `POST /api/soldiers/{id}/unavailable` - תאריך לא זמין

### Assignment Templates (תבניות)
- `POST /api/plugot/{id}/assignment-templates` - יצירה
- `GET /api/plugot/{id}/assignment-templates` - רשימה

### Shavzakim (שיבוצים)
- `POST /api/shavzakim` - יצירת שיבוץ
- `POST /api/shavzakim/{id}/generate` - **הרצת אלגוריתם השיבוץ**
- `GET /api/shavzakim/{id}` - קבלת שיבוץ
- `GET /api/plugot/{id}/shavzakim` - רשימה

### Utilities
- `GET /api/health` - בדיקת תקינות

---

## 🧮 אלגוריתם השיבוץ

האלגוריתם:
1. ✅ **מאזן עומס** - מפזר שעות באופן שווה בין חיילים
2. ✅ **שומר על מנוחה** - מינימום 8 שעות מנוחה
3. ✅ **מעדיף מחלקות** - משתמש במחלקות שעבדו פחות
4. ✅ **מצב חירום אוטומטי** - אם אין מספיק כוח אדם, מקל על הדרישות
5. ✅ **אזהרות** - מודיע על מצבים חריגים

### תבניות משימות נתמכות:
- סיור - מחלקה שלמה
- שמירה - חייל בודד
- כוננות א/ב - צוותים גדולים
- חמל - דורש הסמכה
- תורן מטבח - 24 שעות
- חפ"ק גשש, של"ז - משימות מיוחדות
- קצין תורן - מפקד בכיר

---

## 🛡️ אבטחה

⚠️ **לפני ייצור:**
1. שנה `SECRET_KEY` ב-.env
2. הגדר `DEBUG=False`
3. השתמש ב-HTTPS
4. עשה backup למסד הנתונים

---

## 📊 מבנה מסד הנתונים

```
users          → משתמשים (מפקדים)
plugot         → פלוגות
mahalkot       → מחלקות
soldiers       → חיילים
certifications → הסמכות
unavailable_dates → תאריכים לא זמינים
assignment_templates → תבניות משימות
shavzakim      → שיבוצים
assignments    → משימות בשיבוץ
assignment_soldiers → קישור חיילים למשימות
```

---

## 🐛 פתרון בעיות

### פורט תפוס:
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Token לא עובד:
- וודא ש-Token מתחיל ב-"Bearer "
- Token פג תוקף אחרי 7 ימים - עשה Login מחדש

### איפוס מסד נתונים:
```bash
rm shavzak.db
python setup.py
```

### שגיאת "no such column" בטבלת unavailable_dates:
אם אתה מקבל שגיאה כמו:
```
sqlite3.OperationalError: no such column: unavailable_dates.end_date
```

**הפתרון:**
```bash
# הרצת migration ידנית
python run_migration.py

# או פשוט הפעל את השרת - Migration ירוץ אוטומטית
python api.py
```

**המערכת תזהה אוטומטית** שדות חסרים ותריץ migration בעת אתחול השרת.

---

## 🔄 דוגמה מלאה (Python)

```python
import requests

BASE = "http://localhost:5000/api"

# Login
r = requests.post(f"{BASE}/login", json={
    "username": "commander1",
    "password": "pass123"
})
token = r.json()['token']

# Headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create Soldier
requests.post(f"{BASE}/soldiers", 
    json={"name": "דוד", "role": "לוחם", "mahlaka_id": 1, "kita": "א"},
    headers=headers
)

# Generate Shavzak
requests.post(f"{BASE}/shavzakim/1/generate", headers=headers)
```

---

## 📝 הערות חשובות

1. **הכל דינמי** - אין קוד מובנה, הכל מוגדר דרך ה-API
2. **Token נדרש** - כל בקשה (מלבד register/login) צריכה Token
3. **הרשאות אוטומטיות** - המערכת בודקת מה אתה יכול
4. **סבבי בית אוטומטיים** - המערכת מחשבת לפי תאריך סבב אחרון
5. **מצב חירום** - אם אין מספיק כוח אדם, האלגוריתם מצליח בכל מחיר

---

## 🎯 תכונות עתידיות

- [ ] Frontend (React)
- [ ] אפליקציית מובייל
- [ ] יצוא ל-Excel/PDF
- [ ] התראות במייל
- [ ] דשבורד אנליטי

---

## 📞 תמיכה

יש בעיה?
1. בדוק את `/api/health`
2. בדוק שהפורט 5000 פנוי
3. וודא ש-Token תקף
4. ראה פתרון בעיות למעלה

---

**נבנה בגאווה לצה"ל 🇮🇱**
