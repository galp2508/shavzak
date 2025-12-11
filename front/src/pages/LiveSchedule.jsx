import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useDitto } from '../context/DittoContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight, Clock, Users, RefreshCw, Shield, AlertTriangle, Trash2, Plus, Edit, Brain, ThumbsUp, ThumbsDown, Sparkles, CheckCircle2, XCircle, TrendingUp, Award, Zap, ArrowLeftRight, Download, ZoomIn, ZoomOut, Eraser, LayoutList, Grid, Maximize2, Minimize2 } from 'lucide-react';
import { toast } from 'react-toastify';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, horizontalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import html2canvas from 'html2canvas';
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

const LiveSchedule = () => {
  const { user } = useAuth();
  const { ditto } = useDitto();
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
  const [selectedSoldierForSwap, setSelectedSoldierForSwap] = useState(null); // חייל שנבחר להחלפה { soldier, assignment }
  const [isAutoGenerating, setIsAutoGenerating] = useState(false); // מצב יצירה אוטומטית - למניעת לולאות
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackAssignmentId, setFeedbackAssignmentId] = useState(null);
  const [columnOrder, setColumnOrder] = useState(() => {
    const savedOrder = localStorage.getItem('shavzakColumnOrder');
    return savedOrder ? JSON.parse(savedOrder) : [];
  });
  const [zoomLevel, setZoomLevel] = useState(1);
  const [viewMode, setViewMode] = useState(window.innerWidth < 768 ? 'list' : 'grid');
  const [touchStartDist, setTouchStartDist] = useState(null);
  const [touchStartZoom, setTouchStartZoom] = useState(1);
  const [showStats, setShowStats] = useState(window.innerWidth >= 768);
  const [isFullScreen, setIsFullScreen] = useState(false);

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

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullScreen(true);
      }).catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().then(() => {
          setIsFullScreen(false);
        });
      }
    }
  };

  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullScreenChange);
  }, []);

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      setColumnOrder((items) => {
        const oldIndex = items.indexOf(active.id);
        const newIndex = items.indexOf(over.id);
        const newOrder = arrayMove(items, oldIndex, newIndex);
        localStorage.setItem('shavzakColumnOrder', JSON.stringify(newOrder));
        return newOrder;
      });
    }
  };

  const deleteDaySchedule = async () => {
    if (!currentDate) return;
    
    if (!window.confirm('האם אתה בטוח שברצונך למחוק את כל השיבוצים ליום זה? פעולה זו אינה הפיכה.')) {
      return;
    }

    try {
      setLoading(true);
      const dateStr = currentDate.toISOString().split('T')[0];
      await api.delete(`/plugot/${user.pluga_id}/live-schedule/days/${dateStr}`);
      toast.success('השיבוץ ליום זה נמחק בהצלחה');
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error deleting day schedule:', error);
      toast.error('שגיאה במחיקת השיבוץ');
    } finally {
      setLoading(false);
    }
  };

  const clearDaySoldiers = async () => {
    if (!currentDate) return;
    
    if (!window.confirm('האם אתה בטוח שברצונך לנקות את כל החיילים מהשיבוץ ליום זה? המשימות יישארו ריקות.')) {
      return;
    }

    try {
      setLoading(true);
      const dateStr = currentDate.toISOString().split('T')[0];
      await api.post(`/plugot/${user.pluga_id}/live-schedule/days/${dateStr}/clear-soldiers`);
      toast.success('החיילים נוקו מהשיבוץ בהצלחה');
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error clearing day soldiers:', error);
      toast.error('שגיאה בניקוי החיילים מהשיבוץ');
    } finally {
      setLoading(false);
    }
  };

  const handleExportImage = async () => {
    const element = document.getElementById('schedule-grid');
    if (!element) return;

    try {
      // Clone the element to capture full content
      const clone = element.cloneNode(true);
      
      // Reset zoom on clone for export
      const innerDiv = clone.querySelector('.min-w-max');
      if (innerDiv) {
        innerDiv.style.zoom = '1';
      }

      clone.style.width = 'fit-content';
      clone.style.height = 'auto';
      clone.style.overflow = 'visible';
      clone.style.position = 'absolute';
      clone.style.top = '-9999px';
      clone.style.left = '-9999px';
      document.body.appendChild(clone);

      const canvas = await html2canvas(clone, {
        scale: 2, // Higher quality
        useCORS: true,
        backgroundColor: '#ffffff',
        windowWidth: clone.scrollWidth,
        windowHeight: clone.scrollHeight
      });
      
      document.body.removeChild(clone);
      
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

  useEffect(() => {
    if (scheduleData?.assignments) {
      const uniqueNames = [...new Set(scheduleData.assignments.map(a => a.name))].sort();
      setColumnOrder(prev => {
        // אם אין סדר קודם, החזר את המיון האלפביתי
        if (prev.length === 0) return uniqueNames;

        // שמור על הסדר הקיים, הוסף חדשים בסוף
        const newItems = uniqueNames.filter(n => !prev.includes(n));
        const existingItems = prev.filter(n => uniqueNames.includes(n));
        return [...existingItems, ...newItems];
      });
    }
  }, [scheduleData]);

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

  // Ditto Live Sync
  useEffect(() => {
    if (!ditto || !currentDate) return;

    console.log("🔌 Subscribing to Ditto changes...");
    
    const subscription = ditto.store.collection("assignments").find("true").subscribe();
    
    const observer = ditto.store.collection("assignments").find("true").observeLocal((docs, event) => {
      // When data changes in Ditto (from other devices), reload the schedule
      console.log("🔄 Ditto update received!", event);
      loadSchedule(currentDate);
    });

    return () => {
      subscription.cancel();
      observer.stop();
    };
  }, [ditto, currentDate]);

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

  // טיפול במקלדת - חצים וקיצורים
  useEffect(() => {
    const handleKeyDown = (e) => {
      // בדוק אם המשתמש בתוך input/textarea - אז לא להפעיל קיצורים
      const isTyping = ['INPUT', 'TEXTAREA'].includes(e.target.tagName);
      if (isTyping) return;

      // ניווט בימים
      if (e.key === 'ArrowRight') {
        navigateDay(-1); // ימינה = אתמול (RTL)
      } else if (e.key === 'ArrowLeft') {
        navigateDay(1); // שמאלה = מחר (RTL)
      }
      // T = Today (חזור להיום)
      else if (e.key.toLowerCase() === 't') {
        const today = new Date();
        setCurrentDate(today);
      }
      // R = Refresh
      else if (e.key.toLowerCase() === 'r' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        loadSchedule(currentDate);
      }
      // G = Generate smart schedule (רק למפקדים)
      else if (e.key.toLowerCase() === 'g' && (user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ')) {
        e.preventDefault();
        generateSmartSchedule();
      }
      // N = New assignment (רק למפקדים)
      else if (e.key.toLowerCase() === 'n' && (user?.role === 'מפ' || user?.role === 'ממ')) {
        e.preventDefault();
        openNewAssignmentModal();
      }
      // C = Constraints (רק למפקדים)
      else if (e.key.toLowerCase() === 'c' && (user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ')) {
        e.preventDefault();
        setShowConstraints(true);
      }
      // Escape = Cancel swap selection
      else if (e.key === 'Escape' && selectedForSwap) {
        setSelectedForSwap(null);
        toast.info('בחירת החלפה בוטלה', { icon: '❌' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentDate, selectedForSwap, user]);

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

  // חישוב סטטיסטיקות היום
  const calculateDayStats = () => {
    if (!scheduleData || !scheduleData.assignments) {
      return {
        totalAssignments: 0,
        totalSoldiers: 0,
        avgWorkload: 0,
        lowConfidenceCount: 0,
        approvedCount: 0,
        rejectedCount: 0
      };
    }

    const assignments = scheduleData.assignments;
    const soldiersSet = new Set();
    let lowConfidenceCount = 0;
    let approvedCount = 0;
    let rejectedCount = 0;

    assignments.forEach(assignment => {
      // ספור חיילים ייחודיים
      if (assignment.soldiers) {
        assignment.soldiers.forEach(s => soldiersSet.add(s.id));
      }

      // בדוק ביטחון
      const { level } = calculateAssignmentConfidence(assignment);
      if (level === 'נמוך') lowConfidenceCount++;

      // בדוק פידבק
      const feedbackStatus = feedbackGiven[assignment.id];
      if (feedbackStatus === 'approved') approvedCount++;
      if (feedbackStatus === 'rejected') rejectedCount++;
    });

    // חשב ממוצע עומס
    let totalWorkload = 0;
    soldiersSet.forEach(soldierId => {
      totalWorkload += calculateSoldierWorkload(soldierId);
    });
    const avgWorkload = soldiersSet.size > 0 ? Math.round(totalWorkload / soldiersSet.size) : 0;

    return {
      totalAssignments: assignments.length,
      totalSoldiers: soldiersSet.size,
      avgWorkload,
      lowConfidenceCount,
      approvedCount,
      rejectedCount
    };
  };

  // חישוב עומס שעות לחייל
  const calculateSoldierWorkload = (soldierId) => {
    if (!scheduleData || !scheduleData.assignments) return 0;

    let totalHours = 0;
    scheduleData.assignments.forEach(assignment => {
      if (assignment.soldiers) {
        const isSoldierInAssignment = assignment.soldiers.some(s => s.id === soldierId);
        if (isSoldierInAssignment) {
          totalHours += assignment.length_in_hours || 0;
        }
      }
    });

    return totalHours;
  };

  // חישוב רמת ביטחון למשימה
  const calculateAssignmentConfidence = (assignment) => {
    let confidence = 1.0; // התחל עם ביטחון מלא
    const reasons = [];

    // 1. בדוק אם יש חיילים במשימה
    if (!assignment.soldiers || assignment.soldiers.length === 0) {
      confidence *= 0.3;
      reasons.push('אין חיילים משובצים');
      return { confidence, reasons, level: 'נמוך' };
    }

    // 2. בדוק אם המשימה נדחתה בעבר
    const feedbackStatus = feedbackGiven[assignment.id];
    if (feedbackStatus === 'rejected') {
      confidence *= 0.4;
      reasons.push('נדחתה בעבר');
    }

    // 3. בדוק אם יש הרבה חיילים חדשים (ללא תפקיד מוגדר)
    const newSoldiers = assignment.soldiers.filter(s => !s.role || s.role === 'חייל');
    if (newSoldiers.length === assignment.soldiers.length) {
      confidence *= 0.7;
      reasons.push('כל החיילים חדשים');
    }

    // 4. בדוק אם חסרים מפקדים למשימות שצריכות
    const needsCommander = ['סיור', 'כוננות א'].includes(assignment.assignment_type);
    const hasCommander = assignment.soldiers.some(s => ['מכ', 'ממ', 'סמל'].includes(s.role));
    if (needsCommander && !hasCommander) {
      confidence *= 0.5;
      reasons.push('חסר מפקד');
    }

    // 5. בדוק אם משימה במשמרת לילה
    if (assignment.start_hour >= 22 || assignment.start_hour <= 6) {
      confidence *= 0.9; // הורד מעט - משמרות לילה קשות יותר
    }

    // קבע רמת ביטחון
    let level = 'גבוה';
    if (confidence < 0.5) level = 'נמוך';
    else if (confidence < 0.75) level = 'בינוני';

    return { confidence, reasons, level };
  };

  const loadSchedule = async (date, skipAutoGenerate = false) => {
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

      if (!skipAutoGenerate && response.data.assignments && response.data.assignments.length === 0 && checkDate >= today && !isAutoGenerating) {
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
    // מנע קריאות מקבילות - אם כבר בתהליך יצירה, צא
    if (isAutoGenerating) {
      console.log('⏳ כבר בתהליך יצירה אוטומטית - מדלג');
      return;
    }

    setIsAutoGenerating(true);
    try {
      console.log('🤖 בונה שיבוץ אוטומטי ליומיים קדימה...');
      const response = await api.post('/ml/smart-schedule', {
        pluga_id: user.pluga_id,
        start_date: startDate.toISOString().split('T')[0],
        days_count: 2
      });

      // רענן את התצוגה בשקט (בלי הודעה) - דלג על יצירה אוטומטית נוספת
      if (response.data) {
        await loadSchedule(currentDate, true);
        console.log('✅ שיבוץ אוטומטי הושלם');
      }
    } catch (error) {
      console.error('שגיאה בשיבוץ אוטומטי:', error);
      // לא מציגים שגיאה למשתמש - זה רק ניסיון אוטומטי
    } finally {
      setIsAutoGenerating(false);
    }
  };

  const navigateDay = (days) => {
    setCurrentDate(prevDate => {
      const newDate = new Date(prevDate);
      newDate.setDate(newDate.getDate() + days);
      return newDate;
    });
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

      // טען את השיבוץ החדש - דלג על יצירה אוטומטית נוספת
      loadSchedule(currentDate, true);
      loadMLStats(); // עדכן סטטיסטיקות ML
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת שיבוץ חכם');
      console.error('Smart schedule error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFeedback = async (assignmentId, rating, reason = null, alternative = null) => {
    try {
      // אם זה דחייה ואין סיבה, פתח מודל
      if (rating === 'rejected' && !reason) {
        setFeedbackAssignmentId(assignmentId);
        setShowFeedbackModal(true);
        return;
      }

      // מצא את ה-shavzak_id (שיבוץ אוטומטי)
      const shavzakId = scheduleData?.shavzak_id;
      if (!shavzakId) {
        toast.error('לא נמצא מזהה שיבוץ');
        return;
      }

      const feedbackData = {
        assignment_id: assignmentId,
        shavzak_id: shavzakId,
        rating: rating,
        enable_auto_regeneration: false  // לא לרענן אוטומטית בשיבוץ חי
      };

      if (reason) {
        feedbackData.changes = { 
          feedback_text: reason,
          alternative_suggestion: alternative
        };
      }

      await api.post('/ml/feedback', feedbackData);

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
        // נסה לשבץ מחדש אוטומטית
        toast.info('🔄 מנסה למצוא שיבוץ טוב יותר...', { autoClose: 2000 });
        
        try {
            const regenResponse = await api.post('/ml/regenerate-assignment', { assignment_id: assignmentId });
            
            if (regenResponse.data.assignment) {
                toast.success('✅ נמצא שיבוץ חלופי!', { icon: '🤖' });
                
                // עדכן את המשימה ב-state המקומי
                setScheduleData(prev => {
                    if (!prev) return prev;
                    const newAssignments = prev.assignments.map(a => 
                        a.id === assignmentId 
                        ? { ...a, ...regenResponse.data.assignment } // עדכן שדות רלוונטיים
                        : a
                    );
                    return { ...prev, assignments: newAssignments };
                });
            }
        } catch (regenError) {
            console.error('Regeneration error:', regenError);
            toast.warning('לא נמצא שיבוץ חלופי אוטומטי - נסה לערוך ידנית', { autoClose: 5000 });
        }
      }

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
    const nonDriverSoldiers = soldiers.filter(s => s.role_in_assignment !== 'נהג');

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

  // Soldier Swap handler - החלפה בין חיילים
  const handleSoldierSwapClick = (soldier, assignment, e) => {
    e.stopPropagation();
    
    if (!selectedSoldierForSwap) {
      // Select first soldier
      setSelectedSoldierForSwap({ soldier, assignment });
      toast.info(`נבחר חייל: ${soldier.name}. לחץ על חייל אחר להחלפה`, {
        autoClose: 3000,
        icon: '🔄'
      });
    } else if (selectedSoldierForSwap.soldier.id === soldier.id) {
      // Deselect
      setSelectedSoldierForSwap(null);
      toast.info('הבחירה בוטלה', { icon: '❌' });
    } else {
      // Swap
      swapSoldiers(selectedSoldierForSwap, { soldier, assignment });
    }
  };

  const swapSoldiers = async (source, target) => {
    try {
      // We need to update both assignments with the swapped soldiers
      // 1. Remove source soldier from source assignment and add target soldier
      // 2. Remove target soldier from target assignment and add source soldier
      
      // Prepare updated soldiers list for source assignment
      const sourceSoldiers = source.assignment.soldiers.map(s => 
        s.id === source.soldier.id ? { ...target.soldier, role: source.soldier.role_in_assignment } : s
      );
      
      // Prepare updated soldiers list for target assignment
      const targetSoldiers = target.assignment.soldiers.map(s => 
        s.id === target.soldier.id ? { ...source.soldier, role: target.soldier.role_in_assignment } : s
      );

      // If assignments are the same (swapping roles within same assignment)
      if (source.assignment.id === target.assignment.id) {
         // Just one update
         // Actually the map above handles it but we need to be careful not to duplicate
         // If same assignment, sourceSoldiers and targetSoldiers are derived from same list
         // We should just swap in one list
         const newSoldiers = source.assignment.soldiers.map(s => {
             if (s.id === source.soldier.id) return { ...target.soldier, role: source.soldier.role_in_assignment };
             if (s.id === target.soldier.id) return { ...source.soldier, role: target.soldier.role_in_assignment };
             return s;
         });
         
         await api.put(`/assignments/${source.assignment.id}/soldiers`, {
             soldiers: newSoldiers.map(s => ({ soldier_id: s.id, role: s.role }))
         });
      } else {
          // Two updates
          await Promise.all([
              api.put(`/assignments/${source.assignment.id}/soldiers`, {
                  soldiers: sourceSoldiers.map(s => ({ soldier_id: s.id, role: s.role_in_assignment || 'חייל' }))
              }),
              api.put(`/assignments/${target.assignment.id}/soldiers`, {
                  soldiers: targetSoldiers.map(s => ({ soldier_id: s.id, role: s.role_in_assignment || 'חייל' }))
              })
          ]);
      }

      toast.success('החיילים הוחלפו בהצלחה! 🔄', { icon: '✅' });
      setSelectedSoldierForSwap(null);
      loadSchedule(currentDate);
    } catch (error) {
      console.error('Error swapping soldiers:', error);
      toast.error('שגיאה בהחלפת החיילים');
      setSelectedSoldierForSwap(null);
    }
  };

  // Pinch to Zoom Handlers
  const handleTouchStart = (e) => {
    if (e.touches.length === 2) {
      const dist = Math.hypot(
        e.touches[0].pageX - e.touches[1].pageX,
        e.touches[0].pageY - e.touches[1].pageY
      );
      setTouchStartDist(dist);
      setTouchStartZoom(zoomLevel);
    }
  };

  const handleTouchMove = (e) => {
    if (e.touches.length === 2 && touchStartDist) {
      const dist = Math.hypot(
        e.touches[0].pageX - e.touches[1].pageX,
        e.touches[0].pageY - e.touches[1].pageY
      );
      const scale = dist / touchStartDist;
      // Limit zoom between 0.5 and 2.0
      setZoomLevel(Math.min(Math.max(touchStartZoom * scale, 0.5), 2.0));
    }
  };

  const handleTouchEnd = () => {
    setTouchStartDist(null);
  };

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.1, 2.0));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.1, 0.5));

  if (loading && !scheduleData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 md:space-y-6 ${isFullScreen ? 'fixed inset-0 z-[100] bg-gray-100 overflow-auto p-2' : ''}`}>
      {/* Header with Date Navigation */}
      <div className="card bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white shadow-2xl border-none p-3 md:p-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 md:gap-4">
          <div className="flex items-center justify-between w-full md:w-auto">
            <div className="flex items-center gap-3">
                <div className="bg-white bg-opacity-20 p-2 md:p-3 rounded-2xl backdrop-blur-sm animate-pulse-slow hidden md:block">
                <Calendar className="w-8 h-8 md:w-12 md:h-12" />
                </div>
                <div className="text-right">
                <div className="flex items-center gap-2">
                    <h1 className="text-xl md:text-4xl font-bold tracking-tight">שיבוץ חי</h1>
                    <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-[10px] md:text-xs px-2 py-0.5 md:px-3 md:py-1 rounded-full font-bold animate-pulse flex items-center gap-1">
                    <Sparkles size={10} className="md:w-3 md:h-3" />
                    LIVE
                    </span>
                </div>
                <p className="text-purple-100 text-sm md:text-lg font-medium hidden md:block">ניווט אוטומטי בין ימים • למידת מכונה פעילה</p>
                </div>
            </div>
            
            {/* Mobile Stats Toggle */}
            <button 
                onClick={() => setShowStats(!showStats)}
                className="md:hidden p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors flex items-center gap-1 text-xs font-bold"
            >
                <TrendingUp size={16} />
                {showStats ? 'הסתר נתונים' : 'הצג נתונים'}
            </button>
          </div>

          {/* Date Navigation */}
          <div className="flex items-center justify-between w-full md:w-auto gap-2 md:gap-4 bg-white bg-opacity-20 backdrop-blur-md rounded-xl md:rounded-2xl p-2 md:p-4 shadow-lg">
            <button
              onClick={() => navigateDay(-1)}
              className="p-1.5 md:p-3 hover:bg-white hover:bg-opacity-30 rounded-lg md:rounded-xl transition-all duration-300 active:scale-95 md:hover:scale-110 transform"
              title="יום קודם"
            >
              <ChevronRight size={20} className="md:w-7 md:h-7" />
            </button>

            <div className="text-center min-w-[100px] md:min-w-[220px]">
              <div className="text-lg md:text-3xl font-bold tracking-wide">
                {currentDate && getDayName(currentDate)}
              </div>
              <div className="text-xs md:text-base opacity-90 font-medium mt-0.5 md:mt-1">
                {currentDate && currentDate.toLocaleDateString('he-IL')}
              </div>
            </div>

            <button
              onClick={() => navigateDay(1)}
              className="p-1.5 md:p-3 hover:bg-white hover:bg-opacity-30 rounded-lg md:rounded-xl transition-all duration-300 active:scale-95 md:hover:scale-110 transform"
              title="יום הבא"
            >
              <ChevronLeft size={20} className="md:w-7 md:h-7" />
            </button>
          </div>

          <div className="flex items-center justify-center gap-2 w-full md:w-auto flex-wrap">
            {(user.role === 'מפ' || user.role === 'ממ' || user.role === 'מכ') && (
              <>
                <button
                  onClick={generateSmartSchedule}
                  disabled={isGenerating}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-3 py-1.5 md:py-2 rounded-lg transition-all flex items-center gap-2 shadow-lg disabled:opacity-50 text-xs md:text-base flex-1 md:flex-none justify-center"
                  title="יצירת שיבוץ חכם עם AI"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={16} className="animate-spin md:w-[18px] md:h-[18px]" />
                      <span className="inline">מייצר...</span>
                    </>
                  ) : (
                    <>
                      <Brain size={16} className="md:w-[18px] md:h-[18px]" />
                      <span className="inline">שיבוץ AI</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowConstraints(true)}
                  className="p-1.5 md:p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title="אילוצי שיבוץ"
                >
                  <Shield size={18} className="md:w-6 md:h-6" />
                </button>
                <button
                  onClick={handleExportImage}
                  className="p-1.5 md:p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title="ייצא לתמונה"
                >
                  <Download size={18} className="md:w-6 md:h-6" />
                </button>
                <button
                  onClick={toggleFullScreen}
                  className="p-1.5 md:p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                  title={isFullScreen ? "צא ממסך מלא" : "מסך מלא"}
                >
                  {isFullScreen ? (
                    <Minimize2 size={18} className="md:w-6 md:h-6" />
                  ) : (
                    <Maximize2 size={18} className="md:w-6 md:h-6" />
                  )}
                </button>
                <button
                  onClick={clearDaySoldiers}
                  className="p-1.5 md:p-2 hover:bg-orange-500 hover:bg-opacity-20 text-orange-200 hover:text-orange-100 rounded-lg transition-colors"
                  title="נקה חיילים (השאר משימות)"
                >
                  <Eraser size={18} className="md:w-6 md:h-6" />
                </button>
                <button
                  onClick={deleteDaySchedule}
                  className="p-2 hover:bg-red-500 hover:bg-opacity-20 text-red-600 hover:text-red-700 rounded-lg transition-colors"
                  title="מחק שיבוץ ליום זה"
                >
                  <Trash2 size={20} className="md:w-6 md:h-6" />
                </button>
              </>
            )}
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

      {/* Stats Section - Collapsible on Mobile */}
      {showStats && (
        <div className="space-y-4 md:space-y-6 animate-fadeIn">
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

      {/* Mini Dashboard - סטטיסטיקות יומיות */}
      {scheduleData?.assignments && scheduleData.assignments.length > 0 && (
        <div className="card bg-gradient-to-br from-slate-50 via-gray-50 to-zinc-50 border-2 border-slate-300 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-gradient-to-br from-slate-600 to-gray-700 p-2 rounded-full">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800">סטטיסטיקות היום</h3>
              <p className="text-xs text-gray-600">סיכום מהיר של השיבוץ</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {(() => {
              const stats = calculateDayStats();
              return (
                <>
                  {/* Total Assignments */}
                  <div className="bg-white p-3 rounded-lg border-2 border-blue-200 hover:border-blue-400 transition-all hover:shadow-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Calendar className="w-4 h-4 text-blue-600" />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        משימות
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-blue-700">{stats.totalAssignments}</div>
                  </div>

                  {/* Total Soldiers */}
                  <div className="bg-white p-3 rounded-lg border-2 border-purple-200 hover:border-purple-400 transition-all hover:shadow-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Users className="w-4 h-4 text-purple-600" />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        חיילים
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-purple-700">{stats.totalSoldiers}</div>
                  </div>

                  {/* Average Workload */}
                  <div className="bg-white p-3 rounded-lg border-2 border-indigo-200 hover:border-indigo-400 transition-all hover:shadow-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-indigo-600" />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        ממוצע שעות
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-indigo-700">{stats.avgWorkload}ש'</div>
                  </div>

                  {/* Low Confidence Warnings */}
                  <div className={`bg-white p-3 rounded-lg border-2 transition-all hover:shadow-md ${
                    stats.lowConfidenceCount > 0
                      ? 'border-yellow-300 hover:border-yellow-500 animate-pulse-slow'
                      : 'border-gray-200 hover:border-gray-400'
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className={`w-4 h-4 ${stats.lowConfidenceCount > 0 ? 'text-yellow-600' : 'text-gray-400'}`} />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        אזהרות
                      </div>
                    </div>
                    <div className={`text-2xl font-bold ${stats.lowConfidenceCount > 0 ? 'text-yellow-700' : 'text-gray-400'}`}>
                      {stats.lowConfidenceCount}
                    </div>
                  </div>

                  {/* Approved */}
                  <div className="bg-white p-3 rounded-lg border-2 border-green-200 hover:border-green-400 transition-all hover:shadow-md">
                    <div className="flex items-center gap-2 mb-1">
                      <ThumbsUp className="w-4 h-4 text-green-600" />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        אושרו
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-green-700">{stats.approvedCount}</div>
                  </div>

                  {/* Rejected */}
                  <div className="bg-white p-3 rounded-lg border-2 border-red-200 hover:border-red-400 transition-all hover:shadow-md">
                    <div className="flex items-center gap-2 mb-1">
                      <ThumbsDown className="w-4 h-4 text-red-600" />
                      <div className="text-xs text-gray-500 font-medium mb-1">
                        נדחו
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-red-700">{stats.rejectedCount}</div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500 shadow-md">
        <div className="flex items-center gap-3 mb-3">
          <kbd className="px-3 py-2 bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-lg text-sm font-bold shadow-md">⌨️</kbd>
          <div>
            <h3 className="text-sm font-bold text-gray-800">קיצורי מקלדת</h3>
            <p className="text-xs text-gray-600">לניווט ופעולות מהירות</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 text-sm">
          <div className="flex items-center gap-2 text-blue-700">
            <kbd className="px-2 py-1 bg-white border-2 border-blue-300 rounded text-xs font-bold">←</kbd>
            <span className="text-xs">יום הבא</span>
          </div>
          <div className="flex items-center gap-2 text-blue-700">
            <kbd className="px-2 py-1 bg-white border-2 border-blue-300 rounded text-xs font-bold">→</kbd>
            <span className="text-xs">יום קודם</span>
          </div>
          <div className="flex items-center gap-2 text-green-700">
            <kbd className="px-2 py-1 bg-white border-2 border-green-300 rounded text-xs font-bold">T</kbd>
            <span className="text-xs">חזור להיום</span>
          </div>
          <div className="flex items-center gap-2 text-purple-700">
            <kbd className="px-2 py-1 bg-white border-2 border-purple-300 rounded text-xs font-bold">R</kbd>
            <span className="text-xs">רענן</span>
          </div>
          {(user?.role === 'מפ' || user?.role === 'ממ' || user?.role === 'מכ') && (
            <>
              <div className="flex items-center gap-2 text-emerald-700">
                <kbd className="px-2 py-1 bg-white border-2 border-emerald-300 rounded text-xs font-bold">G</kbd>
                <span className="text-xs">שיבוץ AI</span>
              </div>
              <div className="flex items-center gap-2 text-orange-700">
                <kbd className="px-2 py-1 bg-white border-2 border-orange-300 rounded text-xs font-bold">C</kbd>
                <span className="text-xs">אילוצים</span>
              </div>
            </>
          )}
          {(user?.role === 'מפ' || user?.role === 'ממ') && (
            <div className="flex items-center gap-2 text-indigo-700">
              <kbd className="px-2 py-1 bg-white border-2 border-indigo-300 rounded text-xs font-bold">N</kbd>
              <span className="text-xs">משימה חדשה</span>
            </div>
          )}
          {selectedForSwap && (
            <div className="flex items-center gap-2 text-red-700 animate-pulse">
              <kbd className="px-2 py-1 bg-white border-2 border-red-300 rounded text-xs font-bold">ESC</kbd>
              <span className="text-xs">ביטול החלפה</span>
            </div>
          )}
        </div>
      </div>

        </div>
      )}

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
              
              <div className="flex items-center gap-4">
                {/* View Toggle */}
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-1 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white shadow text-blue-600' : 'hover:bg-white/50 text-gray-500'}`}
                    title="תצוגת רשימה"
                  >
                    <LayoutList size={18} />
                  </button>
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-1 rounded-md transition-colors ${viewMode === 'grid' ? 'bg-white shadow text-blue-600' : 'hover:bg-white/50 text-gray-500'}`}
                    title="תצוגת טבלה"
                  >
                    <Grid size={18} />
                  </button>
                </div>

                {/* Zoom Controls */}
                <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1" dir="ltr">
                  <button 
                    onClick={handleZoomOut}
                    className="p-1 hover:bg-white rounded-md transition-colors disabled:opacity-50"
                    disabled={zoomLevel <= 0.5}
                    title="הקטן תצוגה"
                  >
                    <ZoomOut size={18} />
                  </button>
                  <span className="text-xs font-medium w-10 text-center">
                    {Math.round(zoomLevel * 100)}%
                  </span>
                  <button 
                    onClick={handleZoomIn}
                    className="p-1 hover:bg-white rounded-md transition-colors disabled:opacity-50"
                    disabled={zoomLevel >= 2.0}
                    title="הגדל תצוגה"
                  >
                    <ZoomIn size={18} />
                  </button>
                </div>

                <span className="text-sm text-gray-500 hidden sm:inline">
                  {scheduleData?.assignments?.length} משימות
                </span>
              </div>
            </div>

            {/* Schedule View */}
            {viewMode === 'list' ? (
              <div className="space-y-3">
                {(() => {
                   const sortedAssignments = [...(scheduleData?.assignments || [])].sort((a, b) => {
                     if (a.start_hour !== b.start_hour) return a.start_hour - b.start_hour;
                     return a.name.localeCompare(b.name);
                   });

                   if (sortedAssignments.length === 0) return <div className="text-center text-gray-500 py-8">אין משימות להצגה</div>;

                   return sortedAssignments.map(assignment => {
                     const startHour = assignment.display_start_hour !== undefined ? assignment.display_start_hour : (assignment.start_hour || 0);
                     const lengthInHours = assignment.display_length_in_hours !== undefined ? assignment.display_length_in_hours : (assignment.length_in_hours || 1);
                     const endHour = startHour + lengthInHours;
                     const assignmentColor = getAssignmentColor(assignment);
                     
                     return (
                       <div 
                         key={assignment.id}
                         className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden active:scale-[0.99] transition-transform"
                         onClick={() => (user.role === 'מפ' || user.role === 'ממ') && openEditAssignmentModal(assignment)}
                       >
                         <div className="flex">
                           {/* Color Strip */}
                           <div className="w-2" style={{ backgroundColor: assignmentColor }}></div>
                           
                           <div className="flex-1 p-3">
                             <div className="flex justify-between items-start mb-2">
                               <div>
                                 <h3 className="font-bold text-gray-900">{assignment.name}</h3>
                                 <div className="flex items-center gap-1 text-sm text-gray-500 mt-0.5">
                                   <Clock size={14} />
                                   <span>{startHour.toString().padStart(2, '0')}:00 - {endHour.toString().padStart(2, '0')}:00</span>
                                 </div>
                               </div>
                               {/* Edit Icon for commanders */}
                               {(user.role === 'מפ' || user.role === 'ממ') && (
                                 <Edit size={16} className="text-gray-400" />
                               )}
                             </div>

                             <div className="flex flex-wrap gap-2">
                               {assignment.soldiers && assignment.soldiers.length > 0 ? (
                                 assignment.soldiers.map(soldier => (
                                   <div key={soldier.id} className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md border border-gray-100">
                                     <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-600">
                                       {soldier.name ? soldier.name[0] : '?'}
                                     </div>
                                     <span className="text-sm text-gray-700">{soldier.name}</span>
                                   </div>
                                 ))
                               ) : (
                                 <span className="text-sm text-red-400 italic flex items-center gap-1">
                                   <AlertTriangle size={14} />
                                   ללא חיילים
                                 </span>
                               )}
                             </div>
                           </div>
                         </div>
                       </div>
                     );
                   });
                })()}
              </div>
            ) : (
            /* Time Grid Schedule */
            <div 
              className="overflow-x-auto touch-pan-x touch-pan-y" 
              id="schedule-grid"
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
            >
              {(() => {
                // Use columnOrder if available, otherwise fallback to sorted names
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

                // יצירת 24 שעות
                const hours = Array.from({ length: 24 }, (_, i) => i);

              return (
                <DndContext 
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                <div className="min-w-max" style={{ zoom: zoomLevel }}>
                  {/* Header - שמות תבניות */}
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
                            // Use display values if available (for multi-day support), otherwise fallback to original
                            const startHour = assignment.display_start_hour !== undefined ? assignment.display_start_hour : (assignment.start_hour || 0);
                            const lengthInHours = assignment.display_length_in_hours !== undefined ? assignment.display_length_in_hours : (assignment.length_in_hours || 1);
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

                                {/* Confidence Badge - אזהרת ביטחון נמוך */}
                                {(() => {
                                  const { confidence, reasons, level } = calculateAssignmentConfidence(assignment);
                                  if (level === 'נמוך') {
                                    return (
                                      <div
                                        className="absolute top-1 right-12 z-20 pointer-events-auto"
                                        title={`ביטחון נמוך (${(confidence * 100).toFixed(0)}%)\nסיבות:\n${reasons.join('\n')}`}
                                      >
                                        <div className="bg-yellow-500 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg flex items-center gap-1 animate-pulse">
                                          <AlertTriangle className="w-3 h-3" />
                                          ביטחון נמוך
                                        </div>
                                      </div>
                                    );
                                  } else if (level === 'בינוני') {
                                    return (
                                      <div
                                        className="absolute top-1 right-12 z-20 pointer-events-auto opacity-70 hover:opacity-100"
                                        title={`ביטחון בינוני (${(confidence * 100).toFixed(0)}%)\n${reasons.length > 0 ? `סיבות:\n${reasons.join('\n')}` : 'ללא התראות'}`}
                                      >
                                        <div className="bg-orange-400 text-white px-2 py-1 rounded-full text-xs font-bold shadow-md flex items-center gap-1">
                                          <AlertTriangle className="w-3 h-3" />
                                          בדוק
                                        </div>
                                      </div>
                                    );
                                  }
                                  return null;
                                })()}

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
                                        {assignment.soldiers.map((soldier) => {
                                          const workload = calculateSoldierWorkload(soldier.id);
                                          const workloadPercentage = Math.min((workload / 60) * 100, 100); // מקסימום 60 שעות = 100%
                                          const workloadColor = workload > 40 ? 'bg-red-500' : workload > 20 ? 'bg-yellow-500' : 'bg-green-500';
                                          
                                          const isSelectedSoldier = selectedSoldierForSwap && 
                                                                  selectedSoldierForSwap.soldier.id === soldier.id && 
                                                                  selectedSoldierForSwap.assignment.id === assignment.id;

                                          return (
                                            <div
                                              key={soldier.id}
                                              onClick={(e) => (user.role === 'מפ' || user.role === 'ממ') && handleSoldierSwapClick(soldier, assignment, e)}
                                              className={`text-xs backdrop-blur-md px-2 py-1 rounded border shadow-sm transition-all duration-200 cursor-pointer
                                                ${isSelectedSoldier 
                                                    ? 'bg-yellow-500 border-yellow-300 ring-2 ring-yellow-300 animate-pulse text-white' 
                                                    : 'bg-white/25 border-white/30 hover:bg-white/35 text-white'}
                                              `}
                                            >
                                              <div className="font-semibold flex items-center justify-between gap-1">
                                                <div className="flex items-center gap-1">
                                                  <Users className="w-2.5 h-2.5" />
                                                  {soldier.name}
                                                </div>
                                                <span className="text-[10px] font-bold opacity-90">{workload}ש'</span>
                                              </div>
                                              <div className="text-[10px] opacity-90 font-medium mb-1">
                                                {soldier.role_in_assignment}
                                              </div>
                                              {/* גרף עומס */}
                                              <div className="h-1 w-full bg-white/30 rounded-full overflow-hidden mt-1">
                                                <div
                                                  className={`h-full ${workloadColor} transition-all duration-500`}
                                                  style={{ width: `${workloadPercentage}%` }}
                                                  title={`${workload} שעות עבודה`}
                                                />
                                              </div>
                                            </div>
                                          );
                                        })}
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
                </DndContext>
                );
              })()}
            </div>
            )}
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

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackReasonModal
          onClose={() => setShowFeedbackModal(false)}
          onSubmit={(reason) => {
            handleFeedback(feedbackAssignmentId, 'rejected', reason);
            setShowFeedbackModal(false);
          }}
          onEdit={(reason) => {
            // שלח פידבק
            handleFeedback(feedbackAssignmentId, 'rejected', reason);
            setShowFeedbackModal(false);
            
            // פתח עריכה
            // חפש את המשימה ב-scheduleData
            let assignment = null;
            if (scheduleData?.assignments) {
                assignment = scheduleData.assignments.find(a => a.id === feedbackAssignmentId);
            }
            
            if (assignment) {
                setEditingAssignment(assignment);
                setShowAssignmentModal(true);
            } else {
                toast.error('לא ניתן לפתוח עריכה - המשימה לא נמצאה');
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

// Feedback Reason Modal
const FeedbackReasonModal = ({ onClose, onSubmit, onEdit }) => {
  const [reason, setReason] = useState('');
  const [customReason, setCustomReason] = useState('');

  const reasons = [
    'מחלקה לא נמצאת (בבית)',
    'לא בלבנה שלהם',
    'חיילים לא מתאימים',
    'חוסר במפקדים/נהגים',
    'אחר'
  ];

  const handleSubmit = () => {
    const finalReason = reason === 'אחר' ? customReason : reason;
    if (!finalReason) return;
    onSubmit(finalReason);
  };

  const handleEdit = () => {
    const finalReason = reason === 'אחר' ? customReason : reason;
    if (!finalReason) return;
    onEdit(finalReason);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-fadeIn">
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
            rows={2}
          />
        )}

        <div className="flex flex-col gap-3 mt-6">
          <div className="flex gap-3">
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

          <button
            onClick={handleEdit}
            disabled={!reason || (reason === 'אחר' && !customReason)}
            className="w-full bg-purple-100 text-purple-700 hover:bg-purple-200 font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Edit size={18} />
            שלח פידבק וערוך שיבוץ
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveSchedule;
