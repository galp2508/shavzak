import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight, Clock, Users, RefreshCw, Shield } from 'lucide-react';
import { toast } from 'react-toastify';
import Constraints from './Constraints';

const LiveSchedule = () => {
  const { user } = useAuth();
  const [currentDate, setCurrentDate] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConstraints, setShowConstraints] = useState(false);

  useEffect(() => {
    // התחל עם מחר
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setCurrentDate(tomorrow);
    loadMahalkot();
  }, []);

  useEffect(() => {
    if (currentDate) {
      loadSchedule(currentDate);
    }
  }, [currentDate]);

  // טיפול במקלדת - חצים
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') {
        navigateDay(-1); // ימינה = אתמול (RTL)
      } else if (e.key === 'ArrowLeft') {
        navigateDay(1); // שמאלה = מחר (RTL)
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentDate]);

  const loadMahalkot = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      setMahalkot(response.data.mahalkot || []);
    } catch (error) {
      console.error('Error loading mahalkot:', error);
    }
  };

  const loadSchedule = async (date) => {
    setLoading(true);
    try {
      const dateStr = date.toISOString().split('T')[0];
      const response = await api.get(`/plugot/${user.pluga_id}/live-schedule?date=${dateStr}`);
      setScheduleData(response.data);
    } catch (error) {
      const errorData = error.response?.data;
      let errorMessage = errorData?.error || error.message;

      // הוסף המלצות אם קיימות
      if (errorData?.suggestions && errorData.suggestions.length > 0) {
        errorMessage += '\n\nהמלצות:\n' + errorData.suggestions.map(s => `• ${s}`).join('\n');
      }

      // הצג גם פרטים טכניים אם קיימים
      if (errorData?.technical_details) {
        console.error('Technical details:', errorData.technical_details);
      }

      toast.error(errorMessage, { autoClose: 8000 });
      console.error('Load schedule error:', error);
    } finally {
      setLoading(false);
    }
  };

  const navigateDay = (days) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + days);
    setCurrentDate(newDate);
  };

  const getMahlakaColor = (mahlakaId) => {
    const mahlaka = mahalkot.find(m => m.id === mahlakaId);
    return mahlaka?.color || '#6B7280';
  };

  const getDayName = (date) => {
    const days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
    return days[date.getDay()];
  };

  if (loading && !scheduleData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Date Navigation */}
      <div className="card bg-gradient-to-r from-military-600 to-military-700 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <Calendar className="w-12 h-12" />
            <div className="flex-1">
              <h1 className="text-3xl font-bold">שיבוץ חי</h1>
              <p className="text-military-100">ניווט אוטומטי בין ימים</p>
            </div>
          </div>

          {/* Date Navigation */}
          <div className="flex items-center gap-4 bg-white bg-opacity-20 rounded-lg p-3">
            <button
              onClick={() => navigateDay(-1)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="יום קודם (מקש חץ ימינה)"
            >
              <ChevronRight size={24} />
            </button>

            <div className="text-center min-w-[200px]">
              <div className="text-2xl font-bold">
                {currentDate && getDayName(currentDate)}
              </div>
              <div className="text-sm opacity-90">
                {currentDate && currentDate.toLocaleDateString('he-IL')}
              </div>
            </div>

            <button
              onClick={() => navigateDay(1)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="יום הבא (מקש חץ שמאלה)"
            >
              <ChevronLeft size={24} />
            </button>
          </div>

          <div className="flex items-center gap-2 mr-4">
            {(user.role === 'מפ' || user.role === 'ממ') && (
              <button
                onClick={() => setShowConstraints(true)}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                title="אילוצי שיבוץ"
              >
                <Shield size={24} />
              </button>
            )}
            <button
              onClick={() => loadSchedule(currentDate)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="רענן"
              disabled={loading}
            >
              <RefreshCw size={24} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="card bg-blue-50 border-l-4 border-blue-500">
        <div className="flex items-center gap-2 text-blue-700">
          <kbd className="px-2 py-1 bg-white border border-blue-300 rounded text-sm">←</kbd>
          <span>יום הבא</span>
          <span className="mx-2">•</span>
          <kbd className="px-2 py-1 bg-white border border-blue-300 rounded text-sm">→</kbd>
          <span>יום קודם</span>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="card text-center py-12">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">טוען שיבוץ...</p>
        </div>
      ) : scheduleData?.assignments?.length === 0 ? (
        /* No Assignments */
        <div className="card text-center py-12">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-700 mb-2">אין משימות ליום זה</h3>
          <p className="text-gray-500">לא נמצאו משימות לתאריך {scheduleData?.date_display}</p>
          <p className="text-sm text-gray-400 mt-2">
            ודא שיש תבניות משימות מוגדרות במערכת
          </p>
        </div>
      ) : (
        /* Assignments List */
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              משימות ליום {getDayName(currentDate)}
            </h2>
            <span className="text-sm text-gray-500">
              {scheduleData?.assignments?.length} משימות
            </span>
          </div>

          <div className="space-y-4">
            {scheduleData?.assignments
              .sort((a, b) => a.start_hour - b.start_hour)
              .map((assignment) => {
                const startHour = assignment.start_hour || 0;
                const lengthInHours = assignment.length_in_hours || 1;
                const endHour = startHour + lengthInHours;
                const mahlakaColor = assignment.assigned_mahlaka_id
                  ? getMahlakaColor(assignment.assigned_mahlaka_id)
                  : '#6B7280';

                return (
                  <div
                    key={assignment.id}
                    className="p-4 rounded-lg hover:shadow-md transition-all"
                    style={{
                      backgroundColor: `${mahlakaColor}15`,
                      borderRight: `4px solid ${mahlakaColor}`,
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-gray-900">
                            {assignment.name || 'משימה'}
                          </h3>
                          <span
                            className="text-xs px-2 py-1 rounded-full text-white font-medium"
                            style={{ backgroundColor: mahlakaColor }}
                          >
                            {assignment.type || 'כללי'}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <Clock size={16} />
                        <span className="text-sm font-medium">
                          {startHour.toString().padStart(2, '0')}:00 -{' '}
                          {endHour.toString().padStart(2, '0')}:00
                        </span>
                      </div>
                    </div>

                    {/* Soldiers List */}
                    {assignment.soldiers && assignment.soldiers.length > 0 && (
                      <div className="flex items-start gap-2 pt-3 border-t border-gray-200">
                        <Users size={16} className="text-gray-500 mt-1" />
                        <div className="flex flex-wrap gap-2">
                          {assignment.soldiers.map((soldier) => (
                            <div
                              key={soldier.id}
                              className="bg-white px-3 py-1 rounded-lg text-sm border border-gray-200"
                            >
                              <span className="font-medium">{soldier.name}</span>
                              <span className="text-gray-500 mr-2">
                                ({soldier.role_in_assignment})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Constraints Modal */}
      {showConstraints && (
        <Constraints
          onClose={() => setShowConstraints(false)}
          onUpdate={() => {
            // רענן את השיבוץ החי כאשר האילוצים משתנים
            if (currentDate) {
              loadSchedule(currentDate);
            }
          }}
        />
      )}
    </div>
  );
};

export default LiveSchedule;
