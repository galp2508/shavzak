import React, { createContext, useState, useContext, useCallback, useRef, useEffect } from 'react';

const ServerStatusContext = createContext(null);

export const useServerStatus = () => {
  const context = useContext(ServerStatusContext);
  if (!context) {
    throw new Error('useServerStatus must be used within a ServerStatusProvider');
  }
  return context;
};

export const ServerStatusProvider = ({ children }) => {
  const [isServerDown, setIsServerDown] = useState(false);
  const isServerDownRef = useRef(false);
  const consecutiveSuccessesRef = useRef(0);
  const consecutiveFailuresRef = useRef(0);
  const debounceTimerRef = useRef(null);

  const REQUIRED_SUCCESSES = 3; // מספר בקשות מוצלחות נדרש לפני שמסירים את מסך התחזוקה
  const REQUIRED_FAILURES = 3; // מספר כשלונות ברצף נדרש לפני הצגת מסך תחזוקה
  const DEBOUNCE_DELAY = 1000; // השהיה במילישניות לפני שינוי מצב

  const markServerDown = useCallback(() => {
    // אפס את מונה ההצלחות
    consecutiveSuccessesRef.current = 0;

    // הגדל את מונה הכשלונות
    consecutiveFailuresRef.current += 1;
    const failureCount = consecutiveFailuresRef.current;

    console.log(`🔴 שגיאת רשת (${failureCount}/${REQUIRED_FAILURES})`);

    // רק אם יש מספיק כשלונות ברצף, הצג מסך תחזוקה
    if (failureCount >= REQUIRED_FAILURES && !isServerDownRef.current) {
      // בטל timer קודם אם קיים
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // הוסף delay קטן לפני הצגת מסך התחזוקה
      debounceTimerRef.current = setTimeout(() => {
        console.log('🔴 השרת לא זמין - מציג מסך תחזוקה');
        isServerDownRef.current = true;
        setIsServerDown(true);
      }, DEBOUNCE_DELAY);
    }
  }, []);

  const markServerUp = useCallback(() => {
    // אפס את מונה הכשלונות
    consecutiveFailuresRef.current = 0;

    // בטל timer של מסך תחזוקה אם עדיין לא הוצג
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    // אם השרת כבר פעיל, אל תעשה כלום (מונע עדכוני state מיותרים)
    if (!isServerDownRef.current) {
      return;
    }

    consecutiveSuccessesRef.current += 1;
    const newCount = consecutiveSuccessesRef.current;
    console.log(`✅ בקשה מוצלחת (${newCount}/${REQUIRED_SUCCESSES})`);

    // רק אם יש מספיק הצלחות ברצף, נחזיר את המערכת לפעילות
    if (newCount >= REQUIRED_SUCCESSES) {
      console.log('🎉 השרת חזר לפעילות מלאה!');
      isServerDownRef.current = false;
      setIsServerDown(false);
      consecutiveSuccessesRef.current = 0; // אפס את המונה
    }
  }, []);

  // Cleanup טיימר בעת unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const value = {
    isServerDown,
    markServerDown,
    markServerUp,
  };

  return (
    <ServerStatusContext.Provider value={value}>
      {children}
    </ServerStatusContext.Provider>
  );
};
