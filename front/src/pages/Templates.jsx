import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { FileText, Plus, Clock, Edit, Trash2, X, Copy } from 'lucide-react';
import { toast } from 'react-toastify';

const Templates = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/assignment-templates`);
      setTemplates(response.data.templates);
    } catch (error) {
      toast.error('שגיאה בטעינת תבניות');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את התבנית?')) {
      return;
    }

    try {
      await api.delete(`/assignment-templates/${id}`);
      toast.success('התבנית נמחקה בהצלחה');
      loadTemplates();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת תבנית');
    }
  };

  const handleDuplicate = async (id) => {
    try {
      await api.post(`/assignment-templates/${id}/duplicate`);
      toast.success('התבנית שוכפלה בהצלחה');
      loadTemplates();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בשכפול תבנית');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">תבניות משימות</h1>
          <p className="text-gray-600 mt-1">{templates.length} תבניות</p>
        </div>
        {user.role === 'מפ' && (
          <button
            onClick={() => {
              setEditingTemplate(null);
              setShowModal(true);
            }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={20} />
            <span>תבנית חדשה</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="bg-military-100 p-3 rounded-lg">
                  <FileText className="w-6 h-6 text-military-600" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">{template.name}</h3>
                  <p className="text-sm text-gray-600">{template.assignment_type}</p>
                </div>
              </div>
              {user.role === 'מפ' && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDuplicate(template.id)}
                    className="text-green-600 hover:text-green-800"
                    title="שכפל תבנית"
                  >
                    <Copy size={18} />
                  </button>
                  <button
                    onClick={() => {
                      setEditingTemplate(template);
                      setShowModal(true);
                    }}
                    className="text-blue-600 hover:text-blue-800"
                    title="ערוך"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="text-red-600 hover:text-red-800"
                    title="מחק"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              )}
            </div>

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Clock size={16} />
                <span>{template.length_in_hours} שעות × {template.times_per_day} פעמים ביום</span>
              </div>
              <div className="flex gap-2 flex-wrap mt-3">
                {template.commanders_needed > 0 && (
                  <span className="badge badge-purple">{template.commanders_needed} מפקדים</span>
                )}
                {template.drivers_needed > 0 && (
                  <span className="badge badge-blue">{template.drivers_needed} נהגים</span>
                )}
                {template.soldiers_needed > 0 && (
                  <span className="badge badge-green">{template.soldiers_needed} לוחמים</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">אין תבניות משימות במערכת</p>
        </div>
      )}

      {/* Template Modal */}
      {showModal && (
        <TemplateModal
          template={editingTemplate}
          plugaId={user.pluga_id}
          onClose={() => {
            setShowModal(false);
            setEditingTemplate(null);
          }}
          onSave={() => {
            setShowModal(false);
            setEditingTemplate(null);
            loadTemplates();
          }}
        />
      )}
    </div>
  );
};

// Template Modal Component
const TemplateModal = ({ template, plugaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    assignment_type: template?.assignment_type || 'שמירה',
    length_in_hours: template?.length_in_hours || 8,
    times_per_day: template?.times_per_day || 1,
    commanders_needed: template?.commanders_needed || 0,
    drivers_needed: template?.drivers_needed || 0,
    soldiers_needed: template?.soldiers_needed || 1,
    same_mahlaka_required: template?.same_mahlaka_required || false,
    requires_certification: template?.requires_certification || '',
    requires_senior_commander: template?.requires_senior_commander || false,
  });
  const [loading, setLoading] = useState(false);

  const assignmentTypes = ['שמירה', 'סיור', 'כוננות א', 'כוננות ב', 'חמל', 'תורן מטבח', 'חפק גשש', 'שלז', 'קצין תורן'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (template) {
        await api.put(`/assignment-templates/${template.id}`, formData);
        toast.success('התבנית עודכנה בהצלחה');
      } else {
        await api.post(`/plugot/${plugaId}/assignment-templates`, formData);
        toast.success('התבנית נוספה בהצלחה');
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
            {template ? 'עריכת תבנית' : 'תבנית משימה חדשה'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">שם התבנית *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="label">סוג משימה *</label>
              <select
                value={formData.assignment_type}
                onChange={(e) => setFormData({ ...formData, assignment_type: e.target.value })}
                className="input-field"
                required
              >
                {assignmentTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">אורך במשמרת (שעות) *</label>
              <input
                type="number"
                min="1"
                max="24"
                value={formData.length_in_hours}
                onChange={(e) => setFormData({ ...formData, length_in_hours: parseInt(e.target.value) })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="label">פעמים ביום *</label>
              <input
                type="number"
                min="1"
                max="10"
                value={formData.times_per_day}
                onChange={(e) => setFormData({ ...formData, times_per_day: parseInt(e.target.value) })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="label">מספר מפקדים נדרשים</label>
              <input
                type="number"
                min="0"
                value={formData.commanders_needed}
                onChange={(e) => setFormData({ ...formData, commanders_needed: parseInt(e.target.value) })}
                className="input-field"
              />
            </div>

            <div>
              <label className="label">מספר נהגים נדרשים</label>
              <input
                type="number"
                min="0"
                value={formData.drivers_needed}
                onChange={(e) => setFormData({ ...formData, drivers_needed: parseInt(e.target.value) })}
                className="input-field"
              />
            </div>

            <div>
              <label className="label">מספר חיילים נדרשים</label>
              <input
                type="number"
                min="0"
                value={formData.soldiers_needed}
                onChange={(e) => setFormData({ ...formData, soldiers_needed: parseInt(e.target.value) })}
                className="input-field"
              />
            </div>

            <div>
              <label className="label">הסמכה נדרשת</label>
              <input
                type="text"
                value={formData.requires_certification}
                onChange={(e) => setFormData({ ...formData, requires_certification: e.target.value })}
                className="input-field"
                placeholder="למשל: חמל"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.same_mahlaka_required}
                onChange={(e) => setFormData({ ...formData, same_mahlaka_required: e.target.checked })}
                className="w-4 h-4 text-military-600"
              />
              <span className="text-gray-700">דורש חיילים מאותה מחלקה</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.requires_senior_commander}
                onChange={(e) => setFormData({ ...formData, requires_senior_commander: e.target.checked })}
                className="w-4 h-4 text-military-600"
              />
              <span className="text-gray-700">דורש מפקד בכיר</span>
            </label>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary"
            >
              {loading ? 'שומר...' : template ? 'עדכן' : 'הוסף'}
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

export default Templates;
