# Shavzak API Documentation
# תיעוד מלא של API למערכת השיבוצים

## Base URL
```
http://localhost:5000/api
```

## Authentication
כל ה-endpoints (מלבד register ו-login) דורשים JWT token ב-header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 1. AUTHENTICATION ENDPOINTS

### 1.1 Register (רישום משתמש ראשון)
**POST** `/register`

**Body:**
```json
{
  "username": "commander1",
  "password": "securePassword123",
  "full_name": "משה כהן"
}
```

**Response (201):**
```json
{
  "message": "משתמש נוצר בהצלחה",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "commander1",
    "full_name": "משה כהן",
    "role": "מפ"
  }
}
```

**שימו לב:** Endpoint זה עובד רק אם אין משתמשים במערכת. המשתמש הראשון תמיד מקבל הרשאות מ"פ.

---

### 1.2 Login (התחברות)
**POST** `/login`

**Body:**
```json
{
  "username": "commander1",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "message": "התחברת בהצלחה",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "commander1",
    "full_name": "משה כהן",
    "role": "מפ",
    "pluga_id": 1,
    "mahlaka_id": null,
    "kita": null
  }
}
```

**Error (401):**
```json
{
  "error": "שם משתמש או סיסמה שגויים"
}
```

---

### 1.3 Create User (יצירת משתמש חדש)
**POST** `/users`
**הרשאות:** מ"פ, מ"מ

**Headers:**
```
Authorization: Bearer <token>
```

**Body:**
```json
{
  "username": "platoon_commander",
  "password": "password123",
  "full_name": "יוסי לוי",
  "role": "ממ",
  "pluga_id": 1,
  "mahlaka_id": 2,
  "kita": null
}
```

**Response (201):**
```json
{
  "message": "משתמש נוצר בהצלחה",
  "user": {
    "id": 2,
    "username": "platoon_commander",
    "full_name": "יוסי לוי",
    "role": "ממ"
  }
}
```

**הערה:** מ"מ יכול ליצור רק מ"כ במחלקה שלו.

---

## 2. PLUGA (פלוגה) ENDPOINTS

### 2.1 Create Pluga (יצירת פלוגה)
**POST** `/plugot`
**הרשאות:** מ"פ בלבד (ללא פלוגה)

**Body:**
```json
{
  "name": "פלוגה ב",
  "gdud": "גדוד פנתר",
  "color": "#BF092F"
}
```

**Response (201):**
```json
{
  "message": "פלוגה נוצרה בהצלחה",
  "pluga": {
    "id": 1,
    "name": "פלוגה ב",
    "gdud": "גדוד פנתר",
    "color": "#BF092F"
  }
}
```

---

### 2.2 Get Pluga (קבלת פרטי פלוגה)
**GET** `/plugot/{pluga_id}`
**הרשאות:** כל מי ששייך לפלוגה

**Response (200):**
```json
{
  "pluga": {
    "id": 1,
    "name": "פלוגה ב",
    "gdud": "גדוד פנתר",
    "color": "#BF092F",
    "mahalkot_count": 4
  }
}
```

---

### 2.3 Update Pluga (עדכון פלוגה)
**PUT** `/plugot/{pluga_id}`
**הרשאות:** מ"פ בלבד

**Body:**
```json
{
  "name": "פלוגה ב - מעודכן",
  "gdud": "גדוד פנתר",
  "color": "#FF0000"
}
```

**Response (200):**
```json
{
  "message": "פלוגה עודכנה בהצלחה"
}
```

---

## 3. MAHLAKA (מחלקה) ENDPOINTS

### 3.1 Create Mahlaka (יצירת מחלקה)
**POST** `/mahalkot`
**הרשאות:** מ"פ בלבד

**Body:**
```json
{
  "number": 1,
  "color": "#FF5733",
  "pluga_id": 1
}
```

