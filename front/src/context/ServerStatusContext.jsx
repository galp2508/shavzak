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

  const markServerDown = () => {
    console.log('🔴 השרת לא זמין - מציג מסך תחזוקה');
    setIsServerDown(true);
  };

  const markServerUp = () => {
    console.log('✅ השרת חזר לפעילות');
    setIsServerDown(false);
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
