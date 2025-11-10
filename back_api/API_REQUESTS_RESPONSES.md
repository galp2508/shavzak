# 📡 סיכום בקשות ותגובות API - Shavzak System

## מבנה כללי

**Base URL:** `http://localhost:5000/api`

**Authentication Header:**
```
Authorization: Bearer <jwt_token>
```

---

## 🔐 AUTHENTICATION

### רישום
```
POST /api/register
Body: {username, password, full_name}
→ 201: {message, token, user: {id, username, full_name, role}}
```

### התחברות
```
POST /api/login
Body: {username, password}
→ 200: {message, token, user: {id, username, full_name, role, pluga_id, mahlaka_id, kita}}
→ 401: {error: "שם משתמש או סיסמה שגויים"}
```

### יצירת משתמש
```
POST /api/users [מפ, ממ]
Body: {username, password, full_name, role, pluga_id, mahlaka_id, kita}
→ 201: {message, user: {id, username, full_name, role}}
→ 403: {error: "אין לך הרשאה"}
```

---

## 🏢 PLUGA (פלוגה)

### יצירת פלוגה
```
POST /api/plugot [מפ]
Body: {name, gdud, color}
→ 201: {message, pluga: {id, name, gdud, color}}
```

### קבלת פלוגה
```
GET /api/plugot/{pluga_id}
→ 200: {pluga: {id, name, gdud, color, mahalkot_count}}
→ 403: {error: "אין לך הרשאה"}
→ 404: {error: "פלוגה לא נמצאה"}
```

### עדכון פלוגה
```
PUT /api/plugot/{pluga_id} [מפ]
Body: {name?, gdud?, color?}
→ 200: {message: "פלוגה עודכנה בהצלחה"}
```

---

## 📦 MAHLAKA (מחלקה)

### יצירת מחלקה
```
POST /api/mahalkot [מפ]
Body: {number, color, pluga_id}
→ 201: {message, mahlaka: {id, number, color}}
```

### קבלת מחלקה
```
GET /api/mahalkot/{mahlaka_id}
→ 200: {mahlaka: {id, number, color, pluga_id, stats: {total_soldiers, commanders, drivers, soldiers}}}
```

### רשימת מחלקות
```
GET /api/plugot/{pluga_id}/mahalkot
→ 200: {mahalkot: [{id, number, color, soldiers_count}, ...]}
```

---

## 👤 SOLDIER (חייל)

### יצירת חייל
```
POST /api/soldiers [מפ=כולם, ממ=מחלקה, מכ=כיתה]
Body: {
  name, role, mahlaka_id, kita,
  idf_id?, personal_id?, sex?, phone_number?, address?,
  emergency_contact_name?, emergency_contact_number?,
  pakal?, recruit_date?, birth_date?, home_round_date?,
  is_platoon_commander?, has_hatashab?,
  certifications?: []
}
→ 201: {message, soldier: {id, name, role, kita}}
```

### קבלת חייל
```
GET /api/soldiers/{soldier_id}
→ 200: {soldier: {
  id, name, role, kita, idf_id, personal_id, sex,
  phone_number, address, emergency_contact_name, emergency_contact_number,
  pakal, recruit_date, birth_date, home_round_date,
  is_platoon_commander, has_hatashab, mahlaka_id,
  certifications: [], unavailable_dates: [{id, date, reason, status}, ...]
}}
```

### עדכון חייל
```
PUT /api/soldiers/{soldier_id} [מפ, ממ, מכ]
Body: {כל שדה שרוצים לעדכן}
→ 200: {message: "חייל עודכן בהצלחה"}
```

### מחיקת חייל
```
DELETE /api/soldiers/{soldier_id} [מפ, ממ, מכ]
→ 200: {message: "חייל נמחק בהצלחה"}
```

### רשימת חיילים במחלקה
```
GET /api/mahalkot/{mahlaka_id}/soldiers
→ 200: {soldiers: [{id, name, role, kita, certifications: [], is_platoon_commander, has_hatashab}, ...]}
```

---

## 🎖️ CERTIFICATIONS & UNAVAILABILITY

### הוספת הסמכה
```
POST /api/soldiers/{soldier_id}/certifications
Body: {certification_name}
→ 201: {message: "הסמכה נוספה בהצלחה"}
```

### הוספת תאריך לא זמין
```
POST /api/soldiers/{soldier_id}/unavailable
Body: {date: "YYYY-MM-DD", reason?, status?: "approved"}
→ 201: {message: "תאריך נוסף בהצלחה"}
```

### מחיקת תאריך לא זמין
```
DELETE /api/unavailable/{unavailable_id}
→ 200: {message: "תאריך נמחק בהצלחה"}
```

---

## 📋 ASSIGNMENT TEMPLATES (תבניות משימות)

