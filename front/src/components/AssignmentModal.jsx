import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Users, Clock, Calendar, Save } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../services/api';

const AssignmentModal = ({
  assignment = null, // null = יצירה חדשה, object = עריכה
  date, // תאריך המשימה (Date object)
  dayIndex, // אינדקס היום בשבצ"ק
  shavzakId,
  plugaId,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = useState({
    name: '',
    assignment_type: 'שמירה',
    day: dayIndex !== undefined && dayIndex !== null ? dayIndex : 0,
    start_hour: 8,
    length_in_hours: 2,
    assigned_mahlaka_id: null
  });

  const [availableSoldiers, setAvailableSoldiers] = useState([]);
  const [selectedSoldiers, setSelectedSoldiers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingSoldiers, setLoadingSoldiers] = useState(true);
  const [soldierAssignmentCounts, setSoldierAssignmentCounts] = useState({});
  const [mahalkot, setMahalkot] = useState([]);
  const [expandedMahalkot, setExpandedMahalkot] = useState({}); // For accordion

  const assignmentTypes = [
    'שמירה', 'סיור', 'כוננות א', 'כוננות ב',
    'חמל', 'תורן מטבח', 'חפק גשש', 'שלז', 'קצין תורן'
  ];

  const toggleMahlaka = (mahlakaId) => {
    setExpandedMahalkot(prev => ({
      ...prev,
      [mahlakaId]: !prev[mahlakaId]
    }));
  };

  useEffect(() => {
    loadAvailableSoldiers();

    // אם זו עריכה - טען את הנתונים הקיימים
    if (assignment) {
      setFormData({
        name: assignment.name || '',
        assignment_type: assignment.type || 'שמירה',
        day: assignment.day !== undefined && assignment.day !== null ? assignment.day : (dayIndex !== undefined && dayIndex !== null ? dayIndex : 0),
        start_hour: assignment.start_hour !== undefined && assignment.start_hour !== null ? assignment.start_hour : 8,
        length_in_hours: assignment.length_in_hours !== undefined && assignment.length_in_hours !== null ? assignment.length_in_hours : 2,
        assigned_mahlaka_id: assignment.assigned_mahlaka_id || null
      });

      // טען את החיילים המשובצים
      if (assignment.soldiers && assignment.soldiers.length > 0) {
        setSelectedSoldiers(assignment.soldiers.map(s => ({
          soldier_id: s.id,
          name: s.name,
          role: s.role_in_assignment || 'חייל',
          soldier_role: s.role
        })));
      }
    }
  }, [assignment]);

  const loadAvailableSoldiers = async () => {
    setLoadingSoldiers(true);
    try {
      const response = await api.get(`/plugot/${plugaId}/mahalkot`);
      const mahalkotData = response.data.mahalkot || [];
      setMahalkot(mahalkotData);

      // איסוף כל החיילים מכל המחלקות
      const allSoldiersPromises = mahalkotData.map(m =>
        api.get(`/mahalkot/${m.id}/soldiers`)
          .then(res => {
            const soldiers = res.data.soldiers || [];
            // הוסף מידע על מחלקה לכל חייל
            return soldiers.map(s => ({
              ...s,
              mahlaka_id: m.id,
              mahlaka_number: m.number,
              mahlaka_color: m.color
            }));
          })
          .catch(() => [])
      );

      const soldiersArrays = await Promise.all(allSoldiersPromises);
      const allSoldiers = soldiersArrays.flat();

      setAvailableSoldiers(allSoldiers);

      // טען את כל המשימות של היום הנוכחי כדי לספור כמה פעמים כל חייל משובץ
      if (date && shavzakId) {
        try {
          const dateStr = date.toISOString().split('T')[0];
          const scheduleResponse = await api.get(`/plugot/${plugaId}/live-schedule?date=${dateStr}`);

          const assignments = scheduleResponse.data?.assignments || [];
          const counts = {};

          // ספור כמה פעמים כל חייל משובץ ביום הזה
          assignments.forEach(assign => {
            // דלג על המשימה הנוכחית שאנחנו עורכים
            if (assignment && assign.id === assignment.id) return;

            const soldiers = assign.soldiers || [];
            soldiers.forEach(soldier => {
              counts[soldier.id] = (counts[soldier.id] || 0) + 1;
            });
          });

          setSoldierAssignmentCounts(counts);
        } catch (error) {
          console.error('Error loading assignment counts:', error);
        }
      }
    } catch (error) {
      console.error('Error loading soldiers:', error);
      toast.error('שגיאה בטעינת חיילים');
    } finally {
      setLoadingSoldiers(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'day' || name === 'start_hour' || name === 'length_in_hours'
        ? parseInt(value)
        : value
    }));
  };

  const addSoldier = (soldier, role = 'חייל') => {
    if (selectedSoldiers.find(s => s.soldier_id === soldier.id)) {
      toast.warning('חייל זה כבר משובץ');
      return;
    }

    setSelectedSoldiers(prev => [...prev, {
      soldier_id: soldier.id,
      name: soldier.name,
      role: role,
      soldier_role: soldier.role
    }]);
  };

  const removeSoldier = (soldierId) => {
    setSelectedSoldiers(prev => prev.filter(s => s.soldier_id !== soldierId));
  };

  const updateSoldierRole = (soldierId, newRole) => {
    setSelectedSoldiers(prev => prev.map(s =>
      s.soldier_id === soldierId ? { ...s, role: newRole } : s
    ));
  };

  const handleSoldierToggle = (soldier, defaultRole = 'חייל') => {
    const isSelected = selectedSoldiers.some(s => s.soldier_id === soldier.id);
    if (isSelected) {
      removeSoldier(soldier.id);
    } else {
      addSoldier(soldier, defaultRole);
    }
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error('יש להזין שם למשימה');
      return;
    }

    setLoading(true);
    try {
      if (assignment) {
        // עדכון משימה קיימת
        await api.put(`/assignments/${assignment.id}`, formData);

        // עדכון החיילים
        await api.put(`/assignments/${assignment.id}/soldiers`, {
          soldiers: selectedSoldiers.map(s => ({
            soldier_id: s.soldier_id,
            role: s.role
          }))
        });

        toast.success('המשימה עודכנה בהצלחה');
      } else {
        // יצירת משימה חדשה
        await api.post(`/shavzakim/${shavzakId}/assignments`, {
          ...formData,
          soldiers: selectedSoldiers.map(s => ({
            soldier_id: s.soldier_id,
            role: s.role
          }))
        });

        toast.success('המשימה נוצרה בהצלחה');
      }

      onSave();
      onClose();
    } catch (error) {
      console.error('Error saving assignment:', error);
      toast.error(error.response?.data?.error || 'שגיאה בשמירת המשימה');
    } finally {
      setLoading(false);
    }
  };

  const getSortedSoldiers = (soldiers) => {
    // Sort by assignment count (ascending)
    return [...soldiers].sort((a, b) => {
      const countA = soldierAssignmentCounts[a.id] || 0;
      const countB = soldierAssignmentCounts[b.id] || 0;
      return countA - countB;
    });
  };

  const renderSoldierList = (categoryTitle, filterFn, defaultRole = 'חייל') => {
    const filteredSoldiers = availableSoldiers.filter(filterFn);
    const sortedSoldiers = getSortedSoldiers(filteredSoldiers);
    
    // Group by Mahlaka
    const soldiersByMahlaka = {};
    mahalkot.forEach(m => {
        soldiersByMahlaka[m.id] = {
            ...m,
            soldiers: sortedSoldiers.filter(s => s.mahlaka_id === m.id)
        };
    });

    return (
      <div className="mb-4">
        <h4 className="font-bold text-gray-700 mb-2 border-b pb-1">{categoryTitle}</h4>
        <div className="space-y-2">
          {mahalkot.map(mahlaka => {
            const group = soldiersByMahlaka[mahlaka.id];
            if (!group || group.soldiers.length === 0) return null;
            
            const isExpanded = expandedMahalkot[`${categoryTitle}-${mahlaka.id}`];
            
            return (
              <div key={mahlaka.id} className="border rounded-lg overflow-hidden">
                <button
                    type="button"
                    onClick={() => toggleMahlaka(`${categoryTitle}-${mahlaka.id}`)}
                    className="w-full flex items-center justify-between p-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: mahlaka.color }}></div>
                        <span className="font-medium text-sm">מחלקה {mahlaka.number}</span>
                        <span className="text-xs text-gray-500">({group.soldiers.length})</span>
                    </div>
                    <div className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                    </div>
                </button>
                
                {isExpanded && (
                    <div className="p-2 grid grid-cols-1 sm:grid-cols-2 gap-2 bg-white">
                        {group.soldiers.map(soldier => {
                            const isSelected = selectedSoldiers.some(s => s.soldier_id === soldier.id);
                            const count = soldierAssignmentCounts[soldier.id] || 0;
                            
                            return (
                                <div
                                    key={soldier.id}
                                    onClick={() => handleSoldierToggle(soldier, defaultRole)}
                                    className={`
                                        flex items-center justify-between p-2 rounded cursor-pointer border transition-all
                                        ${isSelected 
                                            ? 'bg-military-50 border-military-500 ring-1 ring-military-500' 
                                            : 'bg-white border-gray-200 hover:border-military-300 hover:bg-gray-50'}
                                    `}
                                >
                                    <div className="flex items-center gap-2">
                                        <div className={`w-2 h-2 rounded-full ${count === 0 ? 'bg-green-500' : count > 1 ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
                                        <span className="text-sm font-medium">{soldier.name}</span>
                                    </div>
                                    <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">
                                        {count} משימות
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-military-600 to-military-700 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-8 h-8" />
            <div>
              <h2 className="text-2xl font-bold">
                {assignment ? 'עריכת משימה' : 'משימה חדשה'}
              </h2>
              <p className="text-military-100">
                {date && date.toLocaleDateString('he-IL')}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* פרטי המשימה */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              פרטי המשימה
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* שם המשימה */}
              <div>
                <label className="label">שם המשימה</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="למשל: שמירה 1"
                />
              </div>

              {/* סוג משימה */}
              <div>
                <label className="label">סוג משימה</label>
                <select
                  name="assignment_type"
                  value={formData.assignment_type}
                  onChange={handleInputChange}
                  className="input-field"
                >
                  {assignmentTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* שעת התחלה */}
              <div>
                <label className="label">שעת התחלה</label>
                <input
                  type="number"
                  name="start_hour"
                  value={formData.start_hour}
                  onChange={handleInputChange}
                  min="0"
                  max="23"
                  className="input-field"
                />
              </div>

              {/* אורך המשימה */}
              <div>
                <label className="label">אורך בשעות</label>
                <input
                  type="number"
                  name="length_in_hours"
                  value={formData.length_in_hours}
                  onChange={handleInputChange}
                  min="1"
                  max="24"
                  className="input-field"
                />
              </div>
            </div>
          </div>

          {/* חיילים משובצים */}
          <div className="mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
              <Users className="w-5 h-5" />
              חיילים משובצים ({selectedSoldiers.length})
            </h3>

            {selectedSoldiers.length === 0 ? (
              <div className="bg-yellow-50 border-2 border-dashed border-yellow-300 rounded-xl p-6 text-center">
                <p className="text-yellow-700 font-medium">לא נבחרו חיילים</p>
                <p className="text-sm text-yellow-600 mt-1">בחר חיילים מהרשימה למטה</p>
              </div>
            ) : (
              <div className="space-y-2">
                {selectedSoldiers.map(soldier => (
                  <div
                    key={soldier.soldier_id}
                    className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-xl flex items-center justify-between shadow-sm hover:shadow-md transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="bg-military-600 text-white p-2 rounded-lg">
                        <Users className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{soldier.name}</div>
                        <div className="text-sm text-gray-600">{soldier.soldier_role}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <select
                        value={soldier.role}
                        onChange={(e) => updateSoldierRole(soldier.soldier_id, e.target.value)}
                        className="input-field py-1 text-sm"
                      >
                        <option value="מפקד">מפקד</option>
                        <option value="נהג">נהג</option>
                        <option value="חייל">חייל</option>
                      </select>

                      <button
                        onClick={() => removeSoldier(soldier.soldier_id)}
                        className="btn-danger p-2"
                        title="הסר חייל"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* חיילים זמינים */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2 mb-4">
              <Plus className="w-5 h-5" />
              הוסף חיילים
            </h3>

            {loadingSoldiers ? (
              <div className="flex items-center justify-center py-8">
                <div className="spinner"></div>
              </div>
            ) : (
              <div className="space-y-6 max-h-96 overflow-y-auto pr-2">
                {/* Commanders */}
                {renderSoldierList('מפקדים', (s) => {
                    const isCommander = ['ממ', 'מכ', 'סמל'].includes(s.role) || 
                                      (s.certifications && s.certifications.some(c => c.name === 'מפקד'));
                    return isCommander;
                }, 'מפקד')}

                {/* Drivers */}
                {renderSoldierList('נהגים', (s) => {
                    const isDriver = s.role.includes('נהג') || 
                                   (s.certifications && s.certifications.some(c => c.name === 'נהג'));
                    // Exclude if already shown as commander (unless they are primarily driver?)
                    // Let's keep them in both if they qualify, or prioritize commander?
                    // User said: "Commanders then Drivers then Soldiers"
                    // So if someone is both, they appear in Commanders.
                    const isCommander = ['ממ', 'מכ', 'סמל'].includes(s.role) || 
                                      (s.certifications && s.certifications.some(c => c.name === 'מפקד'));
                    return isDriver && !isCommander;
                }, 'נהג')}

                {/* Soldiers */}
                {renderSoldierList('חיילים', (s) => {
                    const isCommander = ['ממ', 'מכ', 'סמל'].includes(s.role) || 
                                      (s.certifications && s.certifications.some(c => c.name === 'מפקד'));
                    const isDriver = s.role.includes('נהג') || 
                                   (s.certifications && s.certifications.some(c => c.name === 'נהג'));
                    return !isCommander && !isDriver;
                }, 'חייל')}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-6 flex items-center justify-end gap-3 border-t">
          <button
            onClick={onClose}
            className="btn-secondary"
            disabled={loading}
          >
            ביטול
          </button>
          <button
            onClick={handleSave}
            className="btn-primary flex items-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <div className="spinner w-5 h-5"></div>
                <span>שומר...</span>
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                <span>שמור</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssignmentModal;