**Response (201):**
```json
{
  "message": "מחלקה נוצרה בהצלחה",
  "mahlaka": {
    "id": 1,
    "number": 1,
    "color": "#FF5733"
  }
}
```

---

### 3.2 Get Mahlaka (קבלת פרטי מחלקה)
**GET** `/mahalkot/{mahlaka_id}`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "mahlaka": {
    "id": 1,
    "number": 1,
    "color": "#FF5733",
    "pluga_id": 1,
    "stats": {
      "total_soldiers": 25,
      "commanders": 3,
      "drivers": 4,
      "soldiers": 18
    }
  }
}
```

---

### 3.3 List Mahalkot (רשימת מחלקות)
**GET** `/plugot/{pluga_id}/mahalkot`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "mahalkot": [
    {
      "id": 1,
      "number": 1,
      "color": "#FF5733",
      "soldiers_count": 25
    },
    {
      "id": 2,
      "number": 2,
      "color": "#33FF57",
      "soldiers_count": 23
    }
  ]
}
```

---

## 4. SOLDIER (חייל) ENDPOINTS

### 4.1 Create Soldier (יצירת חייל)
**POST** `/soldiers`
**הרשאות:** מ"פ (כל המחלקות), מ"מ (המחלקה שלו), מ"כ (הכיתה שלו)

**Body:**
```json
{
  "name": "דוד אברהם",
  "role": "לוחם",
  "mahlaka_id": 1,
  "kita": "א",
  "idf_id": "7654321",
  "personal_id": "123456789",
  "sex": "זכר",
  "phone_number": "050-1234567",
  "address": "רחוב הרצל 10, תל אביב",
  "emergency_contact_name": "שרה אברהם",
  "emergency_contact_number": "050-7654321",
  "pakal": "M16",
  "recruit_date": "2024-01-15",
  "birth_date": "2003-05-20",
  "home_round_date": "2024-11-01",
  "is_platoon_commander": false,
  "has_hatashab": false,
  "certifications": ["נהג", "חמל"]
}
```

**Response (201):**
```json
{
  "message": "חייל נוסף בהצלחה",
  "soldier": {
    "id": 1,
    "name": "דוד אברהם",
    "role": "לוחם",
    "kita": "א"
  }
}
```

---

