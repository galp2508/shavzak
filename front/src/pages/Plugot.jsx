import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Edit, Plus } from 'lucide-react';
import { toast } from 'react-toastify';

const Plugot = () => {
  const { user } = useAuth();
  const [pluga, setPluga] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    gdud: '',
    color: '#34996e',
  });

  useEffect(() => {
    loadPluga();
  }, []);

  const loadPluga = async () => {
    if (!user.pluga_id) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.get(`/plugot/${user.pluga_id}`);
      setPluga(response.data.pluga);
      setFormData({
        name: response.data.pluga.name,
        gdud: response.data.pluga.gdud,
        color: response.data.pluga.color,
      });
    } catch (error) {
      toast.error('שגיאה בטעינת פרטי הפלוגה');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (pluga) {
        await api.put(`/plugot/${pluga.id}`, formData);
        toast.success('הפלוגה עודכנה בהצלחה');
      } else {
        await api.post('/plugot', formData);
        toast.success('הפלוגה נוצרה בהצלחה');
      }
      setEditing(false);
      loadPluga();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בשמירה');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  if (!pluga && !editing) {
    return (
      <div className="text-center py-12">
        <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">אין פלוגה במערכת</h2>
        <p className="text-gray-600 mb-6">צור פלוגה חדשה להתחלת העבודה</p>
        <button onClick={() => setEditing(true)} className="btn-primary flex items-center gap-2 mx-auto">
          <Plus size={20} />
          <span>צור פלוגה</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">ניהול הפלוגה</h1>
        {pluga && !editing && (
          <button onClick={() => setEditing(true)} className="btn-primary flex items-center gap-2">
            <Edit size={20} />
            <span>ערוך</span>
          </button>
        )}
      </div>

      {editing ? (
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="label">שם הפלוגה</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
                required
                placeholder="פלוגה ב"
              />
            </div>

            <div>
              <label className="label">גדוד</label>
              <input
                type="text"
                value={formData.gdud}
                onChange={(e) => setFormData({ ...formData, gdud: e.target.value })}
                className="input-field"
                placeholder="גדוד פנתר"
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

            <div className="flex gap-3">
              <button type="submit" className="btn-primary">שמור</button>
              <button type="button" onClick={() => setEditing(false)} className="btn-secondary">ביטול</button>
            </div>
          </form>
        </div>
      ) : (
        <div className="card" style={{ borderTop: `4px solid ${pluga.color}` }}>
          <div className="flex items-center gap-4 mb-6">
            <div className="bg-military-100 p-4 rounded-xl" style={{ backgroundColor: `${pluga.color}20` }}>
              <Shield className="w-12 h-12" style={{ color: pluga.color }} />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-gray-900">{pluga.name}</h2>
              <p className="text-gray-600">{pluga.gdud}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-gray-200">
            <div>
              <p className="text-sm text-gray-600">מחלקות</p>
              <p className="text-2xl font-bold text-gray-900">{pluga.mahalkot_count || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">צבע זיהוי</p>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded" style={{ backgroundColor: pluga.color }}></div>
                <p className="font-mono text-sm text-gray-700">{pluga.color}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-600">סטטוס</p>
              <span className="badge badge-green">פעיל</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Plugot;
