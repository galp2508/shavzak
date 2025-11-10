# 🚀 QUICK START - התחלה מהירה

## התקנה מהירה (5 דקות)

### 1. התקנת תלויות
```bash
pip install -r requirements.txt
```

### 2. הרצת Setup
```bash
python setup.py
```

### 3. הפעלת השרת
```bash
python api.py
```

השרת רץ על: `http://localhost:5000`

---

## בדיקה מהירה

### בדוק שהשרת עובד:
```bash
curl http://localhost:5000/api/health
```

אמור להחזיר:
```json
{"status": "healthy", "message": "Shavzak API is running"}
```

---

## דוגמה מלאה אוטומטית

הרץ את הסקריפט להקמת מערכת מלאה:
```bash
python example_usage.py
```

הסקריפט יצור:
- ✅ משתמש מ"פ
- ✅ פלוגה אחת
- ✅ 4 מחלקות
- ✅ 10 חיילים
- ✅ 3 תבניות משימות
- ✅ שיבוץ אחד

---

## רישום ידני ראשון

### 1. הירשם (משתמש ראשון = מ"פ):
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "commander1",
    "password": "pass123",
    "full_name": "משה כהן"
  }'
```

**שמור את ה-token שחוזר!**

### 2. צור פלוגה:
```bash
curl -X POST http://localhost:5000/api/plugot \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "פלוגה ב",
    "gdud": "גדוד פנתר",
    "color": "#BF092F"
  }'
```

### 3. המשך לפי התיעוד המלא
ראה: **API_DOCUMENTATION.md**

---

## קבצים חשובים

| קובץ | תיאור |
|------|--------|
| `api.py` | השרת הראשי |
| `models.py` | מבנה מסד הנתונים |
| `auth.py` | מערכת הרשאות |
| `API_DOCUMENTATION.md` | תיעוד מלא |
| `README.md` | מדריך מקיף |
| `example_usage.py` | דוגמת שימוש |
| `setup.py` | התקנה אוטומטית |

---

## צריך עזרה?

1. קרא את **README.md** - מדריך מלא
2. קרא את **API_DOCUMENTATION.md** - תיעוד endpoints
3. הרץ את **example_usage.py** - דוגמה חיה

---

**בהצלחה! 🎖️**