### 4.2 Get Soldier (קבלת פרטי חייל)
**GET** `/soldiers/{soldier_id}`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "soldier": {
    "id": 1,
    "name": "דוד אברהם",
    "role": "לוחם",
    "kita": "א",
    "idf_id": "7654321",
    "personal_id": "123456789",
    "sex": "זכר",
    "phone_number": "050-1234567",
    "address": "רחוב הרצל 10, תל אביב",
    "emergency_contact_name": "שרה אברהם",
    "emergency_contact_number": "050-7654321",
    "pakal": "M16",
    "recruit_date": "2024-01-15",
    "birth_date": "2003-05-20",
    "home_round_date": "2024-11-01",
    "is_platoon_commander": false,
    "has_hatashab": false,
    "mahlaka_id": 1,
    "certifications": ["נהג", "חמל"],
    "unavailable_dates": [
      {
        "id": 1,
        "date": "2024-11-15",
        "reason": "בקשת יציאה",
        "status": "approved"
      }
    ]
  }
}
```

---

### 4.3 Update Soldier (עדכון חייל)
**PUT** `/soldiers/{soldier_id}`
**הרשאות:** מ"פ (כולם), מ"מ (המחלקה שלו), מ"כ (הכיתה שלו)

**Body:** (שדות חלקיים - רק מה שרוצים לעדכן)
```json
{
  "name": "דוד אברהם",
  "phone_number": "050-9999999",
  "has_hatashab": true
}
```

**Response (200):**
```json
{
  "message": "חייל עודכן בהצלחה"
}
```

---

### 4.4 Delete Soldier (מחיקת חייל)
**DELETE** `/soldiers/{soldier_id}`
**הרשאות:** מ"פ (כולם), מ"מ (המחלקה שלו), מ"כ (הכיתה שלו)

**Response (200):**
```json
{
  "message": "חייל נמחק בהצלחה"
}
```

---

### 4.5 List Soldiers by Mahlaka (רשימת חיילים במחלקה)
**GET** `/mahalkot/{mahlaka_id}/soldiers`
**הרשאות:** כל מי שבפלוגה (מ"כ רואה רק את הכיתה שלו)

**Response (200):**
```json
{
  "soldiers": [
    {
      "id": 1,
      "name": "דוד אברהם",
      "role": "לוחם",
      "kita": "א",
      "certifications": ["נהג", "חמל"],
      "is_platoon_commander": false,
      "has_hatashab": false
    },
    {
      "id": 2,
      "name": "יעקב משה",
      "role": "נהג",
      "kita": "א",
      "certifications": ["נהג"],
      "is_platoon_commander": false,
      "has_hatashab": true
    }
  ]
}
```

---

## 5. CERTIFICATIONS & UNAVAILABILITY

### 5.1 Add Certification (הוספת הסמכה)
**POST** `/soldiers/{soldier_id}/certifications`
**הרשאות:** מ"פ, מ"מ, מ"כ (בהתאם לחייל)

**Body:**
```json
{
  "certification_name": "סייר"
}
```

**Response (201):**
```json
{
  "message": "הסמכה נוספה בהצלחה"
}
```

---

### 5.2 Add Unavailable Date (הוספת תאריך לא זמין)
**POST** `/soldiers/{soldier_id}/unavailable`
**הרשאות:** מ"פ, מ"מ, מ"כ (בהתאם לחייל)

**Body:**
```json
{
  "date": "2024-11-20",
  "reason": "בקשת יציאה משפחתית",
  "status": "approved"
}
```

**Response (201):**
```json
{
  "message": "תאריך נוסף בהצלחה"
}
```

---

### 5.3 Delete Unavailable Date (מחיקת תאריך)
**DELETE** `/unavailable/{unavailable_id}`
**הרשאות:** מ"פ, מ"מ, מ"כ (בהתאם לחייל)

**Response (200):**
```json
{
  "message": "תאריך נמחק בהצלחה"
}
```

---

## 6. ASSIGNMENT TEMPLATES (תבניות משימות)

### 6.1 Create Assignment Template (יצירת תבנית)
**POST** `/plugot/{pluga_id}/assignment-templates`
**הרשאות:** מ"פ בלבד

**Body:**
```json
{
  "name": "סיור",
  "assignment_type": "סיור",
  "length_in_hours": 8,
  "times_per_day": 3,
  "commanders_needed": 1,
  "drivers_needed": 1,
  "soldiers_needed": 2,
  "same_mahlaka_required": true,
  "requires_certification": null,
  "requires_senior_commander": false
}
```

**Response (201):**
```json
{
  "message": "תבנית נוצרה בהצלחה",
  "template": {
    "id": 1,
    "name": "סיור",
    "assignment_type": "סיור"
  }
}
```

---

### 6.2 List Assignment Templates (רשימת תבניות)
**GET** `/plugot/{pluga_id}/assignment-templates`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "סיור",
      "assignment_type": "סיור",
      "length_in_hours": 8,
      "times_per_day": 3,
      "commanders_needed": 1,
      "drivers_needed": 1,
      "soldiers_needed": 2,
      "same_mahlaka_required": true,
      "requires_certification": null,
      "requires_senior_commander": false
    }
  ]
}
```

---

## 7. SHAVZAK (שיבוץ) ENDPOINTS

### 7.1 Create Shavzak (יצירת שיבוץ)
**POST** `/shavzakim`
**הרשאות:** מ"פ, מ"מ

**Body:**
```json
{
  "name": "שיבוץ שבוע 46",
  "start_date": "2024-11-10",
  "days_count": 7,
  "pluga_id": 1,
  "min_rest_hours": 8,
  "emergency_mode": false
}
```

