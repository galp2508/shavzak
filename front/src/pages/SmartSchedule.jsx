import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Calendar, ChevronLeft, ChevronRight, Clock, Users,
  RefreshCw, Brain, ThumbsUp, ThumbsDown, Upload,
  AlertTriangle, TrendingUp, Award, Zap, Shield, Edit, ArrowLeftRight
} from 'lucide-react';
import { toast } from 'react-toastify';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, horizontalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import html2canvas from 'html2canvas';
import { Download } from 'lucide-react';
import Constraints from './Constraints';
import AssignmentModal from '../components/AssignmentModal';

const SortableHeader = ({ name }) => {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: name });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    cursor: 'grab',
    touchAction: 'none', // Important for PointerSensor
  };
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="flex-1 min-w-[200px] font-bold text-center p-2 bg-gray-100 border-l border-gray-300 select-none hover:bg-gray-200 active:cursor-grabbing"
    >
      {name}
    </div>
  );
};

const SmartSchedule = () => {
  const { user } = useAuth();
  const [currentDate, setCurrentDate] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mlStats, setMlStats] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentShavzakId, setCurrentShavzakId] = useState(null);
  const [iterationInfo, setIterationInfo] = useState(null);
  const [showConstraints, setShowConstraints] = useState(false);
  const [showManualAssignModal, setShowManualAssignModal] = useState(false);
  const [rejectedAssignment, setRejectedAssignment] = useState(null);
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [selectedForSwap, setSelectedForSwap] = useState(null); // משימה שנבחרה להחלפה
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackAssignmentId, setFeedbackAssignmentId] = useState(null);
  const [columnOrder, setColumnOrder] = useState([]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      setColumnOrder((items) => {
        const oldIndex = items.indexOf(active.id);
        const newIndex = items.indexOf(over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleExportImage = async () => {
    const element = document.getElementById('schedule-grid');
    if (!element) return;

    try {
      const canvas = await html2canvas(element, {
        scale: 2, // Higher quality
        useCORS: true,
        backgroundColor: '#ffffff',
      });
      
      const link = document.createElement('a');
      link.download = `shavzak-${currentDate.toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
      toast.success('התמונה נשמרה בהצלחה!');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('שגיאה בייצוא התמונה');
    }
  };

  // 🐛 Debug logging
  useEffect(() => {
    console.log('👤 User object:', user);
    console.log('👤 User role:', user?.role);
    console.log('✅ Should show AI button?', user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ');
  }, [user]);

  useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setCurrentDate(tomorrow);
    loadMahalkot();
    loadMLStats();
  }, []);

  useEffect(() => {
    if (currentDate) {
      loadSchedule(currentDate);
    }
  }, [currentDate]);

  useEffect(() => {
    if (scheduleData?.assignments) {
      const uniqueNames = [...new Set(scheduleData.assignments.map(a => a.name))].sort();
      setColumnOrder(prev => {
        // שמור על הסדר הקיים אם אפשר
        const newItems = uniqueNames.filter(n => !prev.includes(n));
        const existingItems = prev.filter(n => uniqueNames.includes(n));
        return [...existingItems, ...newItems];
      });
    }
  }, [scheduleData]);

  // האזן למקלדת
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight') {
        navigateDay(-1);
      } else if (e.key === 'ArrowLeft') {
        navigateDay(1);
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

  const loadMLStats = async () => {
    try {
      const response = await api.get('/ml/stats');
      setMlStats(response.data.stats);
    } catch (error) {
      console.error('Error loading ML stats:', error);
    }
  };

  const loadSchedule = async (date) => {
    setLoading(true);
    try {
      const dateStr = date.toISOString().split('T')[0];
      const response = await api.get(`/plugot/${user.pluga_id}/live-schedule?date=${dateStr}`);
      setScheduleData(response.data);

      // שמור את ה-shavzak_id אם קיים
      if (response.data.shavzak_id) {
        setCurrentShavzakId(response.data.shavzak_id);
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בטעינת שיבוץ');
      console.error('Load schedule error:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateSmartSchedule = async () => {
    if (!window.confirm('האם אתה בטוח שברצונך ליצור שיבוץ חכם עם AI ליומיים הבאים?')) {
      return;
    }

    setIsGenerating(true);
    try {
      // התחל מהיום הנוכחי (לא מתחילת שבוע)
      const startDate = new Date(currentDate);

      const response = await api.post('/ml/smart-schedule', {
        pluga_id: user.pluga_id,
        start_date: startDate.toISOString().split('T')[0],
        days_count: 2  // 2 ימים במקום 7
      });

      // הצג מידע על משימות שלא הצליחו
      if (response.data.failed_assignments && response.data.failed_assignments.length > 0) {
        toast.warning(`⚠️ ${response.data.message} - ${response.data.success_rate} הצליחו`);
      } else {
        toast.success(`🤖 ${response.data.message}`);
      }

      // טען את השיבוץ החדש
      await loadSchedule(currentDate);
      loadMLStats();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת שיבוץ חכם');
      console.error('Smart schedule error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFeedback = async (assignmentId, rating, reason = null) => {
    try {
      // אם זה דחייה ואין סיבה, פתח מודל
      if (rating === 'rejected' && !reason) {
        setFeedbackAssignmentId(assignmentId);
        setShowFeedbackModal(true);
        return;
      }

      const feedbackData = {
        assignment_id: assignmentId,
        shavzak_id: currentShavzakId,
        rating: rating,
        enable_auto_regeneration: false  // לא יוצר אוטומטית - נותן אופציה לשבץ ידנית
      };

      if (reason) {
        feedbackData.changes = { feedback_text: reason };
      }

      const response = await api.post('/ml/feedback', feedbackData);

      // הצג הודעה מהשרת
      toast.success(response.data.message);

      // אם הפידבק שלילי - הצע לשבץ ידנית
      if (rating === 'rejected') {
        // מצא את המשימה ששלילית
        const assignment = scheduleData?.assignments?.find(a => a.id === assignmentId) ||
          scheduleData?.schedules?.flatMap(s => s.assignments || [])
            .find(a => a.id === assignmentId);

        if (assignment) {
          setRejectedAssignment(assignment);
          // פתח אוטומטית את המודל לעריכה
          setTimeout(() => {
            setShowManualAssignModal(true);
          }, 500);
          toast.info('💡 פתחתי עבורך את חלון העריכה - שבץ ידנית כדי שהמערכת תלמד!', {
            autoClose: 3000
          });
        }
      }

      // רענן את הנתונים מיידית
      await loadSchedule(currentDate);
      loadMLStats();
    } catch (error) {
      toast.error('שגיאה בשמירת פידבק');
      console.error('Feedback error:', error);
    }
  };

  const handleManualAssignmentSave = async () => {
    try {
      // המשימה כבר נשמרה ע"י AssignmentModal
      // עכשיו נשלח פידבק ל-ML שהמשתמש ערך אותה ידנית
      const assignmentToFeedback = rejectedAssignment || editingAssignment;

      if (assignmentToFeedback) {
        await api.post('/ml/feedback', {
          assignment_id: assignmentToFeedback.id,
          shavzak_id: currentShavzakId,
          rating: 'modified',
          changes: {
            feedback_text: rejectedAssignment
              ? 'המשתמש דחה את השיבוץ ואז ערך אותו ידנית - לימוד מהעריכה'
              : 'המשתמש ערך את השיבוץ ידנית - לימוד מהעריכה'
          }
        });
      }

      toast.success('✅ שיבוץ נשמר בהצלחה!');
      setShowManualAssignModal(false);
      setRejectedAssignment(null);
      setEditingAssignment(null);
      loadSchedule(currentDate);
      loadMLStats();
    } catch (error) {
      toast.error('שגיאה בשליחת פידבק');
      console.error('Manual assignment error:', error);
    }
  };

  // Swap handler - החלפה בין משימות
  const handleSwapClick = (assignment, e) => {
    e.stopPropagation(); // מנע פתיחת modal של עריכה

    if (!selectedForSwap) {
      // בחירת משימה ראשונה להחלפה
      setSelectedForSwap(assignment);
      toast.info(`נבחרה משימה: ${assignment.name}. לחץ על כפתור החלפה במשימה נוספת`, {
        autoClose: 3000,
        icon: '🔄'
      });
    } else if (selectedForSwap.id === assignment.id) {
      // ביטול הבחירה - לחיצה על אותה משימה שוב
      setSelectedForSwap(null);
      toast.info('הבחירה בוטלה', {
        icon: '❌'
      });
    } else {
      // החלפה בין שתי המשימות
      swapAssignments(selectedForSwap, assignment);
    }
  };

  const swapAssignments = async (assignment1, assignment2) => {
    try {
      // החלף בין start_hour ו-name של שתי המשימות
      const updates = [
        {
          id: assignment1.id,
          start_hour: assignment2.start_hour,
          name: assignment2.name
        },
        {
          id: assignment2.id,
          start_hour: assignment1.start_hour,
          name: assignment1.name
        }
      ];

      // עדכן את שתי המשימות
      await Promise.all(updates.map(update =>
        api.patch(`/assignments/${update.id}/time`, {
          start_hour: update.start_hour,
          name: update.name
        })
      ));

      toast.success('המשימות הוחלפו בהצלחה! 🔄', {
        icon: '✅'
      });

      // נקה את מצב ההחלפה
      setSelectedForSwap(null);

      // רענן את הנתונים
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error swapping assignments:', error);
      toast.error(error.response?.data?.error || 'שגיאה בהחלפת המשימות');

      // נקה את מצב ההחלפה גם במקרה של שגיאה
      setSelectedForSwap(null);
    }
  };

  const navigateDay = (days) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + days);
    setCurrentDate(newDate);
  };

  const getMahlakaColor = (mahlakaId) => {
    const mahlaka = mahalkot.find(m => m.id === mahlakaId);
    return mahlaka?.color || '#6B7280';
  };

  // פונקציה לקביעת צבע משימה - פלוגתי או מחלקתי
  const getAssignmentColor = (assignment) => {
    const soldiers = assignment.soldiers || [];

    if (soldiers.length === 0) {
      return '#FBBF24'; // צהוב כברירת מחדל למשימות ללא חיילים
    }

    // מצא את כל המחלקות השונות
    const mahalkotSet = new Set(
      soldiers
        .map(s => s.mahlaka_id)
        .filter(id => id != null)
    );

    // אם יש 2 מחלקות או יותר - פלוגתי (צהוב)
    if (mahalkotSet.size >= 2) {
      return '#FBBF24'; // צהוב זהב
    }

    // אם יש מחלקה אחת - צבע המחלקה
    if (mahalkotSet.size === 1) {
      const mahlakaId = Array.from(mahalkotSet)[0];
      return getMahlakaColor(mahlakaId);
    }

    // ברירת מחדל - צהוב
    return '#FBBF24';
  };

  const getDayName = (date) => {
    const days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
    return days[date.getDay()];
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
      {/* Header with AI Badge */}
      <div className="card bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 text-white shadow-2xl border-none p-4 md:p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 w-full md:w-auto">
            <div className="bg-white bg-opacity-20 p-3 rounded-2xl backdrop-blur-sm hidden md:block">
              <Brain className="w-12 h-12 animate-pulse" />
            </div>
            <div className="flex-1 text-center md:text-right">
              <div className="flex items-center justify-center md:justify-start gap-3">
                <h1 className="text-3xl md:text-4xl font-bold tracking-tight">שיבוץ חכם AI</h1>
                <span className="bg-green-500 text-white text-xs px-3 py-1 rounded-full font-bold animate-pulse flex items-center gap-1">
                  <Zap size={12} />
                  POWERED BY ML
                </span>
              </div>
              <p className="text-purple-100 text-sm md:text-lg font-medium hidden md:block">למידת מכונה - משתפר עם הזמן</p>
            </div>
          </div>

          {/* Date Navigation */}
          <div className="flex items-center justify-between w-full md:w-auto gap-4 bg-white bg-opacity-20 backdrop-blur-md rounded-2xl p-2 md:p-4 shadow-lg">
            <button
              onClick={() => navigateDay(-1)}
              className="p-2 md:p-3 hover:bg-white hover:bg-opacity-30 rounded-xl transition-all duration-300 hover:scale-110 transform"
              title="יום קודם (מקש חץ ימינה)"
            >
              <ChevronRight size={24} className="md:w-7 md:h-7" />
            </button>

            <div className="text-center min-w-[120px] md:min-w-[220px]">
              <div className="text-xl md:text-3xl font-bold tracking-wide">
                {currentDate && getDayName(currentDate)}
              </div>
              <div className="text-sm md:text-base opacity-90 font-medium mt-1">
                {currentDate && currentDate.toLocaleDateString('he-IL')}
              </div>
            </div>

            <button
              onClick={() => navigateDay(1)}
              className="p-2 md:p-3 hover:bg-white hover:bg-opacity-30 rounded-xl transition-all duration-300 hover:scale-110 transform"
              title="יום הבא (מקש חץ שמאלה)"
            >
              <ChevronLeft size={24} className="md:w-7 md:h-7" />
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-center gap-2 w-full md:w-auto flex-wrap">
            {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
              <>
                <button
                  onClick={generateSmartSchedule}
                  disabled={isGenerating}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-3 py-2 rounded-lg transition-all flex items-center gap-2 shadow-lg disabled:opacity-50 text-sm md:text-base"
                  title="יצירת שיבוץ חכם עם AI"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={18} className="animate-spin" />
                      <span className="hidden sm:inline">מייצר...</span>
                    </>
                  ) : (
                    <>
                      <Brain size={18} />
                      <span className="hidden sm:inline">שיבוץ AI</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title="העלה דוגמאות שיבוץ"
                >
                  <Upload size={20} className="md:w-6 md:h-6" />
                </button>
              </>
            )}
            <button
              onClick={() => setShowConstraints(true)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="אילוצים ופידבק"
            >
              <Shield size={20} className="md:w-6 md:h-6" />
            </button>
            <button
              onClick={handleExportImage}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="ייצא לתמונה"
            >
              <Download size={20} className="md:w-6 md:h-6" />
            </button>
            <button
              onClick={() => loadSchedule(currentDate)}
              className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
              title="רענן"
              disabled={loading}
            >
              <RefreshCw size={20} className={`md:w-6 md:h-6 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* ML Stats Bar */}
      {mlStats && (
        <div className="card bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-semibold text-gray-700">
                דירוג אישור: {mlStats.approval_rate?.toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-semibold text-gray-700">
                דפוסים שנלמדו: {mlStats.patterns_learned}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-green-600" />
              <span className="text-sm font-semibold text-gray-700">
                סה"כ שיבוצים: {mlStats.total_assignments}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ThumbsUp className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-gray-700">
                אושרו: {mlStats.user_approvals}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ThumbsDown className="w-5 h-5 text-red-600" />
              <span className="text-sm font-semibold text-gray-700">
                נדחו: {mlStats.user_rejections}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Manual Assignment Suggestion - after rejected feedback */}
      {rejectedAssignment && (
        <div className="card bg-gradient-to-r from-orange-50 to-yellow-50 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Edit className="w-6 h-6 text-orange-600" />
              <div>
                <p className="font-semibold text-gray-800">משימה נדחתה - רוצה לשבץ ידנית?</p>
                <p className="text-sm text-gray-600">שיבוץ ידני ישמש כדוגמה למערכת וישפר את הלמידה</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowManualAssignModal(true)}
                className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <Edit size={18} />
                <span>שבץ ידנית</span>
              </button>
              <button
                onClick={() => setRejectedAssignment(null)}
                className="text-gray-600 hover:text-gray-800 px-3"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Iteration Info */}
      {iterationInfo && (
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-green-500 bg-opacity-20 p-2 rounded-full">
                <RefreshCw className="w-5 h-5 text-green-600 animate-spin" />
              </div>
              <div>
                <div className="text-sm font-bold text-green-800">
                  איטרציה #{iterationInfo.number} - השיבוץ שופר!
                </div>
                <div className="text-xs text-green-600">
                  אחוז הצלחה: {iterationInfo.successRate}
                </div>
              </div>
            </div>
            <button
              onClick={() => setIterationInfo(null)}
              className="text-green-600 hover:text-green-800 text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      )}

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
          <Brain className="w-16 h-16 text-purple-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-700 mb-2">אין משימות ליום זה</h3>
          <p className="text-gray-500 mb-4">לחץ על "שיבוץ AI" כדי ליצור שיבוץ חכם אוטומטי</p>
          {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
            <button
              onClick={generateSmartSchedule}
              disabled={isGenerating}
              className="btn-primary inline-flex items-center gap-2"
            >
              <Brain size={20} />
              <span>יצירת שיבוץ חכם</span>
            </button>
          )}
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
                  <div className="space-y-2">
                    {scheduleData.warnings.map((warning, index) => (
                      <div key={index} className="p-2 bg-yellow-100 rounded text-gray-800 text-sm">
                        {typeof warning === 'object' ? warning.message : warning}
                      </div>
                    ))}
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

            {/* Time Grid Schedule */}
            <div className="overflow-x-auto" id="schedule-grid">
              {(() => {
                let assignmentNames = columnOrder;
                const currentNames = [...new Set(scheduleData?.assignments?.map(a => a.name) || [])].sort();
                
                if (!assignmentNames || assignmentNames.length === 0) {
                    assignmentNames = currentNames;
                } else {
                    const missingNames = currentNames.filter(n => !assignmentNames.includes(n));
                    if (missingNames.length > 0) {
                        assignmentNames = [...assignmentNames, ...missingNames];
                    }
                    assignmentNames = assignmentNames.filter(n => currentNames.includes(n));
                }

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

                const hours = Array.from({ length: 24 }, (_, i) => i);

                return (
                  <DndContext 
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <div className="min-w-max">
                      {/* Header */}
                      <div className="flex border-b-2 border-gray-300 mb-2">
                        <div className="w-20 flex-shrink-0 font-bold text-gray-700 p-2">
                          שעה
                        </div>
                        <SortableContext 
                            items={assignmentNames}
                            strategy={horizontalListSortingStrategy}
                        >
                            {assignmentNames.map(name => (
                                <SortableHeader key={name} name={name} />
                            ))}
                        </SortableContext>
                      </div>

                    {/* Grid */}
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

                      {/* Assignment Columns */}
                      {assignmentNames.map(name => (
                        <div key={name} className="flex-1 min-w-[200px] border-l border-gray-300 relative">
                          {hours.map(hour => (
                            <div
                              key={hour}
                              className="h-12 border-b border-gray-200"
                            />
                          ))}

                          {/* Assignment Blocks */}
                          <div className="absolute inset-0">
                            {assignmentsByName[name]?.map(assignment => {
                              const startHour = assignment.start_hour || 0;
                              const lengthInHours = assignment.length_in_hours || 1;
                              const endHour = startHour + lengthInHours;
                              // שימוש בלוגיקה החדשה - פלוגתי (צהוב) או מחלקתי (צבע מחלקה)
                              const assignmentColor = getAssignmentColor(assignment);

                              const topPosition = (startHour / 24) * 100;
                              const height = (lengthInHours / 24) * 100;

                              // בדוק אם משימה זו נבחרה להחלפה
                              const isSelectedForSwap = selectedForSwap && selectedForSwap.id === assignment.id;
                              const swapClass = isSelectedForSwap ? 'ring-4 ring-yellow-500 shadow-yellow-500/50 animate-pulse' : '';

                              return (
                                <div
                                  key={assignment.id}
                                  className={`absolute rounded-lg shadow-md overflow-visible group cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] transform border ${swapClass}`}
                                  style={{
                                    top: `calc(${topPosition}% + 2px)`,
                                    height: `calc(${height}% - 4px)`,
                                    left: '6px',
                                    right: '6px',
                                    background: `linear-gradient(135deg, ${assignmentColor} 0%, ${assignmentColor}dd 100%)`,
                                    borderColor: assignmentColor,
                                  }}
                                >
                                  {/* Assignment Content */}
                                  <div className="p-2 h-full flex flex-col text-white backdrop-blur-sm relative">
                                    {/* Swap Button - תמיד גלוי */}
                                    {(user.role === 'מפ' || user.role === 'ממ') && (
                                      <button
                                        onClick={(e) => handleSwapClick(assignment, e)}
                                        className={`absolute bottom-1 right-1 rounded-md p-1.5 transition-all duration-200 z-10 pointer-events-auto shadow-lg ${
                                          isSelectedForSwap
                                            ? 'bg-yellow-500 text-white animate-pulse scale-110'
                                            : 'bg-white/40 hover:bg-yellow-400 hover:text-white opacity-70 hover:opacity-100 hover:scale-105'
                                        }`}
                                        title={isSelectedForSwap ? "לחץ שוב לביטול או לחץ על משימה אחרת להחלפה" : "החלף משימה זו עם אחרת"}
                                      >
                                        <ArrowLeftRight className="w-3.5 h-3.5" />
                                      </button>
                                    )}

                                    {/* Feedback and Edit Buttons - תמיד גלויים */}
                                    {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
                                      <div className="absolute top-1 left-1 z-10 flex gap-1 pointer-events-auto">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleFeedback(assignment.id, 'approved');
                                          }}
                                          className="bg-gradient-to-br from-green-400 to-emerald-600 hover:from-green-500 hover:to-emerald-700 text-white p-1.5 rounded-full shadow-lg transition-all duration-200 hover:scale-110 transform"
                                          title="אישור שיבוץ - המערכת תלמד מהפידבק"
                                        >
                                          <ThumbsUp className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleFeedback(assignment.id, 'rejected');
                                          }}
                                          className="bg-gradient-to-br from-red-400 to-rose-600 hover:from-red-500 hover:to-rose-700 text-white p-1.5 rounded-full shadow-lg transition-all duration-200 hover:scale-110 transform"
                                          title="דחיית שיבוץ - המערכת תלמד מהפידבק"
                                        >
                                          <ThumbsDown className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            setEditingAssignment(assignment);
                                            setShowManualAssignModal(true);
                                          }}
                                          className="bg-gradient-to-br from-blue-400 to-blue-600 hover:from-blue-500 hover:to-blue-700 text-white p-1.5 rounded-full shadow-lg transition-all duration-200 hover:scale-110 transform"
                                          title="ערוך משימה"
                                        >
                                          <Edit className="w-3.5 h-3.5" />
                                        </button>
                                      </div>
                                    )}

                                    {/* Name & Time */}
                                    <div className="font-bold text-sm mb-1 flex items-center gap-1.5">
                                      <Clock className="w-3.5 h-3.5" />
                                      {assignment.name}
                                    </div>
                                    <div className="text-xs opacity-95 mb-1.5 font-medium bg-black bg-opacity-20 rounded px-1.5 py-0.5 inline-block">
                                      {startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00
                                    </div>

                                    {/* Soldiers */}
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

                                    {/* No soldiers */}
                                    {(!assignment.soldiers || assignment.soldiers.length === 0) && (
                                      <div className="text-xs opacity-80 italic bg-red-500/30 px-2 py-1 rounded border border-red-400/50">
                                        אין חיילים משובצים
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  </DndContext>
                );
              })()}
            </div>
          </div>
        </>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadExamplesModal
          onClose={() => setShowUploadModal(false)}
          onUploadSuccess={() => {
            loadMLStats();
            toast.success('✅ דוגמאות הועלו בהצלחה - המודל משתפר!');
          }}
        />
      )}

      {/* Feedback Reason Modal */}
      {showFeedbackModal && (
        <FeedbackReasonModal
          onClose={() => {
            setShowFeedbackModal(false);
            setFeedbackAssignmentId(null);
          }}
          onSubmit={(reason) => {
            handleFeedback(feedbackAssignmentId, 'rejected', reason);
            setShowFeedbackModal(false);
            setFeedbackAssignmentId(null);
          }}
        />
      )}

      {/* Constraints Modal */}
      {showConstraints && (
        <Constraints
          onClose={() => setShowConstraints(false)}
          onUpdate={() => {
            loadSchedule(currentDate);
            loadMLStats();
          }}
        />
      )}

      {/* Manual Assignment Modal - for editing or after rejected feedback */}
      {showManualAssignModal && (rejectedAssignment || editingAssignment) && (
        <AssignmentModal
          assignment={rejectedAssignment || editingAssignment}
          date={currentDate}
          dayIndex={(rejectedAssignment || editingAssignment)?.day}
          shavzakId={currentShavzakId}
          plugaId={user.pluga_id}
          onClose={() => {
            setShowManualAssignModal(false);
            setRejectedAssignment(null);
            setEditingAssignment(null);
          }}
          onSave={handleManualAssignmentSave}
        />
      )}
    </div>
  );
};

// Upload Examples Modal Component
const UploadExamplesModal = ({ onClose, onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error('בחר לפחות קובץ אחד');
      return;
    }

    setUploading(true);
    try {
      for (const file of selectedFiles) {
        // המרת קובץ ל-base64
        const reader = new FileReader();
        const base64 = await new Promise((resolve) => {
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(file);
        });

        // העלאה לשרת
        await api.post('/ml/upload-example', {
          image: base64,
          rating: 'good'
        });
      }

      toast.success(`✅ הועלו ${selectedFiles.length} דוגמאות!`);
      onUploadSuccess();
      onClose();
    } catch (error) {
      toast.error('שגיאה בהעלאת דוגמאות');
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Upload className="w-6 h-6 text-purple-600" />
            העלאת דוגמאות שיבוץ
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="mb-4">
          <p className="text-gray-600 mb-2">
            העלה תמונות של שיבוצים ידניים טובים - המערכת תלמד מהם!
          </p>
          <div className="border-2 border-dashed border-purple-300 rounded-lg p-6 text-center bg-purple-50">
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center gap-2"
            >
              <Upload className="w-12 h-12 text-purple-400" />
              <span className="text-purple-600 font-medium">
                לחץ לבחירת קבצים
              </span>
              <span className="text-sm text-gray-500">
                תמונות, PDF או Excel
              </span>
            </label>
          </div>

          {selectedFiles.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-semibold text-gray-700 mb-2">
                נבחרו {selectedFiles.length} קבצים:
              </p>
              <div className="space-y-1">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                    {file.name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={uploading || selectedFiles.length === 0}
            className="flex-1 btn-primary disabled:opacity-50"
          >
            {uploading ? 'מעלה...' : 'העלה והאמן'}
          </button>
          <button
            onClick={onClose}
            className="flex-1 btn-secondary"
          >
            ביטול
          </button>
        </div>
      </div>
    </div>
  );
};

// Feedback Reason Modal
const FeedbackReasonModal = ({ onClose, onSubmit }) => {
  const [reason, setReason] = useState('');
  const [customReason, setCustomReason] = useState('');

  const reasons = [
    'חיילים לא מתאימים',
    'ערבוב מחלקות',
    'תזמון לא טוב',
    'חוסר במפקדים/נהגים',
    'אחר'
  ];

  const handleSubmit = () => {
    const finalReason = reason === 'אחר' ? customReason : reason;
    if (!finalReason) return;
    onSubmit(finalReason);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">למה השיבוץ לא טוב?</h3>
        <p className="text-gray-600 mb-4 text-sm">
          הסבר קצר יעזור למערכת ללמוד ולהשתפר לפעם הבאה.
        </p>

        <div className="space-y-2 mb-4">
          {reasons.map((r) => (
            <label key={r} className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
              <input
                type="radio"
                name="reason"
                value={r}
                checked={reason === r}
                onChange={(e) => setReason(e.target.value)}
                className="w-4 h-4 text-purple-600"
              />
              <span className="text-gray-700">{r}</span>
            </label>
          ))}
        </div>

        {reason === 'אחר' && (
          <textarea
            value={customReason}
            onChange={(e) => setCustomReason(e.target.value)}
            placeholder="פרט את הסיבה..."
            className="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-purple-500 outline-none"
            rows={3}
          />
        )}

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleSubmit}
            disabled={!reason || (reason === 'אחר' && !customReason)}
            className="flex-1 btn-primary"
          >
            שלח פידבק
          </button>
          <button onClick={onClose} className="flex-1 btn-secondary">
            ביטול
          </button>
        </div>
      </div>
    </div>
  );
};

export default SmartSchedule;
