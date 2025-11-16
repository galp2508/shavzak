import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight, Clock, Users, RefreshCw, Shield, AlertTriangle, Trash2 } from 'lucide-react';
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

  // האזן לשינויים בתבניות משימות
  useEffect(() => {
    const handleTemplateChange = () => {
      if (currentDate) {
        loadSchedule(currentDate);
      }
    };

    window.addEventListener('templateChanged', handleTemplateChange);
    return () => window.removeEventListener('templateChanged', handleTemplateChange);
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

  const deleteAssignment = async (assignmentId, assignmentName) => {
    if (!window.confirm(`האם אתה בטוח שברצונך למחוק את המשימה "${assignmentName}"?`)) {
      return;
    }

    try {
      await api.delete(`/assignments/${assignmentId}`);
      toast.success(`המשימה "${assignmentName}" נמחקה בהצלחה`);
      // רענן את הנתונים
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error deleting assignment:', error);
      toast.error(error.response?.data?.error || 'שגיאה במחיקת המשימה');
    }
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
        <>
          {/* Warnings Section */}
          {scheduleData?.warnings && scheduleData.warnings.length > 0 && (
            <div className="card bg-yellow-50 border-r-4 border-yellow-500">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-yellow-900 mb-3">
                    אזהרות שיבוץ ({scheduleData.warnings.length})
                  </h3>
                  <div className="space-y-3">
                    {scheduleData.warnings.map((warning, index) => {
                      // תמיכה בפורמט ישן (string) וחדש (object)
                      const isObject = typeof warning === 'object';
                      const message = isObject ? warning.message : warning;
                      const severity = isObject ? warning.severity : 'warning';
                      const suggestion = isObject ? warning.suggestion : null;
                      const suggestDeletion = isObject ? warning.suggest_deletion : false;
                      const assignmentId = isObject ? warning.assignment_id : null;
                      const assignmentName = isObject ? warning.assignment_name : null;

                      // צבעים לפי רמת חומרה
                      const severityColors = {
                        critical: 'bg-red-100 border-red-300',
                        high: 'bg-orange-100 border-orange-300',
                        warning: 'bg-yellow-100 border-yellow-300'
                      };
                      const bgColor = severityColors[severity] || severityColors.warning;

                      return (
                        <div key={index} className={`p-3 rounded-lg border-r-2 ${bgColor}`}>
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <p className="text-gray-800 text-sm font-medium mb-1">
                                {message}
                              </p>
                              {suggestion && (
                                <p className="text-gray-700 text-xs mt-2 bg-white/60 p-2 rounded">
                                  💡 {suggestion}
                                </p>
                              )}
                            </div>
                            {suggestDeletion && assignmentId && (
                              <button
                                onClick={() => deleteAssignment(assignmentId, assignmentName)}
                                className="btn-secondary-sm flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white border-red-700"
                                title="מחק משימה זו"
                              >
                                <Trash2 className="w-4 h-4" />
                                <span className="text-xs">מחק</span>
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                לוח שעות - {getDayName(currentDate)}
              </h2>
              <span className="text-sm text-gray-500">
                {scheduleData?.assignments?.length} משימות
              </span>
            </div>

            {/* Time Grid Schedule */}
            <div className="overflow-x-auto">
              {(() => {
                // קבל את כל סוגי המשימות הייחודיים
                const assignmentTypes = [...new Set(scheduleData?.assignments?.map(a => a.type) || [])].sort();

                // צור מפה של משימות לפי סוג ושעה
                const assignmentsByType = {};
                assignmentTypes.forEach(type => {
                  assignmentsByType[type] = [];
                });

                scheduleData?.assignments?.forEach(assignment => {
                  if (!assignmentsByType[assignment.type]) {
                    assignmentsByType[assignment.type] = [];
                  }
                  assignmentsByType[assignment.type].push(assignment);
                });

                // יצירת 24 שעות
                const hours = Array.from({ length: 24 }, (_, i) => i);

                return (
                  <div className="min-w-max">
                    {/* Header - סוגי משימות */}
                    <div className="flex border-b-2 border-gray-300 mb-2">
                      <div className="w-20 flex-shrink-0 font-bold text-gray-700 p-2">
                        שעה
                      </div>
                      {assignmentTypes.map(type => (
                        <div
                          key={type}
                          className="flex-1 min-w-[200px] font-bold text-center p-2 bg-gray-100 border-l border-gray-300"
                        >
                          {type}
                        </div>
                      ))}
                    </div>

                    {/* Grid Container */}
                    <div className="flex">
                      {/* Hours Column */}
                      <div className="w-20 flex-shrink-0">
                        {hours.map(hour => (
                          <div
                            key={hour}
                            className="h-16 flex items-center justify-center border-b border-gray-200 text-sm text-gray-600 font-medium"
                          >
                            {hour.toString().padStart(2, '0')}:00
                          </div>
                        ))}
                      </div>

                      {/* Assignment Type Columns */}
                      {assignmentTypes.map(type => (
                        <div key={type} className="flex-1 min-w-[200px] border-l border-gray-300 relative">
                          {/* Hour Grid Lines */}
                          {hours.map(hour => (
                            <div
                              key={hour}
                              className="h-16 border-b border-gray-200"
                            />
                          ))}

                          {/* Assignment Blocks - Positioned Absolutely */}
                          <div className="absolute inset-0">
                            {assignmentsByType[type]?.map(assignment => {
                              const startHour = assignment.start_hour || 0;
                              const lengthInHours = assignment.length_in_hours || 1;
                              const endHour = startHour + lengthInHours;
                              const mahlakaColor = assignment.assigned_mahlaka_id
                                ? getMahlakaColor(assignment.assigned_mahlaka_id)
                                : '#6B7280';

                              // Calculate position and height
                              const topPosition = (startHour / 24) * 100;
                              const height = (lengthInHours / 24) * 100;

                              return (
                                <div
                                  key={assignment.id}
                                  className="absolute inset-x-1 rounded-lg shadow-md overflow-hidden group cursor-pointer hover:shadow-lg transition-all"
                                  style={{
                                    top: `${topPosition}%`,
                                    height: `${height}%`,
                                    backgroundColor: mahlakaColor,
                                    border: `2px solid ${mahlakaColor}`,
                                  }}
                                  title={`${assignment.name} (${startHour.toString().padStart(2, '0')}:00 - ${endHour.toString().padStart(2, '0')}:00)`}
                                >
                                  {/* Assignment Content */}
                                  <div className="p-2 h-full flex flex-col text-white">
                                    {/* Assignment Name & Time */}
                                    <div className="font-bold text-sm mb-1">
                                      {assignment.name}
                                    </div>
                                    <div className="text-xs opacity-90 mb-2">
                                      {startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00
                                    </div>

                                    {/* Soldiers List */}
                                    {assignment.soldiers && assignment.soldiers.length > 0 && (
                                      <div className="flex-1 overflow-y-auto">
                                        <div className="space-y-1">
                                          {assignment.soldiers.map((soldier) => (
                                            <div
                                              key={soldier.id}
                                              className="text-xs bg-white/20 backdrop-blur-sm px-2 py-1 rounded"
                                            >
                                              <div className="font-medium">{soldier.name}</div>
                                              <div className="text-[10px] opacity-80">
                                                {soldier.role_in_assignment}
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {/* No soldiers indicator */}
                                    {(!assignment.soldiers || assignment.soldiers.length === 0) && (
                                      <div className="text-xs opacity-75 italic">
                                        אין חיילים
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        </>
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
