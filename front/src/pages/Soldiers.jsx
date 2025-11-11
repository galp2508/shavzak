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
  const [viewingSoldier, setViewingSoldier] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

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

  const handleViewDetails = async (soldierId) => {
    try {
      const response = await api.get(`/soldiers/${soldierId}`);
      setViewingSoldier(response.data.soldier);
      setShowDetailsModal(true);
    } catch (error) {
      toast.error('שגיאה בטעינת פרטי חייל');
      console.error(error);
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
                  פעולות
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSoldiers.map((soldier) => (
                <tr key={soldier.id} className="hover:bg-gray-50">
                  <td
                    className="px-6 py-4 whitespace-nowrap cursor-pointer"
                    onClick={() => handleViewDetails(soldier.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="bg-military-100 p-2 rounded-full">
                        <Shield size={16} className="text-military-600" />
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 hover:text-military-600 transition-colors">{soldier.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getRoleBadge(soldier.role)}`}>
                      {soldier.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {soldier.kita || 'אין כיתה'}
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

      {/* Edit Modal */}
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

      {/* Details Modal */}
      {showDetailsModal && viewingSoldier && (
        <SoldierDetailsModal
          soldier={viewingSoldier}
          onClose={() => {
            setShowDetailsModal(false);
            setViewingSoldier(null);
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

// Soldier Details Modal Component
const SoldierDetailsModal = ({ soldier, onClose }) => {
  // חישוב סבב יציאה נוכחי (כל 21 יום)
  const calculateCurrentRound = () => {
    if (!soldier.home_round_date) return null;

    const homeRoundDate = new Date(soldier.home_round_date);
    const today = new Date();
    const diffTime = Math.abs(today - homeRoundDate);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const roundNumber = Math.floor(diffDays / 21);
    const daysIntoCurrentRound = diffDays % 21;
    const nextRoundDate = new Date(homeRoundDate);
    nextRoundDate.setDate(nextRoundDate.getDate() + ((roundNumber + 1) * 21));

    return {
      roundNumber: roundNumber + 1,
      daysIntoRound: daysIntoCurrentRound,
      nextRoundDate: nextRoundDate.toLocaleDateString('he-IL'),
      daysUntilNextRound: 21 - daysIntoCurrentRound
    };
  };

  const currentRound = calculateCurrentRound();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gradient-to-r from-military-600 to-military-700 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center gap-3">
            <Shield size={28} />
            <h2 className="text-2xl font-bold">{soldier.name}</h2>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-500 uppercase">תפקיד</label>
              <p className="font-medium text-gray-900">{soldier.role}</p>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-500 uppercase">כיתה</label>
              <p className="font-medium text-gray-900">{soldier.kita || 'אין כיתה'}</p>
            </div>
          </div>

          {/* IDs */}
          {(soldier.idf_id || soldier.personal_id) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              {soldier.idf_id && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">מספר אישי</label>
                  <p className="font-medium text-gray-900">{soldier.idf_id}</p>
                </div>
              )}
              {soldier.personal_id && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">תעודת זהות</label>
                  <p className="font-medium text-gray-900">{soldier.personal_id}</p>
                </div>
              )}
            </div>
          )}

          {/* Contact Info */}
          {(soldier.phone_number || soldier.address) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              {soldier.phone_number && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase flex items-center gap-1">
                    <Phone size={14} />
                    טלפון
                  </label>
                  <p className="font-medium text-gray-900">{soldier.phone_number}</p>
                </div>
              )}
              {soldier.address && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase flex items-center gap-1">
                    <MapPin size={14} />
                    כתובת
                  </label>
                  <p className="font-medium text-gray-900">{soldier.address}</p>
                </div>
              )}
            </div>
          )}

          {/* Emergency Contact */}
          {(soldier.emergency_contact_name || soldier.emergency_contact_number) && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3">איש קשר לחירום</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {soldier.emergency_contact_name && (
                  <div className="space-y-1">
                    <label className="text-xs text-gray-500 uppercase">שם</label>
                    <p className="font-medium text-gray-900">{soldier.emergency_contact_name}</p>
                  </div>
                )}
                {soldier.emergency_contact_number && (
                  <div className="space-y-1">
                    <label className="text-xs text-gray-500 uppercase">טלפון</label>
                    <p className="font-medium text-gray-900">{soldier.emergency_contact_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Military Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
            {soldier.pakal && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">פק״ל</label>
                <p className="font-medium text-gray-900">{soldier.pakal}</p>
              </div>
            )}
            {soldier.recruit_date && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">תאריך גיוס</label>
                <p className="font-medium text-gray-900">{new Date(soldier.recruit_date).toLocaleDateString('he-IL')}</p>
              </div>
            )}
            {soldier.birth_date && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">תאריך לידה</label>
                <p className="font-medium text-gray-900">{new Date(soldier.birth_date).toLocaleDateString('he-IL')}</p>
              </div>
            )}
          </div>

          {/* Home Round - סבב יציאה */}
          {currentRound && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Calendar size={20} className="text-military-600" />
                סבב יציאה נוכחי
              </h3>
              <div className="bg-military-50 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">סבב מספר:</span>
                  <span className="font-bold text-military-700">{currentRound.roundNumber}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">יום בסבב:</span>
                  <span className="font-bold text-military-700">{currentRound.daysIntoRound + 1} מתוך 21</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">ימים עד סבב הבא:</span>
                  <span className="font-bold text-military-700">{currentRound.daysUntilNextRound}</span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-military-200">
                  <span className="text-gray-700">תאריך סבב הבא:</span>
                  <span className="font-bold text-military-700">{currentRound.nextRoundDate}</span>
                </div>
              </div>
            </div>
          )}

          {/* Certifications */}
          {soldier.certifications && soldier.certifications.length > 0 && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Award size={20} className="text-military-600" />
                הסמכות
              </h3>
              <div className="flex flex-wrap gap-2">
                {soldier.certifications.map((cert, idx) => (
                  <span key={idx} className="badge badge-blue">
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Status */}
          <div className="pt-4 border-t">
            <h3 className="font-bold text-gray-900 mb-3">סטטוס</h3>
            <div className="flex flex-wrap gap-2">
              {soldier.has_hatashab && (
                <span className="badge badge-yellow">התש״ב</span>
              )}
              {soldier.is_platoon_commander && (
                <span className="badge badge-purple">מפקד כיתה</span>
              )}
              {!soldier.has_hatashab && !soldier.is_platoon_commander && (
                <span className="text-gray-500">אין סטטוס מיוחד</span>
              )}
            </div>
          </div>

          {/* Unavailable Dates */}
          {soldier.unavailable_dates && soldier.unavailable_dates.length > 0 && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3">תאריכי חופשה / אי זמינות</h3>
              <div className="space-y-2">
                {soldier.unavailable_dates.map((unavailable) => (
                  <div key={unavailable.id} className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">
                        {new Date(unavailable.date).toLocaleDateString('he-IL')}
                      </span>
                      {unavailable.reason && (
                        <span className="text-sm text-gray-600">{unavailable.reason}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-end rounded-b-xl border-t">
          <button onClick={onClose} className="btn-secondary">
            סגור
          </button>
        </div>
      </div>
    </div>
  );
};

export default Soldiers;
