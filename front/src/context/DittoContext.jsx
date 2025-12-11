import React, { createContext, useContext, useEffect, useState } from 'react';
import { initDitto } from '../services/ditto';

const DittoContext = createContext(null);

export const DittoProvider = ({ children }) => {
  const [ditto, setDitto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const startDitto = async () => {
      try {
        const dittoInstance = await initDitto();
        setDitto(dittoInstance);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    startDitto();
  }, []);

  return (
    <DittoContext.Provider value={{ ditto, loading, error }}>
      {children}
    </DittoContext.Provider>
  );
};

export const useDitto = () => {
  const context = useContext(DittoContext);
  if (!context) {
    throw new Error('useDitto must be used within a DittoProvider');
  }
  return context;
};
