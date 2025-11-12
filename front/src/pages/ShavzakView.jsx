import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, Users, Clock, Edit, Trash2, Plus, Copy, List, LayoutGrid } from 'lucide-react';
import { toast } from 'react-toastify';

const ShavzakView = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [shavzak, setShavzak] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'timeline'

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [shavzakRes, mahalkotRes] = await Promise.all([
        api.get(`/shavzakim/${id}`),
        api.get(`/plugot/${user.pluga_id}/mahalkot`)
      ]);

      setShavzak(shavzakRes.data || {});
      setMahalkot(mahalkotRes.data.mahalkot || []);
    } catch (error) {
      toast.error('שגיאה בטעינת נתונים');
    } finally {
      setLoading(false);
    }
  };

  const getMahlakaColor = (mahlakaId) => {
    const mahlaka = mahalkot.find(m => m.id === mahlakaId);
    return mahlaka?.color || '#6B7280'; // gray-500 as default
  };

  const handleDeleteAssignment = async (assignmentId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את המשימה?')) {
      return;
    }

    try {
      await api.delete(`/assignments/${assignmentId}`);
      toast.success('המשימה נמחקה בהצלחה');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת משימה');
    }
  };

  const handleDuplicateAssignment = async (assignmentId) => {
    try {
      const response = await api.post(`/assignments/${assignmentId}/duplicate`, {
        duplicate_soldiers: false
      });
      toast.success('המשימה שוכפלה בהצלחה');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בשכפול משימה');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  const shavzakData = shavzak?.shavzak || shavzak;
  const assignments = shavzak?.assignments || [];

  // קיבוץ משימות לפי ימים
  const groupedByDay = {};
  assignments.forEach((assignment) => {
    const day = assignment.day || 0;
    if (!groupedByDay[day]) groupedByDay[day] = [];
    groupedByDay[day].push(assignment);
  });

  // מיון ימים
  const sortedDays = Object.keys(groupedByDay).sort((a, b) => parseInt(a) - parseInt(b));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card bg-gradient-to-r from-military-600 to-military-700 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Calendar className="w-12 h-12" />
            <div>
              <h1 className="text-3xl font-bold">{shavzakData?.name || 'שיבוץ'}</h1>
              {shavzakData?.start_date && (
                <p className="text-military-100">
                  {new Date(shavzakData.start_date).toLocaleDateString('he-IL')}
                  {shavzakData?.days_count && ` · ${shavzakData.days_count} ימים`}
                </p>
              )}
            </div>
          </div>
          {assignments.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('list')}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white text-military-700'
                    : 'bg-military-700 text-white hover:bg-military-800'
                }`}
              >
                <List size={20} />
                <span>רשימה</span>
              </button>
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  viewMode === 'timeline'
                    ? 'bg-white text-military-700'
                    : 'bg-military-700 text-white hover:bg-military-800'
                }`}
              >
                <LayoutGrid size={20} />
                <span>לוח זמנים</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* אם אין משימות, הצג הודעה ברורה */}
      {assignments.length === 0 ? (
        <div className="card text-center py-12">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-700 mb-2">אין משימות בשיבוץ זה</h3>
          <p className="text-gray-500 mb-4">לא נמצאו משימות לשיבוץ זה</p>
          {(user.role === 'מפ' || user.role === 'ממ') && (
            <button
              onClick={async () => {
                if (window.confirm('האם לייצר את השיבוץ אוטומטית כעת?')) {
                  try {
                    await api.post(`/shavzakim/${id}/generate`);
                    toast.success('השיבוץ בוצע בהצלחה!');
                    loadData();
                  } catch (error) {
                    toast.error(error.response?.data?.error || 'שגיאה ביצירת שיבוץ');
                  }
                }
              }}
              className="btn-primary mx-auto"
            >
              <Plus size={20} className="inline ml-2" />
              צור שיבוץ אוטומטי
            </button>
          )}
        </div>
      ) : viewMode === 'timeline' ? (
        /* תצוגת לוח זמנים */
        <TimelineView
          assignments={assignments}
          sortedDays={sortedDays}
          getMahlakaColor={getMahlakaColor}
          handleDuplicateAssignment={handleDuplicateAssignment}
          handleDeleteAssignment={handleDeleteAssignment}
          userRole={user.role}
        />
      ) : (
        <>
          {/* הצגת משימות ממוינות לפי ימים */}
          {sortedDays.map(day => {
            // מיון המשימות של היום לפי שעת התחלה
            const dayAssignments = groupedByDay[day].sort((a, b) =>
              (a.start_hour || 0) - (b.start_hour || 0)
            );

            return (
              <div key={day} className="card">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                  <Calendar size={24} className="text-military-600" />
                  יום {parseInt(day) + 1}
                </h2>

                <div className="space-y-4">
                  {dayAssignments.map(assignment => {
                    const startHour = assignment.start_hour || 0;
                    const lengthInHours = assignment.length_in_hours || 1;
                    const endHour = startHour + lengthInHours;
                    const soldiers = assignment.soldiers || [];
                    const mahlakaColor = assignment.assigned_mahlaka_id
                      ? getMahlakaColor(assignment.assigned_mahlaka_id)
                      : '#6B7280';

                    return (
                      <div
                        key={assignment.id}
                        className="p-4 rounded-lg hover:shadow-md transition-all"
                        style={{
                          backgroundColor: `${mahlakaColor}15`,
                          borderRight: `4px solid ${mahlakaColor}`
                        }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-bold text-gray-900">{assignment.name || 'משימה'}</h3>
                              <span
                                className="text-xs px-2 py-1 rounded-full text-white font-medium"
                                style={{ backgroundColor: mahlakaColor }}
                              >
                                {assignment.type || 'כללי'}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 text-gray-600">
                              <Clock size={16} />
                              <span className="text-sm font-medium">
                                {startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00
                              </span>
                            </div>
                            {(user.role === 'מפ' || user.role === 'ממ') && (
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleDuplicateAssignment(assignment.id)}
                                  className="text-blue-600 hover:text-blue-800"
                                  title="שכפל משימה"
                                >
                                  <Copy size={18} />
                                </button>
                                <button
                                  onClick={() => handleDeleteAssignment(assignment.id)}
                                  className="text-red-600 hover:text-red-800"
                                  title="מחק משימה"
                                >
                                  <Trash2 size={18} />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* הצגת חיילים משובצים */}
                        {soldiers.length > 0 ? (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Users size={16} className="text-gray-500" />
                              <span className="text-sm font-medium text-gray-700">חיילים משובצים:</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {soldiers.map((soldier, idx) => (
                                <span
                                  key={soldier.id || idx}
                                  className={`badge ${
                                    soldier.role === 'מפקד' || soldier.role === 'commander' ? 'badge-purple' :
                                    soldier.role === 'נהג' || soldier.role === 'driver' ? 'badge-blue' :
                                    'badge-green'
                                  }`}
                                >
                                  {soldier.name}
                                  {soldier.role && ` (${soldier.role})`}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-gray-500 italic">
                            אין חיילים משובצים למשימה זו
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
};

// Timeline View Component
const TimelineView = ({ assignments, sortedDays, getMahlakaColor, handleDuplicateAssignment, handleDeleteAssignment, userRole }) => {
  // מציאת טווח השעות
  const hours = [];
  let minHour = 24;
  let maxHour = 0;

  assignments.forEach(assignment => {
    const startHour = assignment.start_hour || 0;
    const endHour = startHour + (assignment.length_in_hours || 1);
    if (startHour < minHour) minHour = startHour;
    if (endHour > maxHour) maxHour = endHour;
  });

  // יצירת רשימת שעות
  for (let i = minHour; i <= maxHour; i++) {
    hours.push(i);
  }

  // קיבוץ משימות לפי יום
  const groupedByDay = {};
  assignments.forEach((assignment) => {
    const day = assignment.day || 0;
    if (!groupedByDay[day]) groupedByDay[day] = [];
    groupedByDay[day].push(assignment);
  });

  return (
    <div className="card overflow-x-auto">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <LayoutGrid size={24} className="text-military-600" />
        לוח זמנים
      </h2>

      <div className="min-w-max">
        <div className="grid gap-2" style={{ gridTemplateColumns: `100px repeat(${sortedDays.length}, 1fr)` }}>
          {/* כותרת - שעות וימים */}
          <div className="font-bold text-center p-2 bg-gray-100 rounded">שעה</div>
          {sortedDays.map(day => (
            <div key={day} className="font-bold text-center p-2 bg-gray-100 rounded">
              יום {parseInt(day) + 1}
            </div>
          ))}

          {/* שורות השעות */}
          {hours.map(hour => (
            <>
              <div key={`hour-${hour}`} className="font-medium text-center p-2 bg-gray-50 rounded flex items-center justify-center">
                {hour.toString().padStart(2, '0')}:00
              </div>

              {sortedDays.map(day => {
                const dayAssignments = groupedByDay[day] || [];
                const assignmentsInHour = dayAssignments.filter(assignment => {
                  const startHour = assignment.start_hour || 0;
                  const endHour = startHour + (assignment.length_in_hours || 1);
                  return startHour <= hour && hour < endHour;
                });

                return (
                  <div key={`${day}-${hour}`} className="relative min-h-[60px] border border-gray-200 rounded p-1">
                    {assignmentsInHour.map((assignment, idx) => {
                      const startHour = assignment.start_hour || 0;
                      const mahlakaColor = assignment.assigned_mahlaka_id
                        ? getMahlakaColor(assignment.assigned_mahlaka_id)
                        : '#6B7280';

                      // הצג את המשימה רק בשעת ההתחלה שלה
                      if (startHour === hour) {
                        const soldiers = assignment.soldiers || [];
                        return (
                          <div
                            key={assignment.id}
                            className="p-2 rounded text-xs mb-1 relative group"
                            style={{
                              backgroundColor: `${mahlakaColor}30`,
                              borderRight: `3px solid ${mahlakaColor}`,
                              minHeight: `${(assignment.length_in_hours || 1) * 50}px`
                            }}
                          >
                            <div className="font-bold text-gray-900">{assignment.name}</div>
                            <div className="text-gray-600 text-xs mt-1">
                              {startHour.toString().padStart(2, '0')}:00 -
                              {(startHour + (assignment.length_in_hours || 1)).toString().padStart(2, '0')}:00
                            </div>
                            {soldiers.length > 0 && (
                              <div className="mt-1 text-xs text-gray-700">
                                <Users size={12} className="inline ml-1" />
                                {soldiers.length} חיילים
                              </div>
                            )}

                            {/* כפתורי פעולה */}
                            {(userRole === 'מפ' || userRole === 'ממ') && (
                              <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                                <button
                                  onClick={() => handleDuplicateAssignment(assignment.id)}
                                  className="bg-white p-1 rounded shadow hover:bg-blue-50"
                                  title="שכפל משימה"
                                >
                                  <Copy size={14} className="text-blue-600" />
                                </button>
                                <button
                                  onClick={() => handleDeleteAssignment(assignment.id)}
                                  className="bg-white p-1 rounded shadow hover:bg-red-50"
                                  title="מחק משימה"
                                >
                                  <Trash2 size={14} className="text-red-600" />
                                </button>
                              </div>
                            )}
                          </div>
                        );
                      }
                      return null;
                    })}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ShavzakView;
