# 🎨 Shavzak Frontend - React Application

אפליקציית React מדהימה למערכת ניהול השיבוצים!

## 🚀 התקנה מהירה

```bash
# 1. התקן תלויות
npm install

# 2. הפעל בפיתוח
npm run dev

# האפליקציה תרוץ על http://localhost:3000
```

## 📋 דרישות

- Node.js 18+
- npm או yarn
- שרת ה-API רץ על port 5000

## 🎯 תכונות

### ✅ עיצוב מדהים
- עיצוב RTL מלא לעברית
- Tailwind CSS עם ערכת נושא צבאית
- אנימציות חלקות
- Responsive לכל המסכים

### ✅ ניהול מלא
- **דשבורד** - סטטיסטיקות וגרפים
- **חיילים** - טבלה עם חיפוש ועריכה
- **מחלקות** - ניהול מחלקות בפלוגה
- **שיבוצים** - יצירה וצפייה בשיבוצים
- **פרופיל** - מידע אישי

### ✅ אבטחה
- JWT Authentication
- Protected Routes
- Role-based permissions
- Auto logout on 401

### ✅ חוויית משתמש
- Toast notifications
- Loading states
- Error handling
- Form validation

## 📁 מבנה הפרויקט

```
frontend/
├── src/
│   ├── components/      # רכיבים רב פעמיים
│   │   ├── Layout.jsx  # ליאאוט ראשי + ניווט
│   │   └── Loading.jsx # מסך טעינה
│   ├── context/        # Context API
│   │   └── AuthContext.jsx  # ניהול אימות
│   ├── pages/          # דפים
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Soldiers.jsx
│   │   ├── Mahalkot.jsx
│   │   ├── Plugot.jsx
│   │   ├── Templates.jsx
│   │   ├── Shavzakim.jsx
│   │   ├── ShavzakView.jsx
│   │   └── Profile.jsx
│   ├── services/       # שירותי API
│   │   └── api.js      # Axios config
│   ├── App.jsx         # App + Router
│   ├── main.jsx        # Entry point
│   └── index.css       # Styles
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 🎨 ערכת העיצוב

### צבעים
```javascript
military: {
  50-900: // ירוק צבאי
}
idf: {
  green: '#34996e',
  gold: '#D4AF37',
  red: '#BF092F',
}
```

### רכיבים מוכנים
```jsx
<button className="btn-primary">כפתור ראשי</button>
<button className="btn-secondary">כפתור משני</button>
<div className="card">כרטיס</div>
<input className="input-field" />
<span className="badge badge-green">תג</span>
```

## 🔐 Authentication Flow

1. **Login/Register** → מקבל JWT token
2. **Token** נשמר ב-localStorage
3. **Auto-inject** ב-headers של כל request
4. **Protected Routes** בודקים authentication
5. **Auto-logout** ב-401 error

## 📡 API Integration

```javascript
import api from './services/api';

// GET request
const response = await api.get('/soldiers');

// POST request
const response = await api.post('/soldiers', data);

// Token מתווסף אוטומטית!
```

## 🎭 Role-Based UI

```jsx
{user.role === 'מפ' && (
  <button>מפ בלבד</button>
)}

{['מפ', 'ממ'].includes(user.role) && (
  <button>מפ וממ</button>
)}
```

## 🛠️ פקודות

```bash
# פיתוח
npm run dev

# בנייה לייצור
npm run build

# preview של build
npm run preview
```

## 🎯 קישור לשרת

הקונפיגורציה ב-`vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  }
}
```

כל קריאה ל-`/api/*` מועברת לשרת Python!

## 📱 Responsive Breakpoints

- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px

## 🎨 אייקונים

משתמש ב-`lucide-react`:

```jsx
import { Shield, Users, Calendar } from 'lucide-react';

<Shield size={24} className="text-military-600" />
```

## 📊 Charts

משתמש ב-`recharts`:

```jsx
import { BarChart, Bar, XAxis, YAxis } from 'recharts';

<BarChart data={data}>
  <Bar dataKey="value" fill="#34996e" />
</BarChart>
```

## 🔔 Notifications

משתמש ב-`react-toastify`:

```jsx
import { toast } from 'react-toastify';

toast.success('הצלחה!');
toast.error('שגיאה!');
toast.info('מידע');
```

## 🐛 פתרון בעיות

### Port 3000 תפוס
```bash
# שנה ב-vite.config.js:
server: { port: 3001 }
```

### שרת API לא עובד
```bash
# וודא שהשרת Python רץ על port 5000
cd ../
python api.py
```

### בעיות Tailwind
```bash
# נקה cache
rm -rf node_modules .vite
npm install
```

## 🌐 דפדפנים נתמכים

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

## 📝 טיפים לפיתוח

1. **HMR** - שינויים מתעדכנים אוטומטית
2. **Console** - כל שגיאות מודפסות ב-console
3. **React DevTools** - מומלץ להתקין
4. **עריכה ב-VSCode** - עם extensions:
   - ES7+ React/Redux/React-Native snippets
   - Tailwind CSS IntelliSense
   - Prettier

## 🎓 למידה

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [Tailwind Docs](https://tailwindcss.com)
- [React Router](https://reactrouter.com)

## ⚡ Performance

- **Code Splitting** - אוטומטי עם Vite
- **Tree Shaking** - רק קוד בשימוש
- **Fast Refresh** - עדכונים מהירים
- **Optimized Build** - minify + compress

## 🎉 התחל לפתח!

```bash
npm install
npm run dev
```

פתח דפדפן ב-`http://localhost:3000` ותראה קסם! ✨

---

**נבנה בגאווה לצה"ל 🇮🇱**
