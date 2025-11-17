import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Calendar, ChevronLeft, ChevronRight, Clock, Users,
  RefreshCw, Brain, ThumbsUp, ThumbsDown, Upload,
  AlertTriangle, TrendingUp, Award, Zap
} from 'lucide-react';
import { toast } from 'react-toastify';

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

      // נסה למצוא את שיבוץ ה-ID אם יש
      if (response.data.schedules && response.data.schedules.length > 0) {
        setCurrentShavzakId(response.data.schedules[0].id);
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בטעינת שיבוץ');
      console.error('Load schedule error:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateSmartSchedule = async () => {
    if (!window.confirm('האם אתה בטוח שברצונך ליצור שיבוץ חכם עם AI? זה עשוי לקחת כמה שניות.')) {
      return;
    }

    setIsGenerating(true);
    try {
      const startDate = new Date(currentDate);
      startDate.setDate(startDate.getDate() - currentDate.getDay()); // תחילת שבוע

      const response = await api.post('/ml/smart-schedule', {
        pluga_id: user.pluga_id,
        start_date: startDate.toISOString().split('T')[0],
        days_count: 7
      });

      // הצג מידע על משימות שלא הצליחו
      if (response.data.failed_assignments && response.data.failed_assignments.length > 0) {
        toast.warning(`⚠️ ${response.data.message} - ${response.data.success_rate} הצליחו`);
      } else {
        toast.success(`🤖 ${response.data.message}`);
      }

      loadSchedule(currentDate);
      loadMLStats();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת שיבוץ חכם');
      console.error('Smart schedule error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFeedback = async (assignmentId, rating) => {
    try {
      const response = await api.post('/ml/feedback', {
        assignment_id: assignmentId,
        shavzak_id: currentShavzakId,
        rating: rating,
        enable_auto_regeneration: true
      });

      // הצג הודעה מהשרת
      toast.success(response.data.message);

      // בדוק אם צריך ליצור שיבוץ חדש
      if (response.data.needs_regeneration && rating === 'rejected') {
        toast.info('🔄 יוצר שיבוץ חדש משופר...', { autoClose: 3000 });

        // המתן קצר ואז צור שיבוץ חדש
        setTimeout(async () => {
          try {
            const regenerateResponse = await api.post('/ml/regenerate-schedule', {
              shavzak_id: currentShavzakId,
              reason: 'פידבק שלילי - יצירת שיבוץ משופר'
            });

            toast.success(regenerateResponse.data.message);

            // הצג מידע על איטרציה
            setIterationInfo({
              number: regenerateResponse.data.iteration_number,
              successRate: regenerateResponse.data.success_rate
            });

            // רענן את השיבוץ
            loadSchedule(currentDate);
            loadMLStats();
          } catch (error) {
            toast.error('שגיאה ביצירת שיבוץ חדש');
            console.error('Regenerate error:', error);
          }
        }, 1500);
      } else {
        loadMLStats();
      }
    } catch (error) {
      toast.error('שגיאה בשמירת פידבק');
      console.error('Feedback error:', error);
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
      return '#9CA3AF'; // אפור למשימות ללא חיילים
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

    // ברירת מחדל
    return '#9CA3AF';
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
      <div className="card bg-gradient-to-br from-purple-600 via-blue-600 to-indigo-700 text-white shadow-2xl border-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="bg-white bg-opacity-20 p-3 rounded-2xl backdrop-blur-sm">
              <Brain className="w-12 h-12 animate-pulse" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <h1 className="text-4xl font-bold tracking-tight">שיבוץ חכם AI</h1>
                <span className="bg-green-500 text-white text-xs px-3 py-1 rounded-full font-bold animate-pulse flex items-center gap-1">
                  <Zap size={12} />
                  POWERED BY ML
                </span>
              </div>
              <p className="text-purple-100 text-lg font-medium">למידת מכונה - משתפר עם הזמן</p>
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

          {/* Actions */}
          <div className="flex items-center gap-2 mr-4">
            {(user.role === 'מפ' || user.role === 'ממ') && (
              <>
                <button
                  onClick={generateSmartSchedule}
                  disabled={isGenerating}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 py-2 rounded-lg transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
                  title="יצירת שיבוץ חכם עם AI"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={20} className="animate-spin" />
                      <span>מייצר...</span>
                    </>
                  ) : (
                    <>
                      <Brain size={20} />
                      <span>שיבוץ AI</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title="העלה דוגמאות שיבוץ"
                >
                  <Upload size={24} />
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
          {(user.role === 'מפ' || user.role === 'ממ') && (
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
            <div className="overflow-x-auto">
              {(() => {
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

                const hours = Array.from({ length: 24 }, (_, i) => i);

                return (
                  <div className="min-w-max">
                    {/* Header */}
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

                              return (
                                <div
                                  key={assignment.id}
                                  className="absolute rounded-lg shadow-md overflow-hidden group cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] transform border"
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
                                    {/* Feedback Buttons */}
                                    {(user.role === 'מפ' || user.role === 'ממ') && (
                                      <div className="absolute top-1 left-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleFeedback(assignment.id, 'approved');
                                          }}
                                          className="bg-green-500 hover:bg-green-600 rounded p-1 text-white"
                                          title="שיבוץ מעולה"
                                        >
                                          <ThumbsUp size={14} />
                                        </button>
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleFeedback(assignment.id, 'rejected');
                                          }}
                                          className="bg-red-500 hover:bg-red-600 rounded p-1 text-white"
                                          title="שיבוץ לא טוב"
                                        >
                                          <ThumbsDown size={14} />
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
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

export default SmartSchedule;
