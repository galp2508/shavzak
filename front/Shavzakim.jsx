import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Calendar, Plus, Eye } from 'lucide-react';
import { toast } from 'react-toastify';
import { format } from 'date-fns';

const Shavzakim = () => {
  const { user } = useAuth();
  const [shavzakim, setShavzakim] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadShavzakim();
  }, []);

  const loadShavzakim = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/shavzakim`);
      setShavzakim(response.data.shavzakim);
    } catch (error) {
      toast.error('שגיאה בטעינת שיבוצים');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">שיבוצים</h1>
          <p className="text-gray-600 mt-1">{shavzakim.length} שיבוצים במערכת</p>
        </div>
        {(user.role === 'מפ' || user.role === 'ממ') && (
          <button className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            <span>שיבוץ חדש</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {shavzakim.map((shavzak) => (
          <div key={shavzak.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-military-100 p-3 rounded-lg">
                <Calendar className="w-8 h-8 text-military-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900">{shavzak.name}</h3>
                <p className="text-sm text-gray-600">
                  {new Date(shavzak.start_date).toLocaleDateString('he-IL')} · {shavzak.days_count} ימים
                </p>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-gray-200">
              <span className="text-xs text-gray-500">
                נוצר {new Date(shavzak.created_at).toLocaleDateString('he-IL')}
              </span>
              <Link to={`/shavzakim/${shavzak.id}`} className="btn-secondary flex items-center gap-2 text-sm">
                <Eye size={16} />
                <span>צפה</span>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {shavzakim.length === 0 && (
        <div className="text-center py-12">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">אין שיבוצים במערכת</p>
        </div>
      )}
    </div>
  );
};

export default Shavzakim;
