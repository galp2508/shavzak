import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Plus, Trash2, X, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';

const Constraints = ({ onClose, onUpdate }) => {
  const { user } = useAuth();
  const [constraints, setConstraints] = useState([]);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [constraintsRes, mahalkotRes] = await Promise.all([
        api.get(`/plugot/${user.pluga_id}/constraints`),
        api.get(`/plugot/${user.pluga_id}/mahalkot`)
      ]);
      setConstraints(constraintsRes.data.constraints || []);
      setMahalkot(mahalkotRes.data.mahalkot || []);
    } catch (error) {
      toast.error('שגיאה בטעינת אילוצים');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את האילוץ?')) {
      return;
    }

    try {
      await api.delete(`/constraints/${id}`);
      toast.success('אילוץ נמחק בהצלחה');
      loadData();
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error('שגיאה במחיקת אילוץ');
    }
  };

  const getConstraintDescription = (constraint) => {
    const parts = [];

    // מחלקה
    if (constraint.mahlaka_name) {
      parts.push(constraint.mahlaka_name);
    } else {
      parts.push('כל הפלוגה');
    }

    // סוג אילוץ
    const types = {
      'cannot_assign': 'לא יכול להשתבץ',
      'max_assignments_per_day': 'מקסימום משימות ביום',
      'restricted_hours': 'הגבלת שעות'
    };
    parts.push(types[constraint.constraint_type] || constraint.constraint_type);

    // סוג משימה
    if (constraint.assignment_type) {
      parts.push(`(${constraint.assignment_type})`);
    }

    // ערך
    if (constraint.constraint_value) {
      parts.push(`- ${constraint.constraint_value}`);
    }

    return parts.join(' ');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gradient-to-r from-military-600 to-military-700 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center gap-3">
            <Shield size={28} />
            <h2 className="text-2xl font-bold">אילוצי שיבוץ</h2>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X size={24} />
          </button>
        </div>

        <div className="p-6">
          {/* Info Alert */}
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
            <div className="flex items-start gap-2">
              <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
              <div className="text-sm text-blue-700">
                <p className="font-medium mb-1">אילוצים משפיעים על השיבוץ האוטומטי</p>
                <p>כל שינוי באילוצים ימחק אוטומטית שיבוצים מושפעים כדי לאפשר בנייה מחדש</p>
              </div>
            </div>
          </div>

          {/* Add Button */}
          {(user.role === 'מפ' || user.role === 'ממ') && (
            <div className="mb-6">
              <button
                onClick={() => setShowModal(true)}
                className="btn-primary flex items-center gap-2"
              >
                <Plus size={20} />
                <span>הוסף אילוץ</span>
              </button>
            </div>
          )}

          {/* Constraints List */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner"></div>
            </div>
          ) : constraints.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">אין אילוצים מוגדרים</p>
            </div>
          ) : (
            <div className="space-y-3">
              {constraints.map((constraint) => (
                <div
                  key={constraint.id}
                  className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 mb-1">
                        {getConstraintDescription(constraint)}
                      </div>
                      {constraint.reason && (
                        <p className="text-sm text-gray-600 mb-2">{constraint.reason}</p>
                      )}
                      <div className="flex flex-wrap gap-2 text-xs">
                        {constraint.days_of_week && (
                          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                            ימים: {constraint.days_of_week}
                          </span>
                        )}
                        {constraint.start_date && (
                          <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                            מ-{new Date(constraint.start_date).toLocaleDateString('he-IL')}
                          </span>
                        )}
                        {constraint.end_date && (
                          <span className="bg-red-100 text-red-700 px-2 py-1 rounded">
                            עד-{new Date(constraint.end_date).toLocaleDateString('he-IL')}
                          </span>
                        )}
                      </div>
                    </div>
                    {(user.role === 'מפ' || user.role === 'ממ') && (
                      <button
                        onClick={() => handleDelete(constraint.id)}
                        className="text-red-600 hover:text-red-800 p-2"
                        title="מחק"
                      >
                        <Trash2 size={18} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-end rounded-b-xl border-t">
          <button onClick={onClose} className="btn-secondary">
            סגור
          </button>
        </div>
      </div>

      {/* Add Constraint Modal */}
      {showModal && (
        <ConstraintModal
          mahalkot={mahalkot}
          plugaId={user.pluga_id}
          onClose={() => setShowModal(false)}
          onSave={() => {
            setShowModal(false);
            loadData();
            if (onUpdate) onUpdate();
          }}
        />
      )}
    </div>
  );
};

// Constraint Modal Component
const ConstraintModal = ({ mahalkot, plugaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    mahlaka_id: '',
    constraint_type: 'cannot_assign',
    assignment_type: '',
    constraint_value: '',
    days_of_week: '',
    start_date: '',
    end_date: '',
    reason: ''
  });
  const [loading, setLoading] = useState(false);

  const constraintTypes = [
    { value: 'cannot_assign', label: 'לא יכול להשתבץ' },
    { value: 'max_assignments_per_day', label: 'מקסימום משימות ביום' },
    { value: 'restricted_hours', label: 'הגבלת שעות' }
  ];

  const assignmentTypes = [
    'סיור', 'שמירה', 'כוננות א', 'כוננות ב',
    'חמל', 'תורן מטבח', 'חפק גשש', 'שלז', 'קצין תורן'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // ניקוי ערכים ריקים
      const cleanData = {};
      Object.keys(formData).forEach(key => {
        if (formData[key] !== '' && formData[key] !== null) {
          cleanData[key] = formData[key];
        }
      });

      // המרת mahlaka_id למספר
      if (cleanData.mahlaka_id) {
        cleanData.mahlaka_id = parseInt(cleanData.mahlaka_id);
      }

      await api.post(`/plugot/${plugaId}/constraints`, cleanData);
      toast.success('אילוץ נוסף בהצלחה');
      onSave();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בהוספת אילוץ');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl sticky top-0 z-10">
          <h2 className="text-2xl font-bold">הוספת אילוץ חדש</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* מחלקה */}
          <div>
            <label className="label">מחלקה (אופציונלי - השאר ריק לכל הפלוגה)</label>
            <select
              value={formData.mahlaka_id}
              onChange={(e) => setFormData({ ...formData, mahlaka_id: e.target.value })}
              className="input-field"
            >
              <option value="">כל הפלוגה</option>
              {mahalkot.map(m => (
                <option key={m.id} value={m.id}>מחלקה {m.number}</option>
              ))}
            </select>
          </div>

          {/* סוג אילוץ */}
          <div>
            <label className="label">סוג אילוץ *</label>
            <select
              value={formData.constraint_type}
              onChange={(e) => setFormData({ ...formData, constraint_type: e.target.value })}
              className="input-field"
              required
            >
              {constraintTypes.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* סוג משימה */}
          <div>
            <label className="label">סוג משימה (אופציונלי - השאר ריק לכל סוגי המשימות)</label>
            <select
              value={formData.assignment_type}
              onChange={(e) => setFormData({ ...formData, assignment_type: e.target.value })}
              className="input-field"
            >
              <option value="">כל סוגי המשימות</option>
              {assignmentTypes.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* ערך אילוץ */}
          {formData.constraint_type !== 'cannot_assign' && (
            <div>
              <label className="label">
                {formData.constraint_type === 'max_assignments_per_day'
                  ? 'מספר מקסימלי *'
                  : 'טווח שעות (למשל: 22-06) *'}
              </label>
              <input
                type="text"
                value={formData.constraint_value}
                onChange={(e) => setFormData({ ...formData, constraint_value: e.target.value })}
                className="input-field"
                placeholder={formData.constraint_type === 'max_assignments_per_day' ? '3' : '22-06'}
                required
              />
            </div>
          )}

          {/* ימים בשבוע */}
          <div>
            <label className="label">ימים בשבוע (אופציונלי - למשל: 0,5,6 לראשון, שישי, שבת)</label>
            <input
              type="text"
              value={formData.days_of_week}
              onChange={(e) => setFormData({ ...formData, days_of_week: e.target.value })}
              className="input-field"
              placeholder="0,1,2,3,4,5,6"
            />
            <p className="text-xs text-gray-500 mt-1">
              0=ראשון, 1=שני, 2=שלישי, 3=רביעי, 4=חמישי, 5=שישי, 6=שבת
            </p>
          </div>

          {/* טווח תאריכים */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">תאריך התחלה (אופציונלי)</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">תאריך סיום (אופציונלי)</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="input-field"
              />
            </div>
          </div>

          {/* סיבה */}
          <div>
            <label className="label">סיבה / הערה (אופציונלי)</label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              className="input-field"
              rows="3"
              placeholder="למשל: מחלקה בהכשרה, אזור סגור, וכו'"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary"
            >
              {loading ? 'שומר...' : 'הוסף אילוץ'}
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

export default Constraints;
