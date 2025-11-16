import React, { createContext, useState, useContext, useCallback, useRef } from 'react';

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

  const REQUIRED_SUCCESSES = 3; // מספר בקשות מוצלחות נדרש לפני שמסירים את מסך התחזוקה

  const markServerDown = useCallback(() => {
    // אם השרת כבר down, אל תעשה כלום
    if (isServerDownRef.current) {
      return;
    }

    console.log('🔴 השרת לא זמין - מציג מסך תחזוקה');
    isServerDownRef.current = true;
    setIsServerDown(true);
    consecutiveSuccessesRef.current = 0; // אפס את מונה ההצלחות
  }, []);

  const markServerUp = useCallback(() => {
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
