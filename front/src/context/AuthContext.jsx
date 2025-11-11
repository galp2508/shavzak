import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // טען את מידע המשתמש מתוך ה-JWT במקום לקרוא /me שמה-backend אין
      const payload = decodeJwt(token);
      if (payload) {
        // המפתח names תואם ל-payload שנוצר ב-backend
        setUser({
          id: payload.user_id,
          username: payload.username,
          full_name: payload.full_name || payload.username,
          role: payload.role,
          pluga_id: payload.pluga_id,
          mahlaka_id: payload.mahlaka_id,
          kita: payload.kita,
        });
        setLoading(false);
      } else {
        logout();
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadUserData = async () => {
    // פונקציה נשארת כדי לשמור על תאימות אבל אינה מצויה בשימוש כרגע
    try {
      setLoading(false);
    } catch (error) {
      setLoading(false);
    }
  };

  // מפענח JWT פשוט (בצד הלקוח) כדי להוציא payload בלי אימות
  const decodeJwt = (token) => {
    try {
      const parts = token.split('.');
      if (parts.length < 2) return null;
      const payload = parts[1];
      // base64url -> base64
      let base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      while (base64.length % 4) {
        base64 += '=';
      }
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      console.error('Failed to decode token', e);
      return null;
    }
  };

  const login = async (username, password) => {
    try {
      const response = await api.post('/login', { username, password });
      const { token: newToken, user: userData } = response.data;
      
      // ⚡ עדכון בסדר הנכון
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'שגיאה בהתחברות' 
      };
    }
  };

  const register = async (username, password, fullName, plugaId = null, role = null) => {
    try {
      const payload = {
        username,
        password,
        full_name: fullName
      };

      // אם יש plugaId ו-role, הוסף אותם
      if (plugaId) {
        payload.pluga_id = parseInt(plugaId);
      }
      if (role) {
        payload.role = role;
      }

      const response = await api.post('/register', payload);
      const { token: newToken, user: userData } = response.data;

      // ⚡ עדכון בסדר הנכון
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setUser(userData);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'שגיאה ברישום'
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  // Update the user object stored in context (shallow merge)
  const updateUser = (updates) => {
    setUser((prev) => {
      if (!prev) return { ...updates };
      return { ...prev, ...updates };
    });
  };

  const isRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    isRole,
    // ✅ שינוי קריטי: isAuthenticated מבוסס על token בלבד!
    isAuthenticated: !!token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
