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
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('שגיאה בטעינת תבניות');
      setTemplates([]); // Ensure it's an array on error
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
      // שדר אירוע שתבנית השתנתה
      window.dispatchEvent(new Event('templateChanged'));
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת תבנית');
    }
  };

  const handleDuplicate = async (id) => {
    try {
      await api.post(`/assignment-templates/${id}/duplicate`);
      toast.success('התבנית שוכפלה בהצלחה');
      loadTemplates();
      // שדר אירוע שתבנית השתנתה
      window.dispatchEvent(new Event('templateChanged'));
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
              {template.duration_days > 0 ? (
                <div className="flex items-center gap-2">
                  <Clock size={16} />
                  <span>משך: {template.duration_days} ימים (כל {template.recurrence_interval} ימים)</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Clock size={16} />
                  <span>{template.length_in_hours} שעות × {Math.floor(24 / template.length_in_hours)} פעמים ביום</span>
                </div>
              )}
              {template.start_hour !== null && template.start_hour !== undefined && !template.duration_days && (
                <div className="text-xs text-gray-500">
                  התחלה: {String(template.start_hour).padStart(2, '0')}:00
                </div>
              )}
              <div className="flex gap-2 flex-wrap mt-3">
                {template.is_base_task && (
                  <span className="badge bg-gray-100 text-gray-700 border border-gray-300">משימת בסיס</span>
                )}
                {template.can_split && (
                  <span className="badge bg-indigo-100 text-indigo-700 border border-indigo-300">ניתן לפיצול</span>
                )}
                {template.is_skippable && (
                  <span className="badge bg-yellow-100 text-yellow-700 border border-yellow-300">ניתן לוויתור</span>
                )}
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
    start_hour: template?.start_hour || '',
    commanders_needed: template?.commanders_needed || 0,
    drivers_needed: template?.drivers_needed || 0,
    soldiers_needed: template?.soldiers_needed || 1,
    same_mahlaka_required: template?.same_mahlaka_required || false,
    requires_certification: template?.requires_certification || '',
    requires_senior_commander: template?.requires_senior_commander || false,
    reuse_soldiers_for_standby: template?.reuse_soldiers_for_standby || false,
    duration_days: template?.duration_days || 0,
    recurrence_interval: template?.recurrence_interval || 1,
    start_day_offset: template?.start_day_offset || 0,
    is_base_task: template?.is_base_task || false,
    can_split: template?.can_split || false,
    is_skippable: template?.is_skippable || false,
    requires_special_mahlaka: template?.requires_special_mahlaka || false,
  });
  const [loading, setLoading] = useState(false);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [isMultiDay, setIsMultiDay] = useState(template?.duration_days > 0);

  // טען את רשימת התפקידים/הסמכות הזמינים
  useEffect(() => {
    const loadAvailableRoles = async () => {
      try {
        const response = await api.get('/available-roles-certifications');
        setAvailableRoles(response.data.roles_certifications || []);
      } catch (error) {
        console.error('Error loading available roles:', error);
        // אם יש שגיאה, השתמש ברשימה ברירת מחדל
        setAvailableRoles(['נהג', 'חמל', 'קצין תורן']);
      }
    };
    loadAvailableRoles();
  }, []);

  // תבניות מוכנות מראש
  const presetTemplates = {
    'שמירה': {
      length_in_hours: 4,
      commanders_needed: 0,
      drivers_needed: 0,
      soldiers_needed: 1,
      same_mahlaka_required: false,
      requires_certification: '',
    },
    'סיור': {
      length_in_hours: 8,
      commanders_needed: 1,
      drivers_needed: 1,
      soldiers_needed: 2,
      same_mahlaka_required: true,  // מפקד ולוחמים מאותה מחלקה, נהג לא
      requires_certification: '',
    },
    'חמל': {
      length_in_hours: 12,
      commanders_needed: 0,
      drivers_needed: 0,
      soldiers_needed: 1,
      same_mahlaka_required: false,
      requires_certification: 'חמל',
    },
  };

  // פונקציה לטעינת תבנית מוכנה
  const loadPresetTemplate = (assignmentType) => {
    const preset = presetTemplates[assignmentType];
    if (preset && !template) {  // טען רק אם זו תבנית חדשה (לא עריכה)
      setFormData({
        ...formData,
        assignment_type: assignmentType,
        ...preset,
      });
    } else {
      setFormData({
        ...formData,
        assignment_type: assignmentType,
      });
    }
  };

  // חישוב אוטומטי של פעמים ביום
  const timesPerDay = formData.length_in_hours > 0 ? Math.floor(24 / formData.length_in_hours) : 1;

  const assignmentTypes = ['שמירה', 'סיור', 'כוננות א', 'כוננות ב', 'חמל', 'תורן מטבח', 'חפק גשש', 'שלז', 'קצין תורן'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // הוסף חישוב אוטומטי של times_per_day
      const dataToSend = {
        ...formData,
        times_per_day: isMultiDay ? 1 : timesPerDay,
        length_in_hours: isMultiDay ? formData.duration_days * 24 : formData.length_in_hours,
        duration_days: isMultiDay ? formData.duration_days : 0,
        start_hour: formData.start_hour ? parseInt(formData.start_hour) : null
      };

      if (template) {
        await api.put(`/assignment-templates/${template.id}`, dataToSend);
        toast.success('התבנית עודכנה בהצלחה');
      } else {
        await api.post(`/plugot/${plugaId}/assignment-templates`, dataToSend);
        toast.success('התבנית נוספה בהצלחה');
      }
      // שדר אירוע שתבנית השתנתה
      window.dispatchEvent(new Event('templateChanged'));
      onSave();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בשמירה');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex-none bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <h2 className="text-2xl font-bold">
            {template ? 'עריכת תבנית' : 'תבנית משימה חדשה'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form id="templateForm" onSubmit={handleSubmit} className="space-y-6">
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
                  onChange={(e) => loadPresetTemplate(e.target.value)}
                  className="input-field"
                  required
                >
                  {assignmentTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                {presetTemplates[formData.assignment_type] && !template && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ תבנית מומלצת נטענה אוטומטית
                  </p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="flex items-center gap-2 cursor-pointer mb-4">
                  <input
                    type="checkbox"
                    checked={isMultiDay}
                    onChange={(e) => {
                      setIsMultiDay(e.target.checked);
                      if (e.target.checked) {
                        setFormData(prev => ({ ...prev, duration_days: 1 }));
                      } else {
                        setFormData(prev => ({ ...prev, duration_days: 0 }));
                      }
                    }}
                    className="w-4 h-4 text-military-600"
                  />
                  <span className="font-bold text-gray-700">משימה רב-יומית (נמשכת יותר מיום אחד)</span>
                </label>
              </div>

              {!isMultiDay ? (
                <>
                  <div>
                    <label className="label">אורך במשמרת (שעות) *</label>
                    <input
                      type="number"
                      min="1"
                      max="24"
                      value={formData.length_in_hours}
                      onChange={(e) => setFormData({ ...formData, length_in_hours: parseInt(e.target.value) })}
                      className="input-field"
                      required={!isMultiDay}
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      תקרה {timesPerDay} {timesPerDay === 1 ? 'פעם' : 'פעמים'} ביום (24 / {formData.length_in_hours})
                    </p>
                  </div>

                  <div>
                    <label className="label">שעת התחלה (אופציונלי)</label>
                    <input
                      type="number"
                      min="0"
                      max="23"
                      value={formData.start_hour}
                      onChange={(e) => setFormData({ ...formData, start_hour: e.target.value })}
                      className="input-field"
                      placeholder="לדוגמה: 8"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      שעת התחלה של המשמרת הראשונה (0-23)
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="label">משך המשימה (ימים) *</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.duration_days}
                      onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) })}
                      className="input-field"
                      required={isMultiDay}
                    />
                  </div>

                  <div>
                    <label className="label">חזרה כל (ימים)</label>
                    <input
                      type="number"
                      min="1"
                      value={formData.recurrence_interval}
                      onChange={(e) => setFormData({ ...formData, recurrence_interval: parseInt(e.target.value) })}
                      className="input-field"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      כל כמה ימים המשימה חוזרת על עצמה (1 = רצוף)
                    </p>
                  </div>

                  <div>
                    <label className="label">התחלה ביום (Offset)</label>
                    <input
                      type="number"
                      min="0"
                      value={formData.start_day_offset}
                      onChange={(e) => setFormData({ ...formData, start_day_offset: parseInt(e.target.value) })}
                      className="input-field"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      התחלה ביום ה-X של השיבוץ (0 = יום ראשון)
                    </p>
                  </div>
                </>
              )}

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
                <label className="label">
                  הסמכה/תפקיד נדרש
                  <span className="text-xs text-gray-500 mr-2">(תפקיד נוסף שחייל צריך בשביל המשימה)</span>
                </label>
                <select
                  value={formData.requires_certification}
                  onChange={(e) => setFormData({ ...formData, requires_certification: e.target.value })}
                  className="input-field"
                >
                  <option value="">ללא הסמכה נדרשת</option>
                  {availableRoles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
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
                  checked={formData.requires_special_mahlaka}
                  onChange={(e) => setFormData({ ...formData, requires_special_mahlaka: e.target.checked })}
                  className="w-4 h-4 text-military-600"
                />
                <span className="text-gray-700">דורש מחלקה מיוחדת</span>
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

              {(formData.assignment_type === 'כוננות א' || formData.assignment_type === 'כוננות ב') && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.reuse_soldiers_for_standby}
                    onChange={(e) => setFormData({ ...formData, reuse_soldiers_for_standby: e.target.checked })}
                    className="w-4 h-4 text-military-600"
                  />
                  <span className="text-gray-700">קח חיילים שסיימו משימה לכוננות</span>
                  <span className="text-xs text-gray-500">(המערכת תעדיף חיילים שסיימו משימה זמן קצר לפני הכוננות)</span>
                </label>
              )}

              <div className="border-t border-gray-200 pt-3 mt-3">
                <h4 className="text-sm font-bold text-gray-700 mb-2">הגדרות מתקדמות</h4>
                
                <label className="flex items-center gap-2 cursor-pointer mb-2">
                  <input
                    type="checkbox"
                    checked={formData.is_base_task}
                    onChange={(e) => setFormData({ ...formData, is_base_task: e.target.checked })}
                    className="w-4 h-4 text-green-600"
                  />
                  <div>
                    <span className="text-gray-700 font-medium">משימת בסיס (נחשבת כמנוחה)</span>
                    <p className="text-xs text-gray-500">משימה קלה שלא דורשת שעות מנוחה לפניה/אחריה ולא שוברת רצף מנוחה</p>
                  </div>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.can_split}
                    onChange={(e) => setFormData({ ...formData, can_split: e.target.checked })}
                    className="w-4 h-4 text-indigo-600"
                  />
                  <div>
                    <span className="text-gray-700 font-medium">ניתן לפיצול</span>
                    <p className="text-xs text-gray-500">המערכת רשאית לפצל את המשימה לשני חלקים (למשל: פתיחה וסגירה) במידת הצורך</p>
                  </div>
                </label>

                <label className="flex items-center gap-2 cursor-pointer mt-2">
                  <input
                    type="checkbox"
                    checked={formData.is_skippable}
                    onChange={(e) => setFormData({ ...formData, is_skippable: e.target.checked })}
                    className="w-4 h-4 text-yellow-600"
                  />
                  <div>
                    <span className="text-gray-700 font-medium">ניתן לוויתור (Optional)</span>
                    <p className="text-xs text-gray-500">במקרה של חוסר בכוח אדם, המערכת תציע לוותר על משימה זו</p>
                  </div>
                </label>
              </div>
            </div>
          </form>
        </div>

        {/* Footer - Fixed at bottom */}
        <div className="flex-none border-t border-gray-200 p-4 bg-gray-50 rounded-b-xl">
          <div className="flex gap-3">
            <button
              type="submit"
              form="templateForm"
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
        </div>
      </div>
    </div>
  );
};

export default Templates;
