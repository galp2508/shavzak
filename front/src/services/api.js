import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// פונקציה גלובלית שתוגדר על ידי App.jsx
let serverDownCallback = null;

export const setServerDownCallback = (callback) => {
  serverDownCallback = callback;
};

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // בדוק אם יש שגיאת רשת (השרת לא זמין)
    if (!error.response && error.code === 'ERR_NETWORK') {
      console.error('🔴 השרת לא זמין - שגיאת רשת');
      if (serverDownCallback) {
        serverDownCallback();
      }
      return Promise.reject(error);
    }

    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
