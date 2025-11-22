import { useState } from 'react';
import api from '../../services/api';
import { toast } from 'react-toastify';
import { X } from 'lucide-react';
import ROLES from '../../constants/roles';

const SoldierEditModal = ({ soldier, mahlakaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: soldier?.name || '',
    idf_id: soldier?.idf_id || '',
    personal_id: soldier?.personal_id || '',
    role: soldier?.role || 'לוחם',
    mahlaka_id: soldier?.mahlaka_id || mahlakaId,
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
    has_hatashab: soldier?.has_hatashab || false,
    hatash_2_days: soldier?.hatash_2_days || '',
  });
  const [loading, setLoading] = useState(false);
  const [hatash2Enabled, setHatash2Enabled] = useState(!!soldier?.hatash_2_days);

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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
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
            <div className="space-y-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.has_hatashab}
                  onChange={(e) => setFormData({ ...formData, has_hatashab: e.target.checked })}
                  className="w-4 h-4 text-military-600"
                />
                <span className="text-gray-700">יש התש״ב</span>
              </label>

              {/* התש"ב 2 - ימים קבועים */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <label className="flex items-center gap-2 cursor-pointer mb-3">
                  <input
                    type="checkbox"
                    checked={hatash2Enabled}
                    onChange={(e) => {
                      setHatash2Enabled(e.target.checked);
                      if (!e.target.checked) {
                        setFormData({ ...formData, hatash_2_days: '' });
                      }
                    }}
                    className="w-4 h-4 text-military-600"
                  />
                  <span className="text-gray-700 font-medium">התש״ב 2 - ימים קבועים שהחייל לא זמין</span>
                </label>

                {hatash2Enabled && (
                  <div className="mr-6">
                    <p className="text-xs text-gray-600 mb-2">בחר ימים בשבוע שהחייל לא זמין באופן קבוע:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { label: 'ראשון', value: '0' },
                        { label: 'שני', value: '1' },
                        { label: 'שלישי', value: '2' },
                        { label: 'רביעי', value: '3' },
                        { label: 'חמישי', value: '4' },
                        { label: 'שישי', value: '5' },
                        { label: 'שבת', value: '6' }
                      ].map((day) => {
                        const daysArray = formData.hatash_2_days ? formData.hatash_2_days.split(',') : [];
                        const isChecked = daysArray.includes(day.value);

                        return (
                          <label key={day.value} className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                let newDays = [...daysArray];
                                if (e.target.checked) {
                                  newDays.push(day.value);
                                } else {
                                  newDays = newDays.filter(d => d !== day.value);
                                }
                                setFormData({ ...formData, hatash_2_days: newDays.sort().join(',') });
                              }}
                              className="w-4 h-4 text-military-600"
                            />
                            <span className="text-sm text-gray-700">{day.label}</span>
                          </label>
                        );
                      })}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      * ריתוק מבטל התש״ב 2 - אם החייל בריתוק, הוא נשאר בבסיס גם בימים אלה
                    </p>
                  </div>
                )}
              </div>
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

export default SoldierEditModal;
