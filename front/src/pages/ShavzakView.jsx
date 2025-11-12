import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, Users, Clock, Edit, Trash2, Plus } from 'lucide-react';
import { toast } from 'react-toastify';

const ShavzakView = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [shavzak, setShavzak] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);

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
                              <button
                                onClick={() => handleDeleteAssignment(assignment.id)}
                                className="text-red-600 hover:text-red-800"
                                title="מחק משימה"
                              >
                                <Trash2 size={18} />
                              </button>
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

export default ShavzakView;
