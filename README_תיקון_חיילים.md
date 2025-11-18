# 🚨 תיקון דחוף - חיילים לא נטענים

## הבעיה שנתקלת בה:

```
Error in list_soldiers_by_mahlaka: (sqlite3.OperationalError) no such column: soldier_status.start_date
```

## הפתרון - פשוט וקל:

### צעדים:

1. **עצור את השרת** (לחץ Ctrl+C בטרמינל)

2. **פתח תיקייה** `back` של הפרויקט

3. **הקלק פעמיים** על הקובץ: `תקן_בסיס_נתונים.bat`

   **או** הרץ בטרמינל:
   ```bash
   cd back
   python fix_soldier_status_schema.py
   ```

4. **המתן** שהסקריפט יסיים (כ-10 שניות)

5. **הפעל מחדש את השרver**

## זהו! 🎉

השגיאה תיעלם והחיילים ייטענו בלי בעיות.

---

## מידע טכני

הסיבה לשגיאה: בסיס הנתונים חסרות שתי עמודות (`start_date`, `end_date`) שהקוד מצפה למצוא.

הסקריפט מוסיף את העמודות החסרות בצורה בטוחה (עם גיבוי אוטומטי).
