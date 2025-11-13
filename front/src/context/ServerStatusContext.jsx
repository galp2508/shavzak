import React, { createContext, useState, useContext } from 'react';

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
  const [consecutiveSuccesses, setConsecutiveSuccesses] = useState(0);

  const REQUIRED_SUCCESSES = 3; // מספר בקשות מוצלחות נדרש לפני שמסירים את מסך התחזוקה

  const markServerDown = () => {
    console.log('🔴 השרת לא זמין - מציג מסך תחזוקה');
    setIsServerDown(true);
    setConsecutiveSuccesses(0); // אפס את מונה ההצלחות
  };

  const markServerUp = () => {
    if (!isServerDown) {
      // אם השרת כבר פעיל, אין צורך לספור
      return;
    }

    setConsecutiveSuccesses(prev => {
      const newCount = prev + 1;
      console.log(`✅ בקשה מוצלחת (${newCount}/${REQUIRED_SUCCESSES})`);

      // רק אם יש מספיק הצלחות ברצף, נחזיר את המערכת לפעילות
      if (newCount >= REQUIRED_SUCCESSES) {
        console.log('🎉 השרת חזר לפעילות מלאה!');
        setIsServerDown(false);
        return 0; // אפס את המונה
      }

      return newCount;
    });
  };

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
