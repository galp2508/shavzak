import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  UserPlus, Search, Edit, Trash2, X, Plus,
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
    idf_id: soldier?.idf_id || '',
    personal_id: soldier?.personal_id || '',
    role: soldier?.role || 'לוחם',
    mahlaka_id: soldier?.mahlaka_id || mahalkot[0]?.id || '',
    kita: soldier?.kita || '',
    sex: soldier?.sex || '',
    phone_number: soldier?.phone_number || '',
    address: soldier?.address || '',
    emergency_contact_name: soldier?.emergency_contact_name || '',
    emergency_contact_number: soldier?.emergency_contact_number || '',
    pakal: soldier?.pakal || '',
    recruit_date: soldier?.recruit_date || '',
    birth_date: soldier?.birth_date || '',
    home_round_date: soldier?.home_round_date || '',
    is_platoon_commander: soldier?.is_platoon_commander || false,
    has_hatashab: soldier?.has_hatashab || false,
  });
  const [loading, setLoading] = useState(false);
  const [unavailableDates, setUnavailableDates] = useState(soldier?.unavailable_dates || []);
  const [newUnavailableDate, setNewUnavailableDate] = useState({ date: '', reason: '' });

  const handleAddUnavailableDate = async () => {
    if (!newUnavailableDate.date) {
      toast.error('יש להזין תאריך');
      return;
    }

    if (!soldier?.id) {
      // אם זה חייל חדש, נוסיף לרשימה המקומית
      setUnavailableDates([...unavailableDates, { ...newUnavailableDate, id: Date.now() }]);
      setNewUnavailableDate({ date: '', reason: '' });
      toast.success('תאריך נוסף');
      return;
    }

    try {
      const response = await api.post(`/soldiers/${soldier.id}/unavailable`, newUnavailableDate);
      setUnavailableDates([...unavailableDates, response.data.unavailable_date]);
      setNewUnavailableDate({ date: '', reason: '' });
      toast.success('תאריך נוסף בהצלחה');
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בהוספת תאריך');
    }
  };

  const handleDeleteUnavailableDate = async (unavailableId) => {
    if (!soldier?.id) {
      // אם זה חייל חדש, נמחק מהרשימה המקומית
      setUnavailableDates(unavailableDates.filter(u => u.id !== unavailableId));
      return;
    }

    try {
      await api.delete(`/unavailable/${unavailableId}`);
      setUnavailableDates(unavailableDates.filter(u => u.id !== unavailableId));
      toast.success('תאריך נמחק בהצלחה');
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת תאריך');
    }
  };

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
          {/* פרטים בסיסיים */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">פרטים בסיסיים</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                <label className="label">מין</label>
                <select
                  value={formData.sex}
                  onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
                  className="input-field"
                >
                  <option value="">בחר...</option>
                  <option value="זכר">זכר</option>
                  <option value="נקבה">נקבה</option>
                </select>
              </div>
            </div>
          </div>

          {/* מספרי זיהוי */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">מספרי זיהוי</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">מספר אישי (מ.א)</label>
                <input
                  type="text"
                  value={formData.idf_id}
                  onChange={(e) => setFormData({ ...formData, idf_id: e.target.value })}
                  className="input-field"
                  placeholder="1234567"
                />
              </div>

              <div>
                <label className="label">תעודת זהות</label>
                <input
                  type="text"
                  value={formData.personal_id}
                  onChange={(e) => setFormData({ ...formData, personal_id: e.target.value })}
                  className="input-field"
                  placeholder="123456789"
                />
              </div>
            </div>
          </div>

          {/* פרטי קשר */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">פרטי קשר</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div>
                <label className="label">כתובת</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input-field"
                  placeholder="רחוב, עיר"
                />
              </div>
            </div>
          </div>

          {/* איש קשר לחירום */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">איש קשר לחירום</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">שם איש קשר</label>
                <input
                  type="text"
                  value={formData.emergency_contact_name}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                  className="input-field"
                  placeholder="שם מלא"
                />
              </div>

              <div>
                <label className="label">טלפון איש קשר</label>
                <input
                  type="tel"
                  value={formData.emergency_contact_number}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_number: e.target.value })}
                  className="input-field"
                  placeholder="050-1234567"
                />
              </div>
            </div>
          </div>

          {/* מידע צבאי */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">מידע צבאי</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">פק״ל</label>
                <input
                  type="text"
                  value={formData.pakal}
                  onChange={(e) => setFormData({ ...formData, pakal: e.target.value })}
                  className="input-field"
                  placeholder="07"
                />
              </div>

              <div>
                <label className="label">תאריך גיוס</label>
                <input
                  type="date"
                  value={formData.recruit_date}
                  onChange={(e) => setFormData({ ...formData, recruit_date: e.target.value })}
                  className="input-field"
                />
              </div>

              <div>
                <label className="label">תאריך לידה</label>
                <input
                  type="date"
                  value={formData.birth_date}
                  onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                  className="input-field"
                />
              </div>

              <div>
                <label className="label">תאריך סבב יציאה</label>
                <input
                  type="date"
                  value={formData.home_round_date}
                  onChange={(e) => setFormData({ ...formData, home_round_date: e.target.value })}
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* סטטוסים */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b">סטטוסים</h3>
            <div className="space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_platoon_commander}
                  onChange={(e) => setFormData({ ...formData, is_platoon_commander: e.target.checked })}
                  className="w-4 h-4 text-military-600"
                />
                <span className="text-gray-700">מפקד כיתה</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_hatashab}
                  onChange={(e) => setFormData({ ...formData, has_hatashab: e.target.checked })}
                  className="w-4 h-4 text-military-600"
                />
                <span className="text-gray-700">יש התש 2</span>
              </label>
            </div>
          </div>

          {/* תאריכי אי זמינות */}
          <div>
            <h3 className="font-bold text-gray-900 mb-3 pb-2 border-b flex items-center gap-2">
              <Calendar size={20} className="text-military-600" />
              תאריכי אי זמינות / חופשה
            </h3>

            {/* תאריכים קיימים */}
            {unavailableDates.length > 0 && (
              <div className="space-y-2 mb-4">
                {unavailableDates.map((unavailable) => (
                  <div
                    key={unavailable.id}
                    className="flex items-center justify-between bg-red-50 border border-red-200 rounded-lg p-3"
                  >
                    <div>
                      <div className="font-medium text-gray-900">
                        {new Date(unavailable.date).toLocaleDateString('he-IL')}
                      </div>
                      {unavailable.reason && (
                        <div className="text-sm text-gray-600">{unavailable.reason}</div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteUnavailableDate(unavailable.id)}
                      className="text-red-600 hover:text-red-800"
                      title="מחק"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* הוספת תאריך חדש */}
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="label">תאריך</label>
                  <input
                    type="date"
                    value={newUnavailableDate.date}
                    onChange={(e) => setNewUnavailableDate({ ...newUnavailableDate, date: e.target.value })}
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="label">סיבה (אופציונלי)</label>
                  <input
                    type="text"
                    value={newUnavailableDate.reason}
                    onChange={(e) => setNewUnavailableDate({ ...newUnavailableDate, reason: e.target.value })}
                    className="input-field"
                    placeholder="חופשה, פטור, מחלה..."
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleAddUnavailableDate}
                className="btn-secondary flex items-center gap-2 w-full justify-center"
              >
                <Plus size={18} />
                <span>הוסף תאריך</span>
              </button>
            </div>
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
    homeRoundDate.setHours(0, 0, 0, 0); // אפס את השעות
    const today = new Date();
    today.setHours(0, 0, 0, 0); // אפס את השעות

    // חישוב ההפרש בימים (יכול להיות חיובי או שלילי)
    const diffTime = today - homeRoundDate;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    // חישוב מספר הסבב הנוכחי
    const roundNumber = Math.floor(diffDays / 21);
    const daysIntoCurrentRound = diffDays % 21;

    // חישוב התאריך של הסבב הבא (חייב להיות בעתיד)
    const nextRoundDate = new Date(homeRoundDate);
    nextRoundDate.setDate(nextRoundDate.getDate() + ((roundNumber + 1) * 21));

    // אם התאריך הבא עדיין בעבר (או היום), להוסיף עוד 21 יום
    while (nextRoundDate <= today) {
      nextRoundDate.setDate(nextRoundDate.getDate() + 21);
    }

    // חישוב כמה ימים נשארו עד הסבב הבא
    const daysUntilNext = Math.ceil((nextRoundDate - today) / (1000 * 60 * 60 * 24));

    return {
      roundNumber: roundNumber + 1,
      daysIntoRound: daysIntoCurrentRound >= 0 ? daysIntoCurrentRound : 0,
      nextRoundDate: nextRoundDate.toLocaleDateString('he-IL'),
      daysUntilNextRound: daysUntilNext
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
                <span className="badge badge-yellow">התש 2</span>
              )}
              {!soldier.has_hatashab && (
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
