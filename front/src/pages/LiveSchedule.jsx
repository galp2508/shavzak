import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight, Clock, Users, RefreshCw, Shield, AlertTriangle, Trash2, Plus, Edit, Brain, ThumbsUp, ThumbsDown, Sparkles, CheckCircle2, XCircle, TrendingUp, Award, Zap, ArrowLeftRight } from 'lucide-react';
import { toast } from 'react-toastify';
import Constraints from './Constraints';
import AssignmentModal from '../components/AssignmentModal';

const LiveSchedule = () => {
  const { user } = useAuth();
  const [currentDate, setCurrentDate] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showConstraints, setShowConstraints] = useState(false);
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false); // מצב יצירת שיבוץ AI
  const [feedbackGiven, setFeedbackGiven] = useState({}); // מעקב אחרי פידבקים שניתנו {assignmentId: 'approved'/'rejected'}
  const [mlStats, setMlStats] = useState(null); // סטטיסטיקות ML
  const [selectedForSwap, setSelectedForSwap] = useState(null); // משימה שנבחרה להחלפה

  useEffect(() => {
    // התחל עם מחר
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

      // בדוק אם אין משימות ליום זה והתאריך בעתיד
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const checkDate = new Date(date);
      checkDate.setHours(0, 0, 0, 0);

      if (response.data.assignments && response.data.assignments.length === 0 && checkDate >= today) {
        // אין שיבוץ ליום זה - בנה אוטומטית 2 ימים קדימה
        console.log(`📅 אין שיבוץ ל-${dateStr} - בונה אוטומטית 2 ימים קדימה`);
        await generateScheduleAutomatically(date);
      }
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

  const generateScheduleAutomatically = async (startDate) => {
    try {
      console.log('🤖 בונה שיבוץ אוטומטי ליומיים קדימה...');
      const response = await api.post('/ml/smart-schedule', {
        pluga_id: user.pluga_id,
        start_date: startDate.toISOString().split('T')[0],
        days_count: 2
      });

      // רענן את התצוגה בשקט (בלי הודעה)
      if (response.data) {
        loadSchedule(currentDate);
        console.log('✅ שיבוץ אוטומטי הושלם');
      }
    } catch (error) {
      console.error('שגיאה בשיבוץ אוטומטי:', error);
      // לא מציגים שגיאה למשתמש - זה רק ניסיון אוטומטי
    }
  };

  const navigateDay = (days) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + days);
    setCurrentDate(newDate);
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

      loadSchedule(currentDate);
      loadMLStats(); // עדכן סטטיסטיקות ML
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת שיבוץ חכם');
      console.error('Smart schedule error:', error);
    } finally {
      setIsGenerating(false);
    }
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

      // עדכן את ה-state של הפידבקים
      setFeedbackGiven(prev => ({
        ...prev,
        [assignmentId]: rating
      }));

      // הצג הודעה מהשרת
      if (rating === 'approved') {
        toast.success('✅ פידבק חיובי נשמר - המודל לומד מזה!', {
          autoClose: 3000,
          icon: '🎉'
        });
      } else if (rating === 'rejected') {
        toast.info('❌ פידבק שלילי נשמר - המודל ישתפר!', {
          autoClose: 3000,
          icon: '📝'
        });
      }

      // אין רענון אוטומטי בשיבוץ חי
      // עדכן סטטיסטיקות ML
      loadMLStats();
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

    // סנן רק חיילים שאינם נהגים - נהגים לא קובעים את צבע המשימה
    const nonDriverSoldiers = soldiers.filter(s => s.role_in_assignment !== 'driver');

    // אם אין חיילים שאינם נהגים, השתמש בצהוב
    if (nonDriverSoldiers.length === 0) return '#FBBF24';

    // בדוק כמה מחלקות שונות יש במשימה (לא כולל נהגים)
    const mahalkotSet = new Set(
      nonDriverSoldiers.map(s => s.mahlaka_id).filter(id => id != null)
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
      <div className="card bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white shadow-2xl border-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="bg-white bg-opacity-20 p-3 rounded-2xl backdrop-blur-sm animate-pulse-slow">
              <Calendar className="w-12 h-12" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-4xl font-bold tracking-tight">שיבוץ חי</h1>
                <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xs px-3 py-1 rounded-full font-bold animate-pulse flex items-center gap-1">
                  <Sparkles size={12} />
                  LIVE
                </span>
              </div>
              <p className="text-purple-100 text-lg font-medium">ניווט אוטומטי בין ימים • למידת מכונה פעילה</p>
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
            {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
              <>
                <button
                  onClick={generateSmartSchedule}
                  disabled={isGenerating}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-3 py-2 rounded-lg transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
                  title="יצירת שיבוץ חכם עם AI"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={20} className="animate-spin" />
                      <span className="hidden md:inline">מייצר...</span>
                    </>
                  ) : (
                    <>
                      <Brain size={20} />
                      <span className="hidden md:inline">שיבוץ AI</span>
                    </>
                  )}
                </button>
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

      {/* Feedback Panel - למעלה משמאל */}
      {scheduleData?.assignments && scheduleData.assignments.some(a => a.is_ai_generated) && (user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ') && (
        <div className="card bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-300 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-2 rounded-full">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-800">פידבק למערכת AI</h3>
                <p className="text-sm text-gray-600">עבור על משימות ותן פידבק לשיפור המערכת</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-green-50 px-4 py-2 rounded-lg border border-green-200">
                <ThumbsUp className="w-5 h-5 text-green-600" />
                <div>
                  <div className="text-xs text-gray-500">אושרו</div>
                  <div className="text-lg font-bold text-green-700">{mlStats?.user_approvals || 0}</div>
                </div>
              </div>
              <div className="flex items-center gap-2 bg-red-50 px-4 py-2 rounded-lg border border-red-200">
                <ThumbsDown className="w-5 h-5 text-red-600" />
                <div>
                  <div className="text-xs text-gray-500">נדחו</div>
                  <div className="text-lg font-bold text-red-700">{mlStats?.user_rejections || 0}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ML Stats Bar - סטטיסטיקות מטורפות */}
      {mlStats && (
        <div className="card bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 border-l-4 border-blue-500 shadow-xl">
          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-2 rounded-full">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">דירוג אישור</div>
                <div className="text-lg font-bold text-blue-700">
                  {mlStats.approval_rate?.toFixed(1)}%
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-2 rounded-full">
                <Award className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">דפוסים שנלמדו</div>
                <div className="text-lg font-bold text-purple-700">
                  {mlStats.patterns_learned}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-green-500 to-green-600 p-2 rounded-full">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">סה"כ שיבוצים</div>
                <div className="text-lg font-bold text-green-700">
                  {mlStats.total_assignments}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-emerald-400 to-emerald-500 p-2 rounded-full">
                <ThumbsUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">אושרו</div>
                <div className="text-lg font-bold text-emerald-700">
                  {mlStats.user_approvals}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-red-400 to-red-500 p-2 rounded-full">
                <ThumbsDown className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">נדחו</div>
                <div className="text-lg font-bold text-red-700">
                  {mlStats.user_rejections}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-yellow-400 to-orange-500 p-2 rounded-full animate-pulse">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-500 font-medium">אחוז הצלחה</div>
                <div className="text-lg font-bold text-orange-700">
                  {mlStats.total_assignments > 0
                    ? ((mlStats.user_approvals / mlStats.total_assignments) * 100).toFixed(1)
                    : 0}%
                </div>
              </div>
            </div>
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

            {/* Time Grid Schedule */}
            <div className="overflow-x-auto">
              {(() => {
                // צור מפה של משימות לפי שם ושעה
                const assignmentNames = [...new Set(scheduleData?.assignments?.map(a => a.name) || [])].sort();
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
                        {/* Hour Grid Lines */}
                        {hours.map(hour => (
                          <div
                            key={hour}
                            className="h-12 border-b border-gray-200"
                          />
                        ))}

                        {/* Assignment Blocks - Positioned Absolutely */}
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

                            // בדוק אם יש פידבק
                            const feedbackStatus = feedbackGiven[assignment.id];
                            const hasFeedback = feedbackStatus === 'approved' || feedbackStatus === 'rejected';
                            const isSelectedForSwap = selectedForSwap && selectedForSwap.id === assignment.id;
                            // מסגרת רק למשימה שנבחרה להחלפה, לא לפידבק
                            const feedbackClass = isSelectedForSwap
                              ? 'ring-4 ring-yellow-500 shadow-yellow-500/50 animate-pulse'
                              : '';

                            return (
                              <div
                                key={assignment.id}
                                className={`absolute rounded-lg shadow-md overflow-visible group hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] transform border pointer-events-auto ${feedbackClass}`}
                                style={{
                                  top: `calc(${topPosition}% + 2px)`,
                                  height: `calc(${height}% - 4px)`,
                                  left: '6px',
                                  right: '6px',
                                  // רקע רגיל ללא שינוי צבע לפי פידבק
                                  background: `linear-gradient(135deg, ${assignmentColor} 0%, ${assignmentColor}dd 100%)`,
                                  borderColor: assignmentColor,
                                }}
                                onClick={() => (user.role === 'מפ' || user.role === 'ממ') && openEditAssignmentModal(assignment)}
                                title={`${assignment.name} (${startHour.toString().padStart(2, '0')}:00 - ${endHour.toString().padStart(2, '0')}:00)`}
                              >
                                {/* Feedback Status Badge - Top Right Corner */}
                                {hasFeedback && (
                                  <div className="absolute -top-2 -right-2 z-20 pointer-events-none">
                                    {feedbackStatus === 'approved' ? (
                                      <div className="bg-gradient-to-br from-green-400 to-emerald-600 text-white p-1 rounded-full shadow-lg animate-scale-in">
                                        <CheckCircle2 className="w-4 h-4" />
                                      </div>
                                    ) : (
                                      <div className="bg-gradient-to-br from-red-400 to-rose-600 text-white p-1 rounded-full shadow-lg animate-scale-in">
                                        <XCircle className="w-4 h-4" />
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Assignment Content */}
                                <div className="p-2 h-full flex flex-col text-white backdrop-blur-sm relative overflow-y-auto">
                                  {/* Edit Icon */}
                                  {(user.role === 'מפ' || user.role === 'ממ') && (
                                    <div className="absolute top-1 right-1 bg-white/30 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
                                      <Edit className="w-3 h-3" />
                                    </div>
                                  )}

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

                                  {/* Feedback Buttons - תמיד גלויים לכל המשתמשים המורשים */}
                                  {(user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ') && (
                                    <div className="absolute top-1 left-1 z-10 flex gap-1 pointer-events-auto">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleFeedback(assignment.id, 'approved');
                                        }}
                                        className={`bg-gradient-to-br hover:from-green-500 hover:to-emerald-700 text-white p-1.5 rounded-full shadow-lg transition-all duration-200 hover:scale-110 transform ${
                                          feedbackStatus === 'approved'
                                            ? 'from-green-500 to-emerald-700 ring-2 ring-white'
                                            : 'from-green-400 to-emerald-600'
                                        }`}
                                        title={feedbackStatus === 'approved' ? 'שיבוץ מאושר - לחץ שוב לביטול' : 'אישור שיבוץ - המערכת תלמד מהפידבק'}
                                      >
                                        <ThumbsUp className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleFeedback(assignment.id, 'rejected');
                                        }}
                                        className={`bg-gradient-to-br hover:from-red-500 hover:to-rose-700 text-white p-1.5 rounded-full shadow-lg transition-all duration-200 hover:scale-110 transform ${
                                          feedbackStatus === 'rejected'
                                            ? 'from-red-500 to-rose-700 ring-2 ring-white'
                                            : 'from-red-400 to-rose-600'
                                        }`}
                                        title={feedbackStatus === 'rejected' ? 'שיבוץ נדחה - לחץ שוב לביטול' : 'דחיית שיבוץ - המערכת תלמד מהפידבק'}
                                      >
                                        <ThumbsDown className="w-3.5 h-3.5" />
                                      </button>
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
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                );
              })()}
            </div>
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

export default LiveSchedule;
