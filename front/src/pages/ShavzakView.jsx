import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import { Calendar, Users, Clock } from 'lucide-react';
import { toast } from 'react-toastify';

const ShavzakView = () => {
  const { id } = useParams();
  const [shavzak, setShavzak] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadShavzak();
  }, [id]);

  const loadShavzak = async () => {
    try {
      const response = await api.get(`/shavzakim/${id}`);
      // תמיכה בכמה פורמטים של נתונים מהשרת
      setShavzak(response.data || {});
    } catch (error) {
      toast.error('שגיאה בטעינת שיבוץ');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  // תמיכה בכמה פורמטים של נתונים
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
          <p className="text-gray-500">לא נמצאו משימות לשיבוץ זה</p>
        </div>
      ) : (
        <>
          {/* הצגת משימות ממוינות לפי ימים */}
          {sortedDays.map(day => (
            <div key={day} className="card">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Calendar size={24} className="text-military-600" />
                יום {parseInt(day) + 1}
              </h2>

              <div className="space-y-4">
                {groupedByDay[day].map(assignment => {
                  const startHour = assignment.start_hour || 0;
                  const lengthInHours = assignment.length_in_hours || 1;
                  const endHour = startHour + lengthInHours;
                  const soldiers = assignment.soldiers || [];

                  return (
                    <div key={assignment.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="font-bold text-gray-900">{assignment.name || 'משימה'}</h3>
                          <p className="text-sm text-gray-600">{assignment.type || 'כללי'}</p>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Clock size={16} />
                          <span className="text-sm font-medium">
                            {startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00
                          </span>
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
          ))}
        </>
      )}
    </div>
  );
};

export default ShavzakView;
