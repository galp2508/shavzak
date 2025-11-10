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
      setShavzak(response.data);
    } catch (error) {
      toast.error('שגיאה בטעינת שיבוץ');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  const groupedByDay = {};
  shavzak.assignments.forEach(assignment => {
    if (!groupedByDay[assignment.day]) {
      groupedByDay[assignment.day] = [];
    }
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

      {Object.keys(groupedByDay).sort().map(day => (
        <div key={day} className="card">
          <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
            <Calendar size={24} className="text-military-600" />
            יום {parseInt(day) + 1}
          </h2>

          <div className="space-y-4">
            {groupedByDay[day].map(assignment => (
              <div key={assignment.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-gray-900">{assignment.name}</h3>
                    <p className="text-sm text-gray-600">{assignment.type}</p>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600">
                    <Clock size={16} />
                    <span className="text-sm">
                      {assignment.start_hour.toString().padStart(2, '0')}:00 - {(assignment.start_hour + assignment.length_in_hours).toString().padStart(2, '0')}:00
                    </span>
                  </div>
                </div>

                {assignment.soldiers.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {assignment.soldiers.map(soldier => (
                      <span key={soldier.id} className={`badge ${
                        soldier.role === 'commander' ? 'badge-purple' :
                        soldier.role === 'driver' ? 'badge-blue' : 'badge-green'
                      }`}>
                        {soldier.name} ({soldier.role})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ShavzakView;
