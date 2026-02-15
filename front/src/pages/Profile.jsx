import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Shield, Mail, Phone, MapPin, Award, Edit2, Save, X, Lock } from 'lucide-react';

const Profile = () => {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  });

  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        username: user.username || '',
        full_name: user.full_name || ''
      }));
    }
  }, [user]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    
    if (formData.password && formData.password !== formData.confirmPassword) {
      setMessage({ type: 'error', text: 'הסיסמאות אינן תואמות' });
      return;
    }

    setLoading(true);
    try {
      const updateData = {
        username: formData.username,
        full_name: formData.full_name
      };
      
      if (formData.password) {
        updateData.password = formData.password;
      }

      const result = await updateProfile(updateData);
      
      if (result.success) {
        setMessage({ type: 'success', text: 'הפרופיל עודכן בהצלחה' });
        setIsEditing(false);
        setFormData(prev => ({ ...prev, password: '', confirmPassword: '' }));
      } else {
        setMessage({ type: 'error', text: result.error || 'שגיאה בעדכון הפרופיל' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'שגיאה לא צפויה' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">הפרופיל שלי</h1>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 px-4 py-2 bg-military-600 text-white rounded-lg hover:bg-military-700 transition"
          >
            <Edit2 size={20} />
            <span>עריכת פרטים</span>
          </button>
        ) : (
          <button
            onClick={() => setIsEditing(false)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition"
          >
            <X size={20} />
            <span>ביטול עריכה</span>
          </button>
        )}
      </div>

      {message.text && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 sm:p-8">
          <div className="flex items-center gap-6 mb-8">
            <div className="bg-military-100 p-4 rounded-full">
              <User className="w-12 h-12 text-military-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{user?.full_name}</h2>
              <p className="text-gray-600">{user?.role} - {user?.pluga?.name}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Username Field */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <User size={16} />
                  שם משתמש
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  className={`w-full p-2.5 rounded-lg border ${
                    isEditing ? 'border-gray-300 focus:ring-2 focus:ring-military-500' : 'bg-gray-50 border-gray-200'
                  }`}
                />
              </div>

              {/* Full Name Field */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Award size={16} />
                  שם מלא
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  className={`w-full p-2.5 rounded-lg border ${
                    isEditing ? 'border-gray-300 focus:ring-2 focus:ring-military-500' : 'bg-gray-50 border-gray-200'
                  }`}
                />
              </div>

              {/* Password Fields - Only visible when editing */}
              {isEditing && (
                <>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <Lock size={16} />
                      סיסמה חדשה (אופציונלי)
                    </label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="השאר רוק אם אין שינוי"
                      className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-military-500"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                      <Lock size={16} />
                      אימות סיסמה חדשה
                    </label>
                    <input
                      type="password"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      placeholder="חזור על הסיסמה החדשה"
                      className="w-full p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-military-500"
                    />
                  </div>
                </>
              )}

              {/* Read Only Fields */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Shield size={16} />
                  תפקיד
                </label>
                <input
                  type="text"
                  value={user?.role || ''}
                  disabled
                  className="w-full p-2.5 rounded-lg border border-gray-200 bg-gray-50 text-gray-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Shield size={16} />
                  פלוגה
                </label>
                <input
                  type="text"
                  value={user?.pluga?.name || ''}
                  disabled
                  className="w-full p-2.5 rounded-lg border border-gray-200 bg-gray-50 text-gray-500"
                />
              </div>
            </div>

            {isEditing && (
              <div className="flex gap-4 pt-4 border-t border-gray-100">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2.5 bg-military-600 text-white rounded-lg hover:bg-military-700 transition disabled:opacity-50"
                >
                  <Save size={20} />
                  {loading ? 'שומר...' : 'שמור שינויים'}
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                >
                  ביטול
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