### יצירת תבנית
```
POST /api/plugot/{pluga_id}/assignment-templates [מפ]
Body: {
  name, assignment_type, length_in_hours, times_per_day,
  commanders_needed?, drivers_needed?, soldiers_needed?,
  same_mahlaka_required?, requires_certification?,
  requires_senior_commander?
}
→ 201: {message, template: {id, name, assignment_type}}
```

### רשימת תבניות
```
GET /api/plugot/{pluga_id}/assignment-templates
→ 200: {templates: [{
  id, name, assignment_type, length_in_hours, times_per_day,
  commanders_needed, drivers_needed, soldiers_needed,
  same_mahlaka_required, requires_certification, requires_senior_commander
}, ...]}
```

---

## 📅 SHAVZAK (שיבוץ)

### יצירת שיבוץ
```
POST /api/shavzakim [מפ, ממ]
Body: {
  name, start_date: "YYYY-MM-DD", days_count,
  pluga_id?, min_rest_hours?: 8, emergency_mode?: false
}
→ 201: {message, shavzak: {id, name, start_date, days_count}}
```

### הרצת אלגוריתם שיבוץ
```
POST /api/shavzakim/{shavzak_id}/generate [מפ, ממ]
Body: {emergency_mode?: false}
→ 200: {
  message: "שיבוץ בוצע בהצלחה",
  warnings: ["..."],
  stats: {total_assignments, emergency_assignments}
}
```

### קבלת שיבוץ
```
GET /api/shavzakim/{shavzak_id}
→ 200: {
  shavzak: {id, name, start_date, days_count, created_at, min_rest_hours, emergency_mode},
  assignments: [{
    id, name, type, day, start_hour, length_in_hours,
    assigned_mahlaka_id,
    soldiers: [{id, name, role}, ...]
  }, ...]
}
```

### רשימת שיבוצים
```
GET /api/plugot/{pluga_id}/shavzakim
→ 200: {shavzakim: [{id, name, start_date, days_count, created_at}, ...]}
```

---

## 🔧 UTILITY

### מידע משתמש נוכחי
```
GET /api/me
→ 200: {user: {
  id, username, full_name, role,
  pluga: {id, name}?,
  mahlaka: {id, number}?,
  kita, last_login
}}
```

### סטטיסטיקות
```
GET /api/stats
→ 200: {stats: {
  mahalkot, total_soldiers, commanders, drivers, soldiers, shavzakim
}}
```

### בדיקת תקינות
```
GET /api/health
→ 200: {status: "healthy", message: "Shavzak API is running"}
```

---

## ❌ שגיאות נפוצות

| Code | Error | משמעות |
|------|-------|---------|
| 400 | Bad Request | נתונים לא תקינים |
| 401 | Unauthorized | חסר token או token לא תקף |
| 403 | Forbidden | אין הרשאה לפעולה |
| 404 | Not Found | משאב לא נמצא |
| 500 | Internal Server Error | שגיאת שרת |

**פורמט שגיאה:**
```json
{
  "error": "הסבר השגיאה בעברית"
}
```

---

## 🎯 הרשאות לפי תפקיד

| תפקיד | הרשאות |
|-------|---------|
| **מ"פ** | כל הפעולות בפלוגה |
| **מ"מ** | צפייה בכל הפלוגה, עריכת המחלקה שלו, יצירת שיבוצים |
| **מ"כ** | צפייה בכל הפלוגה, עריכת הכיתה שלו |

---

## 📌 דוגמאות מהירות

### התחלה מלאה (Bash)
```bash
# 1. רישום
TOKEN=$(curl -s -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"cmd1","password":"pass","full_name":"משה"}' \
  | jq -r '.token')

# 2. יצירת פלוגה
curl -X POST http://localhost:5000/api/plugot \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"פלוגה ב","gdud":"פנתר","color":"#FF0000"}'

# 3. יצירת מחלקה
curl -X POST http://localhost:5000/api/mahalkot \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"number":1,"color":"#00FF00","pluga_id":1}'

# 4. הוספת חייל
curl -X POST http://localhost:5000/api/soldiers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"דוד","role":"לוחם","mahlaka_id":1,"kita":"א"}'
```

### Python
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
r = requests.post(f"{BASE}/soldiers", 
    json={"name": "דוד", "role": "לוחם", "mahlaka_id": 1, "kita": "א"},
    headers=headers
)
print(r.json())
```

---

## 🔗 קישורים מהירים

- **מדריך מלא**: README.md
- **תיעוד מפורט**: API_DOCUMENTATION.md
- **התחלה מהירה**: QUICKSTART.md
- **דוגמה חיה**: example_usage.py

---

**סיכום:** המערכת מספקת API מלא עם 35+ endpoints לניהול שיבוצים צבאיים! 🎖️
