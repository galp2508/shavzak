# 🎨 Shavzak Frontend - Smart Scheduling UI with AI

אפליקציית React מתקדמת למערכת ניהול שיבוצים חכמה עם **למידת מכונה (ML)**!

המערכת מציגה ממשק אינטראקטיבי ללמידה ושיפור מתמיד של אלגוריתם השיבוץ. 🤖

---

## 🚀 התקנה מהירה

```bash
# 1. התקן תלויות
npm install

# 2. הפעל בפיתוח
npm run dev

# האפליקציה תרוץ על http://localhost:3000
```

---

## 🎯 תכונות עיקריות

### 🧠 שיבוץ חכם עם AI
- **כפתור "שיבוץ AI"** - יצירת שיבוץ חכם אוטומטי
- **פידבק בזמן אמת** - כפתורי 👍 / 👎 על כל משימה
- **סטטיסטיקות ML** - מעקב אחרי ביצועי המודל
- **העלאת דוגמאות** - לימוד ממשק מתמונות שיבוץ

### 📊 ממשק SmartSchedule
- לוח שעות 24 אינטראקטיבי
- צבעי מחלקות דינמיים
- התראות וא זהרות בזמן אמת
- ניווט קל בין ימים (מקלדת: ← →)

### ✅ תכונות נוספות
- עיצוב RTL מלא לעברית
- Tailwind CSS עם ערכת צבעים צבאית
- אנימציות והנפשות חלקות
- Responsive לכל המסכים
- Role-based permissions

---

## 📁 מבנה הפרויקט

```
front/
├── src/
│   ├── components/
│   │   ├── Layout.jsx              # ליאאוט ראשי + ניווט
│   │   └── Loading.jsx             # מסך טעינה
│   ├── context/
│   │   └── AuthContext.jsx         # ניהול אימות
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── SmartSchedule.jsx       # 🤖 דף שיבוץ חכם חדש!
│   │   ├── LiveSchedule.jsx        # (ישן - גיבוי)
│   │   ├── Mahalkot.jsx
│   │   ├── Templates.jsx
│   │   ├── Shavzakim.jsx
│   │   └── Profile.jsx
│   ├── services/
│   │   └── api.js                  # Axios config + ML endpoints
│   ├── App.jsx                     # App + Router
│   ├── main.jsx
│   └── index.css
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## 🎨 דף SmartSchedule החדש

### תכונות הדף:

#### 1. **כותרת עם תג AI**
```jsx
<h1>שיבוץ חכם AI</h1>
<span>POWERED BY ML</span>
```

#### 2. **סרגל סטטיסטיקות ML**
מציג בזמן אמת:
- 📊 דירוג אישור (Approval Rate)
- 🎯 דפוסים שנלמדו
- ✅ שיבוצים שאושרו
- ❌ שיבוצים שנדחו

#### 3. **כפתורים אינטראקטיביים**

**כפתור "שיבוץ AI":**
```jsx
<button onClick={generateSmartSchedule}>
  <Brain /> שיבוץ AI
</button>
```
יוצר שיבוץ חכם עם ML!

**כפתור "העלאת דוגמאות":**
```jsx
<button onClick={() => setShowUploadModal(true)}>
  <Upload /> העלה דוגמאות
</button>
```
מאפשר העלאת תמונות שיבוץ ידניות לאימון המודל

#### 4. **פידבק על משימות**
כל משימה כוללת כפתורי פידבק:
```jsx
<button onClick={() => handleFeedback(id, 'approved')}>
  <ThumbsUp /> אישור
</button>
<button onClick={() => handleFeedback(id, 'rejected')}>
  <ThumbsDown /> דחייה
</button>
```

#### 5. **לוח שעות אינטראקטיבי**
- 24 שעות בתצוגה
- בלוקים צבעוניים לפי מחלקות
- hover effects מרהיבים
- מידע מפורט על כל משימה

---

## 🔌 אינטגרציה עם ML API

### Endpoints חדשים:

```javascript
// יצירת שיבוץ חכם
const response = await api.post('/ml/smart-schedule', {
  pluga_id: 1,
  start_date: '2025-01-01',
  days_count: 7
});

// הוספת פידבק
await api.post('/ml/feedback', {
  assignment_id: 123,
  rating: 'approved'  // או 'rejected' / 'modified'
});

// קבלת סטטיסטיקות
const stats = await api.get('/ml/stats');

// העלאת דוגמה
await api.post('/ml/upload-example', {
  image: base64Image,
  rating: 'excellent'
});
```

---

## 🎨 ערכת העיצוב החדשה

### צבעים חדשים:
```javascript
// Gradient AI
from-purple-600 via-blue-600 to-indigo-700

// כפתור AI
from-green-500 to-emerald-600

// סטטיסטיקות
blue-600, purple-600, green-600, emerald-600, red-600
```

### אנימציות:
```css
.animate-pulse       /* עבור תג ML */
.animate-spin        /* עבור loading */
.hover:scale-105     /* עבור כרטיסים */
.hover:shadow-lg     /* עבור משימות */
```

---

## 🛠️ פיתוח

### פקודות:
```bash
# פיתוח
npm run dev

# בנייה לייצור
npm run build

