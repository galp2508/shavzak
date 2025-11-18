import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight, Clock, Users, RefreshCw, Shield, AlertTriangle, Trash2, Plus, Edit, Move } from 'lucide-react';
import { toast } from 'react-toastify';
import Constraints from './Constraints';
import AssignmentModal from '../components/AssignmentModal';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, useDroppable, useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

const LiveSchedule = () => {
  const { user } = useAuth();
  const [currentDate, setCurrentDate] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConstraints, setShowConstraints] = useState(false);
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);

  useEffect(() => {
    // התחל עם מחר
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setCurrentDate(tomorrow);
    loadMahalkot();
  }, []);

  useEffect(() => {
    if (currentDate) {
      loadSchedule(currentDate);
    }
  }, [currentDate]);

  // האזן לשינויים בתבניות משימות
  useEffect(() => {
    const handleTemplateChange = () => {
      if (currentDate) {
        loadSchedule(currentDate);
      }
    };

    window.addEventListener('templateChanged', handleTemplateChange);
    return () => window.removeEventListener('templateChanged', handleTemplateChange);
  }, [currentDate]);

  // טיפול במקלדת - חצים
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') {
        navigateDay(-1); // ימינה = אתמול (RTL)
      } else if (e.key === 'ArrowLeft') {
        navigateDay(1); // שמאלה = מחר (RTL)
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentDate]);

  const loadMahalkot = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      setMahalkot(response.data.mahalkot || []);
    } catch (error) {
      console.error('Error loading mahalkot:', error);
    }
  };

  const loadSchedule = async (date) => {
    setLoading(true);
    try {
      const dateStr = date.toISOString().split('T')[0];
      const response = await api.get(`/plugot/${user.pluga_id}/live-schedule?date=${dateStr}`);
      setScheduleData(response.data);
    } catch (error) {
      const errorData = error.response?.data;
      let errorMessage = errorData?.error || error.message;

      // הוסף המלצות אם קיימות
      if (errorData?.suggestions && errorData.suggestions.length > 0) {
        errorMessage += '\n\nהמלצות:\n' + errorData.suggestions.map(s => `• ${s}`).join('\n');
      }

      // הצג גם פרטים טכניים אם קיימים
      if (errorData?.technical_details) {
        console.error('Technical details:', errorData.technical_details);
      }

      toast.error(errorMessage, { autoClose: 8000 });
      console.error('Load schedule error:', error);
    } finally {
      setLoading(false);
    }
  };

  const navigateDay = (days) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + days);
    setCurrentDate(newDate);
  };

  const handleFeedback = async (assignmentId, rating) => {
    try {
      // מצא את ה-shavzak_id (שיבוץ אוטומטי)
      const shavzakId = scheduleData?.shavzak_id;
      if (!shavzakId) {
        toast.error('לא נמצא מזהה שיבוץ');
        return;
      }

      const response = await api.post('/ml/feedback', {
        assignment_id: assignmentId,
        shavzak_id: shavzakId,
        rating: rating,
        enable_auto_regeneration: false  // לא לרענן אוטומטית בשיבוץ חי
      });

      // הצג הודעה מהשרת
      if (rating === 'approved') {
        toast.success('✅ פידבק חיובי נשמר - המודל לומד מזה!');
      } else if (rating === 'rejected') {
        toast.info('❌ פידבק שלילי נשמר - המודל ישתפר!');
      }

      // אין רענון אוטומטי בשיבוץ חי
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'שגיאה בשמירת פידבק';
      toast.error(errorMsg);
      console.error('Feedback error:', error);
    }
  };

  const getMahlakaColor = (mahlakaId) => {
    const mahlaka = mahalkot.find(m => m.id === mahlakaId);
    return mahlaka?.color || '#6B7280';
  };

  // קבע צבע לפי פלוגתי/מחלקתי
  const getAssignmentColor = (assignment) => {
    const soldiers = assignment.soldiers || [];
    if (soldiers.length === 0) return '#FBBF24'; // צהוב כברירת מחדל אם אין חיילים

    // בדוק כמה מחלקות שונות יש במשימה
    const mahalkotSet = new Set(
      soldiers.map(s => s.mahlaka_id).filter(id => id != null)
    );

    // אם יש 2+ מחלקות = פלוגתי (צהוב)
    if (mahalkotSet.size >= 2) {
      return '#FBBF24'; // צהוב זהב לפלוגתי
    }

    // אם יש מחלקה אחת = צבע המחלקה
    if (mahalkotSet.size === 1) {
      const mahlakaId = Array.from(mahalkotSet)[0];
      return getMahlakaColor(mahlakaId);
    }

    return '#FBBF24'; // צהוב כברירת מחדל
  };

  const getDayName = (date) => {
    const days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
    return days[date.getDay()];
  };

  const deleteAssignment = async (assignmentId, assignmentName) => {
    if (!window.confirm(`האם אתה בטוח שברצונך למחוק את המשימה "${assignmentName}"?`)) {
      return;
    }

    try {
      await api.delete(`/assignments/${assignmentId}`);
      toast.success(`המשימה "${assignmentName}" נמחקה בהצלחה`);
      // רענן את הנתונים
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error deleting assignment:', error);
      toast.error(error.response?.data?.error || 'שגיאה במחיקת המשימה');
    }
  };

  const openNewAssignmentModal = () => {
    setEditingAssignment(null);
    setShowAssignmentModal(true);
  };

  const openEditAssignmentModal = (assignment) => {
    setEditingAssignment(assignment);
    setShowAssignmentModal(true);
  };

  const closeAssignmentModal = () => {
    setShowAssignmentModal(false);
    setEditingAssignment(null);
  };

  const handleAssignmentSave = () => {
    loadSchedule(currentDate);
  };

  // Drag & Drop handlers
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // דרוש תזוזה של 8 פיקסלים כדי להתחיל גרירה
      },
    })
  );

  const handleDragEnd = async (event) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    // מצא את המשימה שנגררה
    const draggedAssignment = scheduleData?.assignments?.find(a => a.id === active.id);
    if (!draggedAssignment) {
      return;
    }

    // חלץ את השעה ושם התבנית החדשים מה-over id (פורמט: "drop-zone-{name}-{hour}")
    const overIdParts = over.id.toString().split('-');
    const newStartHour = parseInt(overIdParts[overIdParts.length - 1]);

    // שם התבנית הוא כל מה שבין "drop-zone-" ל-hour האחרון
    const newTemplateName = overIdParts.slice(2, -1).join('-');

    if (isNaN(newStartHour)) {
      return;
    }

    // בדוק אם משהו באמת השתנה
    const hourChanged = draggedAssignment.start_hour !== newStartHour;
    const templateChanged = draggedAssignment.name !== newTemplateName;

    if (!hourChanged && !templateChanged) {
      return;
    }

    try {
      // הכן את הנתונים לעדכון
      const updateData = {};

      if (hourChanged) {
        updateData.start_hour = newStartHour;
      }

      if (templateChanged) {
        updateData.name = newTemplateName;
      }

      // עדכן את השרת
      await api.patch(`/assignments/${draggedAssignment.id}/time`, updateData);

      // הודעה מותאמת
      if (hourChanged && templateChanged) {
        toast.success(`המשימה הועברה ל-${newTemplateName} בשעה ${newStartHour.toString().padStart(2, '0')}:00`);
      } else if (templateChanged) {
        toast.success(`המשימה שונתה ל-${newTemplateName}`);
      } else {
        toast.success(`המשימה הועברה לשעה ${newStartHour.toString().padStart(2, '0')}:00`);
      }

      // רענן את הנתונים
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error updating assignment:', error);
      toast.error(error.response?.data?.error || 'שגיאה בהזזת המשימה');
    }
  };

  if (loading && !scheduleData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Date Navigation */}
      <div className="card bg-gradient-to-br from-military-600 via-military-700 to-military-800 text-white shadow-2xl border-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="bg-white bg-opacity-20 p-3 rounded-2xl backdrop-blur-sm">
              <Calendar className="w-12 h-12" />
            </div>
            <div className="flex-1">
              <h1 className="text-4xl font-bold tracking-tight">שיבוץ חי</h1>
              <p className="text-military-100 text-lg font-medium">ניווט אוטומטי בין ימים</p>
            </div>
          </div>

          {/* Date Navigation */}
          <div className="flex items-center gap-4 bg-white bg-opacity-20 backdrop-blur-md rounded-2xl p-4 shadow-lg">
            <button
              onClick={() => navigateDay(-1)}
              className="p-3 hover:bg-white hover:bg-opacity-30 rounded-xl transition-all duration-300 hover:scale-110 transform"
              title="יום קודם (מקש חץ ימינה)"
            >
              <ChevronRight size={28} />
            </button>

            <div className="text-center min-w-[220px]">
              <div className="text-3xl font-bold tracking-wide">
                {currentDate && getDayName(currentDate)}
              </div>
              <div className="text-base opacity-90 font-medium mt-1">
                {currentDate && currentDate.toLocaleDateString('he-IL')}
              </div>
            </div>

            <button
              onClick={() => navigateDay(1)}
              className="p-3 hover:bg-white hover:bg-opacity-30 rounded-xl transition-all duration-300 hover:scale-110 transform"
              title="יום הבא (מקש חץ שמאלה)"
            >
              <ChevronLeft size={28} />
            </button>
          </div>

          <div className="flex items-center gap-2 mr-4">
            {(user.role === 'מפ' || user.role === 'ממ') && (
              <>
                <button
                  onClick={openNewAssignmentModal}
                  className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors flex items-center gap-2"
                  title="הוסף משימה חדשה"
                >
                  <Plus size={24} />
                  <span className="hidden md:inline">משימה חדשה</span>
                </button>
                <button
                  onClick={() => setShowConstraints(true)}
                  className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title="אילוצי שיבוץ"
                >
                  <Shield size={24} />
                </button>
              </>
            )}
            <button
              onClick={() => loadSchedule(currentDate)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="רענן"
              disabled={loading}
            >
              <RefreshCw size={24} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="card bg-blue-50 border-l-4 border-blue-500">
        <div className="flex items-center gap-2 text-blue-700">
          <kbd className="px-2 py-1 bg-white border border-blue-300 rounded text-sm">←</kbd>
          <span>יום הבא</span>
          <span className="mx-2">•</span>
          <kbd className="px-2 py-1 bg-white border border-blue-300 rounded text-sm">→</kbd>
          <span>יום קודם</span>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="card text-center py-12">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">טוען שיבוץ...</p>
        </div>
      ) : scheduleData?.assignments?.length === 0 ? (
        /* No Assignments */
        <div className="card text-center py-12">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-700 mb-2">אין משימות ליום זה</h3>
          <p className="text-gray-500">לא נמצאו משימות לתאריך {scheduleData?.date_display}</p>
          <p className="text-sm text-gray-400 mt-2">
            ודא שיש תבניות משימות מוגדרות במערכת
          </p>
        </div>
      ) : (
        /* Assignments List */
        <>
          {/* Warnings Section */}
          {/* {scheduleData?.warnings && scheduleData.warnings.length > 0 && (
            <div className="card bg-yellow-50 border-r-4 border-yellow-500">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-yellow-900 mb-3">
                    אזהרות שיבוץ ({scheduleData.warnings.length})
                  </h3>
                  <div className="space-y-3">
                    {scheduleData.warnings.map((warning, index) => {
                      // תמיכה בפורמט ישן (string) וחדש (object)
                      const isObject = typeof warning === 'object';
                      const message = isObject ? warning.message : warning;
                      const severity = isObject ? warning.severity : 'warning';
                      const suggestion = isObject ? warning.suggestion : null;
                      const suggestDeletion = isObject ? warning.suggest_deletion : false;
                      const assignmentId = isObject ? warning.assignment_id : null;
                      const assignmentName = isObject ? warning.assignment_name : null;

                      // צבעים לפי רמת חומרה
                      const severityColors = {
                        critical: 'bg-red-100 border-red-300',
                        high: 'bg-orange-100 border-orange-300',
                        warning: 'bg-yellow-100 border-yellow-300'
                      };
                      const bgColor = severityColors[severity] || severityColors.warning;

                      return (
                        <div key={index} className={`p-3 rounded-lg border-r-2 ${bgColor}`}>
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <p className="text-gray-800 text-sm font-medium mb-1">
                                {message}
                              </p>
                              {suggestion && (
                                <p className="text-gray-700 text-xs mt-2 bg-white/60 p-2 rounded">
                                  💡 {suggestion}
                                </p>
                              )}
                            </div>
                            {suggestDeletion && assignmentId && (
                              <button
                                onClick={() => deleteAssignment(assignmentId, assignmentName)}
                                className="btn-secondary-sm flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white border-red-700"
                                title="מחק משימה זו"
                              >
                                <Trash2 className="w-4 h-4" />
                                <span className="text-xs">מחק</span>
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )} */}

          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                לוח שעות - {getDayName(currentDate)}
              </h2>
              <span className="text-sm text-gray-500">
                {scheduleData?.assignments?.length} משימות
              </span>
            </div>

            {/* Time Grid Schedule with Drag & Drop */}
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <div className="overflow-x-auto">
                {(() => {
                  // קבל את כל שמות התבניות הייחודיים
                  const assignmentNames = [...new Set(scheduleData?.assignments?.map(a => a.name) || [])].sort();

                // צור מפה של משימות לפי שם ושעה
                const assignmentsByName = {};
                assignmentNames.forEach(name => {
                  assignmentsByName[name] = [];
                });

                scheduleData?.assignments?.forEach(assignment => {
                  if (!assignmentsByName[assignment.name]) {
                    assignmentsByName[assignment.name] = [];
                  }
                  assignmentsByName[assignment.name].push(assignment);
                });

                // יצירת 24 שעות
                const hours = Array.from({ length: 24 }, (_, i) => i);

                return (
                  <div className="min-w-max">
                    {/* Header - שמות תבניות */}
                    <div className="flex border-b-2 border-gray-300 mb-2">
                      <div className="w-20 flex-shrink-0 font-bold text-gray-700 p-2">
                        שעה
                      </div>
                      {assignmentNames.map(name => (
                        <div
                          key={name}
                          className="flex-1 min-w-[200px] font-bold text-center p-2 bg-gray-100 border-l border-gray-300"
                        >
                          {name}
                        </div>
                      ))}
                    </div>

                    {/* Grid Container */}
                    <div className="flex">
                      {/* Hours Column */}
                      <div className="w-20 flex-shrink-0">
                        {hours.map(hour => (
                          <div
                            key={hour}
                            className="h-12 flex items-center justify-center border-b border-gray-200 text-sm text-gray-600 font-medium"
                          >
                            {hour.toString().padStart(2, '0')}:00
                          </div>
                        ))}
                      </div>

                      {/* Assignment Name Columns */}
                      {assignmentNames.map(name => (
                        <div key={name} className="flex-1 min-w-[200px] border-l border-gray-300 relative">
                          {/* Hour Grid Lines with Drop Zones */}
                          {hours.map(hour => (
                            <DropZone
                              key={hour}
                              id={`drop-zone-${name}-${hour}`}
                              hour={hour}
                            />
                          ))}

                          {/* Assignment Blocks - Positioned Absolutely with Drag */}
                          <div className="absolute inset-0 pointer-events-none">
                            {assignmentsByName[name]?.map(assignment => {
                              const startHour = assignment.start_hour || 0;
                              const lengthInHours = assignment.length_in_hours || 1;
                              const endHour = startHour + lengthInHours;
                              // צבע לפי פלוגתי (2+ מחלקות = צהוב) או מחלקתי (צבע המחלקה)
                              const assignmentColor = getAssignmentColor(assignment);

                              // Calculate position and height
                              const topPosition = (startHour / 24) * 100;
                              const height = (lengthInHours / 24) * 100;

                              return (
                                <DraggableAssignment
                                  key={assignment.id}
                                  assignment={assignment}
                                  topPosition={topPosition}
                                  height={height}
                                  assignmentColor={assignmentColor}
                                  startHour={startHour}
                                  endHour={endHour}
                                  onEdit={(user.role === 'מפ' || user.role === 'ממ') ? openEditAssignmentModal : null}
                                  userRole={user.role}
                                >
                                </DraggableAssignment>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  );
                })()}
              </div>
            </DndContext>
          </div>
        </>
      )}

      {/* Constraints Modal */}
      {showConstraints && (
        <Constraints
          onClose={() => setShowConstraints(false)}
          onUpdate={() => {
            // רענן את השיבוץ החי כאשר האילוצים משתנים
            if (currentDate) {
              loadSchedule(currentDate);
            }
          }}
        />
      )}

      {/* Assignment Modal */}
      {showAssignmentModal && (
        <AssignmentModal
          assignment={editingAssignment}
          date={currentDate}
          dayIndex={scheduleData?.day_index}
          shavzakId={scheduleData?.shavzak_id}
          plugaId={user.pluga_id}
          onClose={closeAssignmentModal}
          onSave={handleAssignmentSave}
        />
      )}
    </div>
  );
};

// DropZone Component - אזור שאפשר לזרוק בו משימות
const DropZone = ({ id, hour }) => {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`h-12 border-b border-gray-200 transition-colors ${
        isOver ? 'bg-blue-100 border-blue-400' : ''
      }`}
      data-hour={hour}
    />
  );
};

// DraggableAssignment Component - משימה שאפשר לגרור
const DraggableAssignment = ({
  assignment,
  topPosition,
  height,
  assignmentColor,
  startHour,
  endHour,
  onEdit,
  userRole
}) => {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: assignment.id,
  });

  const style = {
    top: `calc(${topPosition}% + 2px)`,
    height: `calc(${height}% - 4px)`,
    left: '6px',
    right: '6px',
    background: `linear-gradient(135deg, ${assignmentColor} 0%, ${assignmentColor}dd 100%)`,
    borderColor: assignmentColor,
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    opacity: isDragging ? 0.5 : 1,
    cursor: (userRole === 'מפ' || userRole === 'ממ') ? 'grab' : 'default',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className="absolute rounded-lg shadow-md overflow-hidden group hover:shadow-lg transition-all duration-200 hover:scale-[1.02] transform border pointer-events-auto"
      onClick={() => onEdit && onEdit(assignment)}
      title={`${assignment.name} (${startHour.toString().padStart(2, '0')}:00 - ${endHour.toString().padStart(2, '0')}:00) - גרור להזזה`}
    >
      {/* Assignment Content */}
      <div className="p-2 h-full flex flex-col text-white backdrop-blur-sm relative">
        {/* Drag Icon */}
        {(userRole === 'מפ' || userRole === 'ממ') && (
          <div className="absolute top-1 left-1 bg-white/30 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Move className="w-3 h-3" />
          </div>
        )}

        {/* Edit Icon */}
        {(userRole === 'מפ' || userRole === 'ממ') && onEdit && (
          <div className="absolute top-1 right-1 bg-white/30 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Edit className="w-3 h-3" />
          </div>
        )}

        {/* Assignment Name & Time */}
        <div className="font-bold text-sm mb-1 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          {assignment.name}
        </div>
        <div className="text-xs opacity-95 mb-1.5 font-medium bg-black bg-opacity-20 rounded px-1.5 py-0.5 inline-block">
          {startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00
        </div>

        {/* Soldiers List */}
        {assignment.soldiers && assignment.soldiers.length > 0 && (
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-1">
              {assignment.soldiers.map((soldier) => (
                <div
                  key={soldier.id}
                  className="text-xs bg-white/25 backdrop-blur-md px-2 py-1 rounded border border-white/30 shadow-sm hover:bg-white/35 transition-all duration-200"
                >
                  <div className="font-semibold flex items-center gap-1">
                    <Users className="w-2.5 h-2.5" />
                    {soldier.name}
                  </div>
                  <div className="text-[10px] opacity-90 font-medium">
                    {soldier.role_in_assignment}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No soldiers indicator */}
        {(!assignment.soldiers || assignment.soldiers.length === 0) && (
          <div className="text-xs opacity-80 italic bg-red-500/30 px-2 py-1 rounded border border-red-400/50">
            אין חיילים משובצים
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveSchedule;
