import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// פונקציה גלובלית שתוגדר על ידי App.jsx
let serverDownCallback = null;
let consecutiveErrors = 0;
const MAX_ERRORS_BEFORE_MAINTENANCE = 3;

export const setServerDownCallback = (callback) => {
  serverDownCallback = callback;
};

export const resetErrorCount = () => {
  consecutiveErrors = 0;
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
  (response) => {
    // אם הבקשה הצליחה, אפס את מונה השגיאות
    consecutiveErrors = 0;
    return response;
  },
  (error) => {
    // בדוק אם יש שגיאת רשת (השרת לא זמין)
    if (!error.response && error.code === 'ERR_NETWORK') {
      consecutiveErrors++;
      console.error(`🔴 שגיאת רשת (${consecutiveErrors}/${MAX_ERRORS_BEFORE_MAINTENANCE})`);

      // הצג מסך תחזוקה רק אחרי 3 שגיאות רצופות
      if (consecutiveErrors >= MAX_ERRORS_BEFORE_MAINTENANCE && serverDownCallback) {
        console.error('🔴 השרת לא זמין - מציג מסך תחזוקה');
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
