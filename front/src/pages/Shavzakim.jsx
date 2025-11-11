import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Calendar, Plus, Eye, Trash2, X } from 'lucide-react';
import { toast } from 'react-toastify';
import { format } from 'date-fns';

const Shavzakim = () => {
  const { user } = useAuth();
  const [shavzakim, setShavzakim] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

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

  const handleDelete = async (id) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את השיבוץ? כל המשימות יימחקו גם כן.')) {
      return;
    }

    try {
      await api.delete(`/shavzakim/${id}`);
      toast.success('השיבוץ נמחק בהצלחה');
      loadShavzakim();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת שיבוץ');
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
          <button
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center gap-2"
          >
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
              <div className="flex gap-2">
                <Link to={`/shavzakim/${shavzak.id}`} className="btn-secondary flex items-center gap-2 text-sm">
                  <Eye size={16} />
                  <span>צפה</span>
                </Link>
                {(user.role === 'מפ' || user.role === 'ממ') && (
                  <button
                    onClick={() => handleDelete(shavzak.id)}
                    className="text-red-600 hover:text-red-800 p-2"
                    title="מחק"
                  >
                    <Trash2 size={18} />
                  </button>
                )}
              </div>
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

      {/* Shavzak Modal */}
      {showModal && (
        <ShavzakModal
          plugaId={user.pluga_id}
          userId={user.id}
          onClose={() => setShowModal(false)}
          onSave={() => {
            setShowModal(false);
            loadShavzakim();
          }}
        />
      )}
    </div>
  );
};

// Shavzak Modal Component
const ShavzakModal = ({ plugaId, userId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    start_date: new Date().toISOString().split('T')[0],
    days_count: 7,
    min_rest_hours: 8,
    emergency_mode: false,
  });
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/shavzakim', {
        ...formData,
        pluga_id: plugaId,
      });

      const shavzakId = response.data.shavzak.id;
      toast.success('שיבוץ נוצר בהצלחה');

      // שאל אם רוצה לייצר את השיבוץ אוטומטית
      if (window.confirm('האם תרצה לייצר את השיבוץ אוטומטית כעת?')) {
        setGenerating(true);
        try {
          const generateResponse = await api.post(`/shavzakim/${shavzakId}/generate`);
          toast.success('השיבוץ בוצע בהצלחה!');
          if (generateResponse.data.warnings && generateResponse.data.warnings.length > 0) {
            toast.warning(`${generateResponse.data.warnings.length} אזהרות בשיבוץ`);
          }
        } catch (genError) {
          toast.error(genError.response?.data?.error || 'שגיאה ביצירת שיבוץ');
        } finally {
          setGenerating(false);
        }
      }

      onSave();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בשמירה');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <h2 className="text-2xl font-bold">שיבוץ חדש</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="label">שם השיבוץ *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input-field"
              placeholder='למשל: "שיבוץ שבוע 23-29.11"'
              required
            />
          </div>

          <div>
            <label className="label">תאריך התחלה *</label>
            <input
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              className="input-field"
              required
            />
          </div>

          <div>
            <label className="label">מספר ימים *</label>
            <input
              type="number"
              min="1"
              max="30"
              value={formData.days_count}
              onChange={(e) => setFormData({ ...formData, days_count: parseInt(e.target.value) })}
              className="input-field"
              required
            />
          </div>

          <div>
            <label className="label">שעות מנוחה מינימליות</label>
            <input
              type="number"
              min="4"
              max="12"
              value={formData.min_rest_hours}
              onChange={(e) => setFormData({ ...formData, min_rest_hours: parseInt(e.target.value) })}
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">מומלץ 8 שעות</p>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading || generating}
              className="flex-1 btn-primary"
            >
              {loading ? 'יוצר...' : generating ? 'מייצר שיבוץ...' : 'צור שיבוץ'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-secondary"
              disabled={loading || generating}
            >
              ביטול
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Shavzakim;
