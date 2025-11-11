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
      console.log('Shavzak response:', response.data);
      setShavzak(response.data || {});
    } catch (error) {
      toast.error('שגיאה בטעינת שיבוץ');
      console.error('Error loading shavzak:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  if (!shavzak || !shavzak.shavzak) {
    return (
      <div className="card">
        <p className="text-center text-gray-600">שיבוץ לא נמצא</p>
      </div>
    );
  }

  const groupedByDay = {};
  const assignments = shavzak?.assignments || [];
  assignments.forEach((assignment) => {
    if (!groupedByDay[assignment.day]) groupedByDay[assignment.day] = [];
    groupedByDay[assignment.day].push(assignment);
  });

  return (
    <div className="space-y-6">
      <div className="card bg-gradient-to-r from-military-600 to-military-700 text-white">
        <div className="flex items-center gap-4">
          <Calendar className="w-12 h-12" />
          <div>
            <h1 className="text-3xl font-bold">{shavzak.shavzak.name}</h1>
            <p className="text-military-100">
              {new Date(shavzak.shavzak.start_date).toLocaleDateString('he-IL')} · {shavzak.shavzak.days_count} ימים
            </p>
          </div>
        </div>
      </div>

      {assignments.length === 0 ? (
        <div className="card">
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">אין משימות בשיבוץ זה</p>
            <p className="text-sm text-gray-500 mt-2">ייתכן שהשיבוץ עדיין לא הופעל או שלא נוצרו משימות</p>
          </div>
        </div>
      ) : (
        Object.keys(groupedByDay).sort((a, b) => parseInt(a) - parseInt(b)).map(day => (
          <div key={day} className="card">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Calendar size={24} className="text-military-600" />
              יום {parseInt(day) + 1}
            </h2>

            <div className="space-y-4">
              {groupedByDay[day].map(assignment => (
                <div key={assignment.id} className="p-4 bg-gray-50 rounded-lg border-r-4 border-military-600">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-gray-900 text-lg">{assignment.name}</h3>
                      <p className="text-sm text-gray-600">{assignment.assignment_type || assignment.type}</p>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600 bg-white px-3 py-2 rounded-lg">
                      <Clock size={16} />
                      <span className="text-sm font-medium">
                        {assignment.start_hour.toString().padStart(2, '0')}:00 - {(assignment.start_hour + assignment.length_in_hours).toString().padStart(2, '0')}:00
                      </span>
                    </div>
                  </div>

                  {assignment.soldiers_assigned && assignment.soldiers_assigned.length > 0 ? (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Users size={14} />
                        חיילים משובצים ({assignment.soldiers_assigned.length})
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {assignment.soldiers_assigned.map((soldierAssignment, idx) => (
                          <span key={idx} className={`badge ${
                            soldierAssignment.role_in_assignment === 'מפקד' || soldierAssignment.role_in_assignment === 'commander' ? 'badge-purple' :
                            soldierAssignment.role_in_assignment === 'נהג' || soldierAssignment.role_in_assignment === 'driver' ? 'badge-blue' :
                            'badge-green'
                          }`}>
                            {soldierAssignment.soldier?.name || soldierAssignment.soldier_name || 'חייל'}
                            {soldierAssignment.role_in_assignment && ` (${soldierAssignment.role_in_assignment})`}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : assignment.soldiers && assignment.soldiers.length > 0 ? (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Users size={14} />
                        חיילים משובצים ({assignment.soldiers.length})
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {assignment.soldiers.map((soldier, idx) => (
                          <span key={idx} className={`badge ${
                            soldier.role === 'commander' || soldier.role === 'מפקד' ? 'badge-purple' :
                            soldier.role === 'driver' || soldier.role === 'נהג' ? 'badge-blue' : 'badge-green'
                          }`}>
                            {soldier.name} ({soldier.role})
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 italic flex items-center gap-2">
                      <Users size={14} />
                      אין חיילים משובצים למשימה זו
                    </div>
                  )}

                  {assignment.assigned_mahlaka_id && (
                    <div className="mt-2 text-xs text-gray-500">
                      מחלקה משובצת: מחלקה {assignment.assigned_mahlaka_id}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default ShavzakView;