# preview של build
npm run preview
```

### Dev Tools מומלצים:
- React DevTools
- Tailwind CSS IntelliSense
- ES7+ React Snippets
- Prettier

---

## 📱 Responsive Design

### Breakpoints:
- **sm**: 640px - מובייל גדול
- **md**: 768px - טאבלט
- **lg**: 1024px - לפטופ
- **xl**: 1280px - מסך גדול

### דוגמה:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
  {/* מובייל: 1 עמודה, טאבלט: 2, מחשב: 4 */}
</div>
```

---

## 🎭 Role-Based UI

### הרשאות:
```jsx
// מפקד פלוגה בלבד
{user.role === 'מפ' && (
  <button>יצירת שיבוץ AI</button>
)}

// מפקד ומחלקה
{['מפ', 'ממ'].includes(user.role) && (
  <button>פידבק על שיבוץ</button>
)}

// כולם
<div>תצוגת שיבוץ</div>
```

---

## 🔔 התראות

### משתמש ב-`react-toastify`:

```jsx
import { toast } from 'react-toastify';

// הצלחה
toast.success('🤖 שיבוץ AI נוצר בהצלחה!');

// שגיאה
toast.error('❌ שגיאה בשיבוץ');

// מידע
toast.info('💡 המערכת לומדת מהפידבק');
```

---

## 🧩 רכיבים חשובים

### 1. SmartSchedule.jsx
הרכיב הראשי של דף השיבוץ החכם

**Props:** אין (משתמש ב-AuthContext)

**State:**
- `currentDate` - התאריך הנוכחי
- `scheduleData` - נתוני השיבוץ
- `mlStats` - סטטיסטיקות ML
- `isGenerating` - האם יוצר שיבוץ

**Functions:**
- `generateSmartSchedule()` - יצירת שיבוץ חכם
- `handleFeedback()` - מתן פידבק
- `loadMLStats()` - טעינת סטטיסטיקות

### 2. UploadExamplesModal
מודל להעלאת תמונות דוגמה

**Props:**
- `onClose` - סגירת המודל
- `onUploadSuccess` - callback אחרי העלאה

**Features:**
- drag & drop תמיכה
- multi-file upload
- base64 encoding
- progress indicator

---

## 🎨 אייקונים

### משתמש ב-`lucide-react`:

```jsx
import {
  Brain,      // AI icon
  ThumbsUp,   // אישור
  ThumbsDown, // דחייה
  Upload,     // העלאה
  TrendingUp, // סטטיסטיקות
  Award,      // הצלחה
  Zap         // מהירות
} from 'lucide-react';

<Brain size={24} className="text-purple-600 animate-pulse" />
```

---

## 🐛 פתרון בעיות

### ML לא עובד
**בעיה:** `⚠️ Smart Scheduler: אין מודל קיים`

**פתרון:**
1. ודא שהשרת Python רץ
2. אמן את המודל דרך `/api/ml/train`
3. בדוק ב-`/api/ml/stats`

### פידבק לא נשמר
**בעיה:** Feedback button לא עובד

**פתרון:**
1. בדוק את ה-Token (F12 → Network)
2. ודא שיש הרשאות (מפ/ממ)
3. בדוק שה-assignment_id תקין

### סטטיסטיקות לא מופיעות
**בעיה:** ML Stats bar ריק

**פתרון:**
```javascript
// בדוק בקונסול:
console.log(mlStats);

// ודא שה-endpoint עובד:
fetch('/api/ml/stats')
  .then(r => r.json())
  .then(console.log);
```

---

## ⚡ Performance

### אופטימיזציות:
- ✅ Lazy loading של components
- ✅ Memoization ב-React
- ✅ Virtual scrolling לרשימות ארוכות
- ✅ Code splitting אוטומטי
- ✅ Tree shaking
- ✅ Fast Refresh

### טיפים:
```jsx
// השתמש ב-useMemo לחישובים כבדים
const expensiveValue = useMemo(() => {
  return heavyCalculation(data);
}, [data]);

// השתמש ב-useCallback לפונקציות
const handleClick = useCallback(() => {
  // ...
}, [deps]);
```

---

## 📚 מדריך שימוש

### תרחיש 1: יצירת שיבוץ חכם
1. היכנס לדף "שיבוץ חי"
2. לחץ על כפתור "שיבוץ AI" 🤖
3. המערכת תיצור שיבוץ אוטומטי
4. תן פידבק עם 👍 / 👎

### תרחיש 2: העלאת דוגמאות
1. לחץ על כפתור Upload (📤)
2. בחר תמונות שיבוץ ידניות
3. לחץ "העלה והאמן"
4. המערכת תלמד מהדוגמאות!

### תרחיש 3: מעקב אחרי ביצועים
1. ראה סטטיסטיקות בסרגל העליון:
   - 📊 דירוג אישור
   - 🎯 דפוסים שנלמדו
   - ✅ אישורים
   - ❌ דחיות

---

## 🎓 למידה נוספת

- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [React Router](https://reactrouter.com)
- [Lucide Icons](https://lucide.dev)

---

## 🎉 התחל לפתח!

```bash
# התקן
npm install

# הפעל
npm run dev

# פתח דפדפן
http://localhost:3000
```

תראה ממשק מדהים עם AI! ✨🤖

---

**נבנה עם ❤️ ו-AI בישראל 🇮🇱**

**POWERED BY MACHINE LEARNING 🤖**
