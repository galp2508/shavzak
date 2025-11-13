import { useState } from 'react';
import api from '../services/api';
import { X, Calendar } from 'lucide-react';
import { toast } from 'react-toastify';

// Helper להצגת סטטוס
export const getStatusBadge = (soldier) => {
  // ריתוק מנצח סבב קו
  if (soldier.status && soldier.status.status_type === 'ריתוק') {
    return {
      text: 'ריתוק',
      className: 'bg-red-600 text-white',
      show: true
    };
  }

  // בסבב קו - אבל רק אם אין סטטוס אחר
  if (soldier.in_round && (!soldier.status || soldier.status.status_type === 'בבסיס')) {
    return {
      text: 'סבב קו',
      className: 'bg-green-600 text-white',
      show: true
    };
  }

  // סטטוסים אחרים
  if (soldier.status && soldier.status.status_type !== 'בבסיס') {
    const statusColors = {
      'בקשת יציאה': 'bg-blue-500 text-white',
      'גימלים': 'bg-yellow-500 text-white',
      'ריתוק': 'bg-red-600 text-white',
      'בסבב קו': 'bg-green-600 text-white'
    };

    return {
      text: soldier.status.status_type,
      className: statusColors[soldier.status.status_type] || 'bg-gray-500 text-white',
      show: true,
      returnDate: soldier.status.return_date
    };
  }

  return { text: '', className: '', show: false };
};

// קומפוננט Badge
export const SoldierStatusBadge = ({ soldier, onClick }) => {
  const badge = getStatusBadge(soldier);

  if (!badge.show) return null;

  return (
    <span
      onClick={onClick}
      className={`text-xs px-2 py-1 rounded-full cursor-pointer hover:opacity-80 transition-opacity ${badge.className}`}
      title={badge.returnDate ? `חזרה: ${new Date(badge.returnDate).toLocaleDateString('he-IL')}` : 'לחץ לשינוי סטטוס'}
    >
      {badge.text}
      {badge.returnDate && (
        <span className="mr-1">
          ({new Date(badge.returnDate).toLocaleDateString('he-IL', { day: 'numeric', month: 'numeric' })})
        </span>
      )}
    </span>
  );
};

// מודאל לשינוי סטטוס
export const StatusChangeModal = ({ soldier, onClose, onUpdate }) => {
  const [formData, setFormData] = useState({
    status_type: soldier.status?.status_type || 'בבסיס',
    return_date: soldier.status?.return_date || '',
    notes: soldier.status?.notes || ''
  });
  const [loading, setLoading] = useState(false);

  const statusTypes = [
    { value: 'בבסיס', label: 'בבסיס', needsReturn: false },
    { value: 'בקשת יציאה', label: 'בקשת יציאה', needsReturn: true },
    { value: 'גימלים', label: 'גימלים', needsReturn: true },
    { value: 'ריתוק', label: 'ריתוק', needsReturn: true },
    { value: 'בסבב קו', label: 'בסבב קו', needsReturn: false }
  ];

  const selectedType = statusTypes.find(t => t.value === formData.status_type);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // בדיקה שבוחרים תאריך חזרה כשצריך
    if (selectedType?.needsReturn && !formData.return_date) {
      toast.error('חובה להזין תאריך חזרה לבסיס');
      return;
    }

    setLoading(true);
    try {
      await api.put(`/soldiers/${soldier.id}/status`, {
        status_type: formData.status_type,
        return_date: formData.return_date || null,
        notes: formData.notes
      });
      toast.success('סטטוס עודכן בהצלחה');
      onUpdate();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בעדכון סטטוס');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
        <div className="bg-military-600 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
          <h2 className="text-xl font-bold">שינוי סטטוס - {soldier.name}</h2>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* אזהרה על סבב קו */}
          {soldier.in_round && (
            <div className="bg-green-50 border-l-4 border-green-500 p-3 text-sm">
              <p className="text-green-700 font-medium">
                ℹ️ החייל כרגע בסבב קו (17-4)
              </p>
              <p className="text-green-600 text-xs mt-1">
                אם תבחר "ריתוק", הריתוק ידרוס את הסבב והחייל יישאר בבסיס
              </p>
            </div>
          )}

          {/* סוג סטטוס */}
          <div>
            <label className="label">סטטוס *</label>
            <select
              value={formData.status_type}
              onChange={(e) => setFormData({ ...formData, status_type: e.target.value, return_date: '' })}
              className="input-field"
              required
            >
              {statusTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {/* תאריך חזרה (רק אם לא בבסיס ולא בסבב קו) */}
          {selectedType?.needsReturn && (
            <div>
              <label className="label flex items-center gap-2">
                <Calendar size={16} />
                תאריך חזרה לבסיס *
              </label>
              <input
                type="date"
                value={formData.return_date}
                onChange={(e) => setFormData({ ...formData, return_date: e.target.value })}
                className="input-field"
                required
                min={new Date().toISOString().split('T')[0]}
              />
              <p className="text-xs text-gray-500 mt-1">
                עד תאריך זה החייל יהיה לא זמין לשיבוצים
              </p>
            </div>
          )}

          {/* הערות */}
          <div>
            <label className="label">הערות (אופציונלי)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="input-field"
              rows="2"
              placeholder="הערות נוספות..."
            />
          </div>

          {/* כפתורים */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary"
            >
              {loading ? 'שומר...' : 'עדכן סטטוס'}
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

export default { SoldierStatusBadge, StatusChangeModal, getStatusBadge };
