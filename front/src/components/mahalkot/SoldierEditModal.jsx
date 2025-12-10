import { useState, useEffect } from 'react';
import api from '../../services/api';
import { toast } from 'react-toastify';
import { X, Save, User, Phone, MapPin, Calendar, Shield, Award } from 'lucide-react';

const SoldierEditModal = ({ soldier, mahlakaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    role: 'לוחם',
    kita: '',
    idf_id: '',
    personal_id: '',
    phone_number: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_number: '',
    pakal: '',
    has_hatashab: false,
    recruit_date: '',
    birth_date: '',
    home_round_date: '',
    certifications: []
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (soldier) {
      setFormData({
        name: soldier.name || '',
        role: soldier.role || 'לוחם',
        kita: soldier.kita || '',
        idf_id: soldier.idf_id || '',
        personal_id: soldier.personal_id || '',
        phone_number: soldier.phone_number || '',
        address: soldier.address || '',
        emergency_contact_name: soldier.emergency_contact_name || '',
        emergency_contact_number: soldier.emergency_contact_number || '',
        pakal: soldier.pakal || '',
        has_hatashab: soldier.has_hatashab || false,
        recruit_date: soldier.recruit_date || '',
        birth_date: soldier.birth_date || '',
        home_round_date: soldier.home_round_date || '',
        certifications: soldier.certifications ? soldier.certifications.map(c => c.name) : []
      });
    }
  }, [soldier]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const dataToSend = {
        ...formData,
        mahlaka_id: mahlakaId
      };

      if (soldier) {
        await api.put(`/soldiers/${soldier.id}`, dataToSend);
        toast.success('פרטי חייל עודכנו בהצלחה');
      } else {
        await api.post('/soldiers', dataToSend);
        toast.success('חייל נוסף בהצלחה');
      }
      onSave();
    } catch (error) {
      console.error('Error saving soldier:', error);
      toast.error(error.response?.data?.error || 'שגיאה בשמירת פרטי חייל');
    } finally {
      setLoading(false);
    }
  };

  const roles = ['לוחם', 'ממ', 'מכ', 'סמל', 'חופל', 'קשר', 'נהג', 'אחר'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <h2 className="text-xl font-bold text-gray-800">
            {soldier ? 'עריכת פרטי חייל' : 'הוספת חייל חדש'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">שם מלא</label>
              <div className="relative">
                <User className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="input-field pr-10 w-full"
                  placeholder="ישראל ישראלי"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תפקיד</label>
              <div className="relative">
                <Shield className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="input-field pr-10 w-full"
                >
                  {roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">מספר אישי</label>
              <input
                type="text"
                name="personal_id"
                value={formData.personal_id}
                onChange={handleChange}
                className="input-field w-full"
                dir="ltr"
                placeholder="1234567"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">כיתה</label>
              <input
                type="text"
                name="kita"
                value={formData.kita}
                onChange={handleChange}
                className="input-field w-full"
                placeholder="שם כיתה"
              />
            </div>
          </div>

          <hr />

          {/* Contact Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">טלפון</label>
              <div className="relative">
                <Phone className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="tel"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleChange}
                  className="input-field pr-10 w-full"
                  dir="ltr"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">כתובת</label>
              <div className="relative">
                <MapPin className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  className="input-field pr-10 w-full"
                />
              </div>
            </div>
          </div>

          <hr />

          {/* Dates */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תאריך גיוס</label>
              <input
                type="date"
                name="recruit_date"
                value={formData.recruit_date}
                onChange={handleChange}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תאריך לידה</label>
              <input
                type="date"
                name="birth_date"
                value={formData.birth_date}
                onChange={handleChange}
                className="input-field w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">תאריך סבב יציאה</label>
              <input
                type="date"
                name="home_round_date"
                value={formData.home_round_date}
                onChange={handleChange}
                className="input-field w-full"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              name="has_hatashab"
              id="has_hatashab"
              checked={formData.has_hatashab}
              onChange={handleChange}
              className="rounded text-military-600 focus:ring-military-500 h-4 w-4"
            />
            <label htmlFor="has_hatashab" className="text-sm font-medium text-gray-700">
              זכאי התש"ב (יציאות מיוחדות)
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={loading}
            >
              ביטול
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'שומר...' : 'שמור שינויים'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SoldierEditModal;