**Response (201):**
```json
{
  "message": "שיבוץ נוצר בהצלחה",
  "shavzak": {
    "id": 1,
    "name": "שיבוץ שבוע 46",
    "start_date": "2024-11-10",
    "days_count": 7
  }
}
```

---

### 7.2 Generate Shavzak (הרצת אלגוריתם שיבוץ)
**POST** `/shavzakim/{shavzak_id}/generate`
**הרשאות:** מ"פ, מ"מ

**Body:** (אופציונלי - הגדרות נוספות)
```json
{
  "emergency_mode": false
}
```

**Response (200):**
```json
{
  "message": "שיבוץ בוצע בהצלחה",
  "warnings": [
    "⚠️ סיור 2 ביום 3: מנוחה מופחתת ל-4 שעות"
  ],
  "stats": {
    "total_assignments": 147,
    "emergency_assignments": 3
  }
}
```

---

### 7.3 Get Shavzak (קבלת שיבוץ)
**GET** `/shavzakim/{shavzak_id}`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "shavzak": {
    "id": 1,
    "name": "שיבוץ שבוע 46",
    "start_date": "2024-11-10",
    "days_count": 7,
    "created_at": "2024-11-09T10:30:00",
    "min_rest_hours": 8,
    "emergency_mode": false
  },
  "assignments": [
    {
      "id": 1,
      "name": "סיור 1",
      "type": "סיור",
      "day": 0,
      "start_hour": 0,
      "length_in_hours": 8,
      "assigned_mahlaka_id": 1,
      "soldiers": [
        {
          "id": 5,
          "name": "דוד אברהם",
          "role": "commander"
        },
        {
          "id": 8,
          "name": "משה לוי",
          "role": "driver"
        },
        {
          "id": 12,
          "name": "יוסי כהן",
          "role": "soldier"
        },
        {
          "id": 15,
          "name": "אבי ישראל",
          "role": "soldier"
        }
      ]
    }
  ]
}
```

---

### 7.4 List Shavzakim (רשימת שיבוצים)
**GET** `/plugot/{pluga_id}/shavzakim`
**הרשאות:** כל מי שבפלוגה

**Response (200):**
```json
{
  "shavzakim": [
    {
      "id": 1,
      "name": "שיבוץ שבוע 46",
      "start_date": "2024-11-10",
      "days_count": 7,
      "created_at": "2024-11-09T10:30:00"
    },
    {
      "id": 2,
      "name": "שיבוץ שבוע 45",
      "start_date": "2024-11-03",
      "days_count": 7,
      "created_at": "2024-11-02T14:20:00"
    }
  ]
}
```

---

## 8. UTILITY ENDPOINTS

### 8.1 Get Current User Info (מידע על המשתמש)
**GET** `/me`
**הרשאות:** כל משתמש מחובר

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "commander1",
    "full_name": "משה כהן",
    "role": "מפ",
    "pluga": {
      "id": 1,
      "name": "פלוגה ב"
    },
    "mahlaka": null,
    "kita": null,
    "last_login": "2024-11-09T08:30:00"
  }
}
```

---

### 8.2 Get Statistics (סטטיסטיקות)
**GET** `/stats`
**הרשאות:** כל משתמש מחובר

**Response (200):**
```json
{
  "stats": {
    "mahalkot": 4,
    "total_soldiers": 95,
    "commanders": 12,
    "drivers": 15,
    "soldiers": 68,
    "shavzakim": 8
  }
}
```

---

### 8.3 Health Check (בדיקת תקינות)
**GET** `/health`
**הרשאות:** ללא

**Response (200):**
```json
{
  "status": "healthy",
  "message": "Shavzak API is running"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "נתונים לא תקינים"
}
```

### 401 Unauthorized
```json
{
  "error": "חסר token"
}
```

