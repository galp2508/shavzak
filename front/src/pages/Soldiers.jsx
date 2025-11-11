import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  UserPlus, Search, Edit, Trash2, X, 
  Award, Phone, MapPin, Shield, Calendar 
} from 'lucide-react';
import ROLES from '../constants/roles';
import { toast } from 'react-toastify';

const Soldiers = () => {
  const { user } = useAuth();
  const [soldiers, setSoldiers] = useState([]);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingSoldier, setEditingSoldier] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // טען מחלקות
      const mahalkotRes = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      setMahalkot(mahalkotRes.data.mahalkot);

      // טען חיילים לפי ההרשאה
      let allSoldiers = [];
      for (const mahlaka of mahalkotRes.data.mahalkot) {
        const soldiersRes = await api.get(`/mahalkot/${mahlaka.id}/soldiers`);
        allSoldiers = [...allSoldiers, ...soldiersRes.data.soldiers];
      }
      setSoldiers(allSoldiers);
    } catch (error) {
      toast.error('שגיאה בטעינת נתונים');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSoldiers = soldiers.filter(soldier =>
    soldier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    soldier.role.includes(searchTerm) ||
    soldier.kita?.includes(searchTerm)
  );

  const handleDelete = async (id) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את החייל?')) {
      return;
    }

    try {
      await api.delete(`/soldiers/${id}`);
      toast.success('החייל נמחק בהצלחה');
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת חייל');
    }
  };

  const getRoleBadge = (role) => {
    const badges = {
      'לוחם': 'badge-green',
      'נהג': 'badge-blue',
      'ממ': 'badge-purple',
      'מכ': 'badge-purple',
      'סמל': 'badge-yellow',
    };
    return badges[role] || 'badge-blue';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ניהול חיילים</h1>
          <p className="text-gray-600 mt-1">
            {soldiers.length} חיילים במערכת
          </p>
        </div>
        {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
          <button
            onClick={() => {
              setEditingSoldier(null);
              setShowModal(true);
            }}
            className="btn-primary flex items-center gap-2"
          >
            <UserPlus size={20} />
            <span>הוסף חייל</span>
          </button>
        )}
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute right-3 top-3 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="חפש לפי שם, תפקיד או כיתה..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pr-10"
          />
        </div>
      </div>

      {/* Soldiers Table */}
      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  שם
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  תפקיד
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  כיתה
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  הסמכות
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  סטטוס
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  פעולות
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSoldiers.map((soldier) => (
                <tr key={soldier.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="bg-military-100 p-2 rounded-full">
                        <Shield size={16} className="text-military-600" />
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{soldier.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getRoleBadge(soldier.role)}`}>
                      {soldier.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {soldier.kita || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-wrap gap-1">
                      {soldier.certifications?.map((cert, idx) => (
                        <span key={idx} className="badge badge-blue text-xs">
                          {cert}
                        </span>
                      )) || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {soldier.has_hatashab && (
                      <span className="badge badge-yellow">התש״ב</span>
                    )}
                    {soldier.is_platoon_commander && (
                      <span className="badge badge-purple mr-1">מ״כ</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingSoldier(soldier);
                          setShowModal(true);
                        }}
                        className="text-blue-600 hover:text-blue-800"
                        title="ערוך"
                      >
                        <Edit size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(soldier.id)}
                        className="text-red-600 hover:text-red-800"
                        title="מחק"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredSoldiers.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              לא נמצאו חיילים
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <SoldierModal
          soldier={editingSoldier}
          mahalkot={mahalkot}
          onClose={() => {
            setShowModal(false);
            setEditingSoldier(null);
          }}
          onSave={() => {
            setShowModal(false);
            setEditingSoldier(null);
            loadData();
          }}
        />
      )}
    </div>
  );
};

// Modal Component
const SoldierModal = ({ soldier, mahalkot, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: soldier?.name || '',
    role: soldier?.role || 'לוחם',
    mahlaka_id: soldier?.mahlaka_id || mahalkot[0]?.id || '',
    kita: soldier?.kita || '',
    phone_number: soldier?.phone_number || '',
    has_hatashab: soldier?.has_hatashab || false,
    is_platoon_commander: soldier?.is_platoon_commander || false,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (soldier) {
        await api.put(`/soldiers/${soldier.id}`, formData);
        toast.success('החייל עודכן בהצלחה');
      } else {
        await api.post('/soldiers', formData);
        toast.success('החייל נוסף בהצלחה');
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
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">
            {soldier ? 'עריכת חייל' : 'הוספת חייל חדש'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">שם מלא *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="label">תפקיד *</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="input-field"
                required
              >
                {ROLES.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">מחלקה *</label>
              <select
                value={formData.mahlaka_id}
                onChange={(e) => setFormData({ ...formData, mahlaka_id: parseInt(e.target.value) })}
                className="input-field"
                required
              >
                {mahalkot.map(m => (
                  <option key={m.id} value={m.id}>מחלקה {m.number}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">כיתה</label>
              <input
                type="text"
                value={formData.kita}
                onChange={(e) => setFormData({ ...formData, kita: e.target.value })}
                className="input-field"
                placeholder="א, ב, ג..."
              />
            </div>

            <div>
              <label className="label">טלפון</label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="input-field"
                placeholder="050-1234567"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.has_hatashab}
                onChange={(e) => setFormData({ ...formData, has_hatashab: e.target.checked })}
                className="w-4 h-4 text-military-600"
              />
              <span className="text-gray-700">יש התש״ב</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_platoon_commander}
                onChange={(e) => setFormData({ ...formData, is_platoon_commander: e.target.checked })}
                className="w-4 h-4 text-military-600"
              />
              <span className="text-gray-700">מפקד כיתה</span>
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary"
            >
              {loading ? 'שומר...' : soldier ? 'עדכן' : 'הוסף'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-secondary"
            >
              ביטול
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Soldiers;
