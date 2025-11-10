import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Plus, Users } from 'lucide-react';
import { toast } from 'react-toastify';

const Mahalkot = () => {
  const { user } = useAuth();
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadMahalkot();
  }, []);

  const loadMahalkot = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      setMahalkot(response.data.mahalkot);
    } catch (error) {
      toast.error('שגיאה בטעינת מחלקות');
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
          <h1 className="text-3xl font-bold text-gray-900">מחלקות</h1>
          <p className="text-gray-600 mt-1">{mahalkot.length} מחלקות</p>
        </div>
        {user.role === 'מפ' && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            <span>הוסף מחלקה</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mahalkot.map((mahlaka) => (
          <div key={mahlaka.id} className="card hover:shadow-lg transition-shadow" style={{ borderTop: `4px solid ${mahlaka.color}` }}>
            <div className="flex items-center justify-between mb-4">
              <div className="bg-gray-100 p-3 rounded-lg" style={{ backgroundColor: `${mahlaka.color}20` }}>
                <Shield className="w-8 h-8" style={{ color: mahlaka.color }} />
              </div>
              <span className="badge badge-blue">{mahlaka.soldiers_count} חיילים</span>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">מחלקה {mahlaka.number}</h3>
            <div className="flex items-center gap-2 text-gray-600">
              <Users size={16} />
              <span className="text-sm">{mahlaka.soldiers_count} לוחמים</span>
            </div>
          </div>
        ))}
      </div>

      {mahalkot.length === 0 && (
        <div className="text-center py-12">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">אין מחלקות במערכת</p>
        </div>
      )}

      {showModal && (
        <MahlakaModal
          plugaId={user.pluga_id}
          onClose={() => setShowModal(false)}
          onSave={() => {
            setShowModal(false);
            loadMahalkot();
          }}
        />
      )}
    </div>
  );
};

const MahlakaModal = ({ plugaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    number: '',
    color: '#' + Math.floor(Math.random()*16777215).toString(16),
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api.post('/mahalkot', { ...formData, pluga_id: plugaId });
      toast.success('המחלקה נוצרה בהצלחה');
      onSave();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת מחלקה');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-6">הוספת מחלקה חדשה</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">מספר מחלקה</label>
            <input
              type="number"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: parseInt(e.target.value) })}
              className="input-field"
              required
              min="1"
            />
          </div>

          <div>
            <label className="label">צבע</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-16 h-10 rounded cursor-pointer"
              />
              <input
                type="text"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="input-field flex-1"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" disabled={loading} className="flex-1 btn-primary">
              {loading ? 'יוצר...' : 'צור מחלקה'}
            </button>
            <button type="button" onClick={onClose} className="flex-1 btn-secondary">ביטול</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Mahalkot;