### 403 Forbidden
```json
{
  "error": "אין לך הרשאה לפעולה זו"
}
```

### 404 Not Found
```json
{
  "error": "משאב לא נמצא"
}
```

### 500 Internal Server Error
```json
{
  "error": "שגיאת שרת פנימית"
}
```

---

## הרשאות לפי תפקיד

### מ"פ (מפקד פלוגה)
- ✅ יכול לערוך **הכל** בפלוגה שלו
- ✅ יכול ליצור משתמשים (מ"מ, מ"כ)
- ✅ יכול ליצור ולערוך מחלקות
- ✅ יכול ליצור ולערוך חיילים בכל המחלקות
- ✅ יכול ליצור תבניות משימות
- ✅ יכול ליצור שיבוצים

### מ"מ (מפקד מחלקה)
- ✅ יכול לצפות בכל הפלוגה
- ✅ יכול לערוך את **המחלקה שלו בלבד**
- ✅ יכול ליצור משתמשים (מ"כ במחלקה שלו)
- ✅ יכול ליצור ולערוך חיילים במחלקה שלו
- ✅ יכול ליצור שיבוצים

### מ"כ (מפקד כיתה)
- ✅ יכול לצפות בכל הפלוגה
- ✅ יכול לערוך את **הכיתה שלו בלבד**
- ✅ יכול ליצור ולערוך חיילים בכיתה שלו
- ❌ לא יכול ליצור משתמשים
- ❌ לא יכול ליצור שיבוצים

---

## דוגמאות שימוש (Flow מלא)

### תרחיש 1: הקמת פלוגה חדשה

```bash
# 1. רישום מ"פ ראשון
POST /api/register
{
  "username": "commander1",
  "password": "pass123",
  "full_name": "משה כהן"
}

# 2. יצירת פלוגה
POST /api/plugot
Authorization: Bearer <token>
{
  "name": "פלוגה ב",
  "gdud": "גדוד פנתר",
  "color": "#BF092F"
}

# 3. יצירת מחלקות (4 מחלקות)
POST /api/mahalkot
{
  "number": 1,
  "color": "#FF0000",
  "pluga_id": 1
}

# 4. הוספת חיילים לכל מחלקה
POST /api/soldiers
{
  "name": "דוד אברהם",
  "role": "לוחם",
  "mahlaka_id": 1,
  "kita": "א"
}

# 5. יצירת תבניות משימות
POST /api/plugot/1/assignment-templates
{
  "name": "סיור",
  "assignment_type": "סיור",
  "length_in_hours": 8,
  "times_per_day": 3
}

# 6. יצירת שיבוץ
POST /api/shavzakim
{
  "name": "שיבוץ שבוע 46",
  "start_date": "2024-11-10",
  "days_count": 7
}

# 7. הרצת אלגוריתם שיבוץ
POST /api/shavzakim/1/generate

# 8. צפייה בתוצאות
GET /api/shavzakim/1
```

---

## טיפים לפיתוח

1. **תמיד שמרו את ה-Token** לאחר Login
2. **בדקו הרשאות** - כל endpoint בודק מי אתה ומה אתה יכול
3. **טיפול בשגיאות** - תמיד בדקו את status code
4. **תאריכים** - פורמט ISO: `YYYY-MM-DD`
5. **כל ה-IDs** הם integers
6. **Token פג תוקף אחרי 7 ימים** - צריך Login מחדש

---

## סיכום נקודות חשובות

✅ **מערכת הרשאות מלאה** - 3 רמות (מ"פ, מ"מ, מ"כ)
✅ **JWT Authentication** - אבטחה מלאה
✅ **Cascading Deletes** - מחיקת משאב מוחקת גם את התלויים בו
✅ **Validation** - בדיקות הרשאות בכל endpoint
✅ **Hebrew Support** - כל ההודעות בעברית
✅ **RESTful Design** - עיצוב API סטנדרטי
