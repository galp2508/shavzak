import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Users, Shield, Calendar,
  Activity, Award, Clock, CheckCircle, Truck, TrendingUp, AlertTriangle,
  PieChart as PieChartIcon, BarChart as BarChartIcon
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [pluga, setPluga] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState({ status: [], workload: [] });

  useEffect(() => {
    // Load stats once user is available (we need pluga_id)
    if (user) {
      loadPluga();
      loadStats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    // if no user (not authenticated) stop loading spinner
    if (!user) setLoading(false);
  }, [user]);

  const loadStats = async () => {
    try {
      // נסה את נקודת הקצה /stats אם קיימת
      const res = await api.get('/stats').catch(() => null);
      if (res && res.data && res.data.stats) {
        setStats(res.data.stats);
        return;
      }

      // Fallback: חישוב סטטיסטיקות בעזרת נקודות הקצה הקיימות
      if (!user?.pluga_id) {
        setStats({});
        return;
      }

      // רשימת מחלקות של הפלוגה
      const mahRes = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      const mahalkot = mahRes.data.mahalkot || [];

      // רשימת שיבוצים של הפלוגה
      const shavRes = await api.get(`/plugot/${user.pluga_id}/shavzakim`);
      const shavzakim = shavRes.data.shavzakim || [];

      // שיבוץ חי להיום (עבור סטטיסטיקות זמן אמת)
      const today = new Date().toISOString().split('T')[0];
      const liveScheduleRes = await api.get(`/plugot/${user.pluga_id}/live-schedule?date=${today}`).catch(() => ({ data: {} }));
      const liveAssignments = liveScheduleRes.data.assignments || [];

      // סכום חיילים בכל מחלקה וספירת מפקדים
      const soldiersPromises = mahalkot.map((m) =>
        api.get(`/mahalkot/${m.id}/soldiers`).then((r) => {
          const sList = r.data.soldiers || [];
          // Inject mahlaka_id manually if missing, to ensure we can link back to mahlaka
          return sList.map(s => ({ ...s, mahlaka_id: s.mahlaka_id || m.id }));
        }).catch((err) => {
          console.error(`Failed to fetch soldiers for mahlaka ${m.id}`, err);
          return [];
        })
      );
      const soldiersArrays = await Promise.all(soldiersPromises);
      const allSoldiers = soldiersArrays.flat();

      console.log('Dashboard loaded soldiers:', allSoldiers.length); // Debug log

      const totalSoldiers = allSoldiers.length;

      // ספירת חיילים בבסיס לפי קטגוריות
      let soldiersOnBase = 0;
      let commandersOnBase = 0;
      let driversOnBase = 0;
      const mahlakaOnBaseCounts = {}; // mahlakaId -> count
      
      // New logic for active soldiers and next assignment
      const activeSoldiers = new Set();
      let nextAssignment = null;
      const currentHour = new Date().getHours();
      
      // Calculate active soldiers from live assignments
      liveAssignments.forEach(assignment => {
        const start = assignment.start_hour;
        const end = assignment.start_hour + assignment.length_in_hours;
        
        // Check if currently active
        if (currentHour >= start && currentHour < end) {
            if (assignment.soldiers) {
                assignment.soldiers.forEach(s => activeSoldiers.add(s.id));
            }
        }
        
        // Check for next assignment
        if (start > currentHour) {
            if (!nextAssignment || start < nextAssignment.start_hour) {
                nextAssignment = assignment;
            }
        }
      });

      // Calculate chart data
      const statusCounts = {};
      const workloadByMahlaka = {}; // mahlaka_id -> hours

      allSoldiers.forEach(soldier => {
        // Determine Status
        let status = 'בבסיס';
        if (soldier.status && soldier.status.status_type) {
            status = soldier.status.status_type;
            // Normalize 'בסבב קו' to 'סבב קו'
            if (status === 'בסבב קו') status = 'סבב קו';
        } else if (soldier.in_round) {
            status = 'סבב קו';
        }

        const isOnBase = status === 'בבסיס';

        // Status Chart Data
        if (statusCounts[status] !== undefined) {
            statusCounts[status]++;
        } else {
            statusCounts[status] = 1;
        }

        if (isOnBase) {
          // ספירת חיילים בבסיס לכל מחלקה
          const mahlaka = mahalkot.find(m => m.id === soldier.mahlaka_id);
          if (mahlaka) {
            if (!mahlakaOnBaseCounts[mahlaka.id]) {
                mahlakaOnBaseCounts[mahlaka.id] = 0;
            }
            mahlakaOnBaseCounts[mahlaka.id]++;
            
            // Initialize workload for this mahlaka if needed
            if (!workloadByMahlaka[mahlaka.number]) {
                workloadByMahlaka[mahlaka.number] = 0;
            }
          }

          // Check for specific roles/certifications
          const isCommander = ['ממ', 'מכ', 'סמל'].includes(soldier.role) || 
                              (soldier.certifications && soldier.certifications.some(c => c.name === 'מפקד'));
          
          const isDriver = soldier.role.includes('נהג') || 
                           (soldier.certifications && soldier.certifications.some(c => c.name === 'נהג'));

          // סיווג לפי תפקיד
          if (isCommander) {
            commandersOnBase++;
          } else if (isDriver) {
            driversOnBase++;
          } else {
            // חייל רגיל (לא מפקד ולא נהג)
            soldiersOnBase++;
          }
        }
      });

      // חישוב מחלקות בבסיס - רק אם יש יותר מ-3 חיילים בבסיס
      const activeMahalkotCount = Object.values(mahlakaOnBaseCounts).filter(count => count > 3).length;
      
      // Calculate workload from assignments
      liveAssignments.forEach(assignment => {
          // משימות בסיס (מנוחה) לא נספרות בעומס
          if (assignment.is_base_task) return;
          
          // Try to attribute to a mahlaka
          // If assigned_mahlaka_id exists, use it
          // Otherwise, look at the soldiers
          let mahlakaName = null;
          if (assignment.assigned_mahlaka_id) {
              const m = mahalkot.find(m => m.id === assignment.assigned_mahlaka_id);
              if (m) mahlakaName = m.number;
          } else if (assignment.soldiers && assignment.soldiers.length > 0) {
              // Infer from first soldier
              // We need to find the soldier in allSoldiers to get mahlaka_id
              const firstSoldierId = assignment.soldiers[0].id;
              const soldier = allSoldiers.find(s => s.id === firstSoldierId);
              if (soldier) {
                  const m = mahalkot.find(m => m.id === soldier.mahlaka_id);
                  if (m) mahlakaName = m.number;
              }
          }
          
          // Only count specific mahlaka assignments, ignore general/pluga assignments
          if (mahlakaName) {
              if (!workloadByMahlaka[mahlakaName]) workloadByMahlaka[mahlakaName] = 0;
              workloadByMahlaka[mahlakaName] += assignment.length_in_hours;
          }
      });

      // Get names (numbers) of active mahalkot
      const activeMahalkotIds = Object.keys(mahlakaOnBaseCounts).filter(mid => mahlakaOnBaseCounts[mid] > 3);
      const activeMahalkotNumbers = activeMahalkotIds.map(mid => {
          const m = mahalkot.find(m => m.id === parseInt(mid));
          return m ? m.number : '?';
      }).sort((a, b) => a - b);

      // Format Chart Data
      // Define colors for known statuses
      const statusColors = {
        'בבסיס': '#10B981', // Green
        'בית': '#EF4444', // Red
        'גימלים': '#F59E0B', // Yellow
        'חופשה': '#3B82F6', // Blue
        'בקשת יציאה': '#8B5CF6', // Purple
        'סבב קו': '#EC4899', // Pink
        'ריתוק': '#6366F1', // Indigo
        'מילואים': '#14B8A6', // Teal
      };

      const statusChartData = Object.entries(statusCounts).map(([name, value]) => ({
        name,
        value,
        color: statusColors[name] || '#6B7280' // Default gray
      })).filter(d => d.value > 0);
      
      const workloadChartData = Object.entries(workloadByMahlaka).map(([name, hours]) => ({
          name: `מחלקה ${name}`,
          hours: hours
      }));

      setChartData({
          status: statusChartData,
          workload: workloadChartData
      });

      setStats({
        mahalkot_count: activeMahalkotCount,
        mahalkot_names: activeMahalkotNumbers,
        soldiers_on_base: soldiersOnBase,
        commanders_on_base: commandersOnBase,
        drivers_on_base: driversOnBase,
        active_now: activeSoldiers.size,
        next_assignment: nextAssignment
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
      setStats({});
    } finally {
      setLoading(false);
    }
  };

  const loadPluga = async () => {
    try {
      if (!user?.pluga_id) return;
      const res = await api.get(`/plugot/${user.pluga_id}`);
      setPluga(res.data.pluga || null);
    } catch (e) {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'מחלקות בבסיס',
      value: stats?.mahalkot_count || 0,
      icon: Shield,
      color: 'bg-blue-500',
      subtext: stats?.mahalkot_names?.length > 0 ? `מחלקות: ${stats.mahalkot_names.join(', ')}` : 'אין מחלקות'
    },
    {
      title: 'חיילים בבסיס',
      value: stats?.soldiers_on_base || 0,
      icon: Users,
      color: 'bg-green-500',
      subtext: 'ללא מפקדים ונהגים'
    },
    {
      title: 'מפקדים בבסיס',
      value: stats?.commanders_on_base || 0,
      icon: Award,
      color: 'bg-purple-500',
    },
    {
      title: 'נהגים בבסיס',
      value: stats?.drivers_on_base || 0,
      icon: Truck,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome */}
      <div className="card bg-gradient-to-br from-military-600 via-military-700 to-military-800 text-white shadow-2xl border-none overflow-hidden relative p-6 md:p-8">
        <div className="absolute top-0 left-0 w-64 h-64 bg-white opacity-5 rounded-full -translate-x-32 -translate-y-32"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-white opacity-5 rounded-full translate-x-48 translate-y-48"></div>
        <div className="flex flex-col md:flex-row items-center justify-between relative z-10 gap-6">
          <div className="text-center md:text-right w-full md:w-auto">
            <h1 className="text-3xl md:text-4xl font-bold mb-3 tracking-tight">
              שלום, {user?.full_name} 👋
            </h1>
            <p className="text-military-100 text-base md:text-lg font-medium flex flex-wrap items-center justify-center md:justify-start gap-2">
              <span className="bg-white/20 px-3 py-1 rounded-full">{user?.role}</span>
              <span className="hidden md:inline">·</span>
              <span>{pluga?.name || user?.pluga_id || 'טוען...'}</span>
            </p>
          </div>
          
          <div className="bg-white bg-opacity-20 p-4 rounded-2xl backdrop-blur-sm hidden md:block">
            <Activity className="w-16 h-16 md:w-20 md:h-20" />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="card hover:shadow-2xl transition-all duration-300 hover:scale-105 transform animate-slideIn overflow-hidden relative group"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-gray-100 to-transparent rounded-full -translate-y-16 translate-x-16 group-hover:scale-150 transition-transform duration-500"></div>
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                  <div className={`${stat.color} bg-gradient-to-br p-4 rounded-2xl text-white shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                    <Icon size={28} />
                  </div>
                </div>
                <h3 className="text-gray-600 text-base font-semibold mb-2">{stat.title}</h3>
                <p className="text-4xl font-bold text-gray-900 tracking-tight">{stat.value}</p>
                {stat.subtext && (
                  <p className="text-xs text-gray-500 mt-2 font-medium">{stat.subtext}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts & Detailed Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Chart */}
        <div className="card lg:col-span-1 min-h-[300px] flex flex-col">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <PieChartIcon className="text-blue-500" size={20} />
            סטטוס כוח אדם
          </h3>
          <div className="flex-1 w-full h-full min-h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData.status}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {chartData.status.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Workload Chart */}
        <div className="card lg:col-span-2 min-h-[300px] flex flex-col">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <BarChartIcon className="text-purple-500" size={20} />
            עומס שעות לפי מחלקה (היום)
          </h3>
          <div className="flex-1 w-full h-full min-h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData.workload}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip cursor={{fill: 'transparent'}} />
                <Bar dataKey="hours" name="שעות שמירה" fill="#8B5CF6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Next Shift Card */}
      {stats?.next_assignment && (
        <div className="card bg-gradient-to-r from-indigo-500 to-purple-600 text-white overflow-hidden relative">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-10 rounded-full -translate-y-32 translate-x-16"></div>
          <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6 p-2">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm">
                <Clock size={32} className="animate-pulse" />
              </div>
              <div>
                <p className="text-indigo-100 font-medium mb-1">המשימה הבאה ({stats.next_assignment.start_hour}:00)</p>
                <h3 className="text-2xl font-bold">{stats.next_assignment.name}</h3>
              </div>
            </div>
            
            <div className="flex -space-x-2 space-x-reverse overflow-hidden p-2">
              {stats.next_assignment.soldiers.slice(0, 5).map((s, i) => (
                <div key={i} className="w-10 h-10 rounded-full bg-white/20 border-2 border-indigo-400 flex items-center justify-center text-xs font-bold" title={s.name}>
                  {s.name.charAt(0)}
                </div>
              ))}
              {stats.next_assignment.soldiers.length > 5 && (
                <div className="w-10 h-10 rounded-full bg-white/20 border-2 border-indigo-400 flex items-center justify-center text-xs font-bold">
                  +{stats.next_assignment.soldiers.length - 5}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Clock size={24} className="text-military-600" />
            פעולות מהירות
          </h2>
          <div className="space-y-3">
            {user?.role === 'מפ' && (
              <>
                <QuickAction
                  title="יצירת שיבוץ חדש"
                  description="תכנון שיבוץ לשבוע הבא"
                  icon={Calendar}
                  href="/shavzakim"
                />
                <QuickAction
                  title="ניהול מחלקות"
                  description="ניהול חיילים במחלקות"
                  icon={Users}
                  href="/mahalkot"
                />
                <QuickAction
                  title="ניהול תבניות"
                  description="עריכת תבניות משימות"
                  icon={CheckCircle}
                  href="/templates"
                />
              </>
            )}
            {user?.role === 'ממ' && (
              <>
                <QuickAction
                  title="ניהול המחלקה"
                  description="צפייה בחיילי המחלקה"
                  icon={Shield}
                  href="/mahalkot"
                />
                <QuickAction
                  title="שיבוצים פעילים"
                  description="צפייה בשיבוצים קיימים"
                  icon={Calendar}
                  href="/shavzakim"
                />
              </>
            )}
            {user?.role === 'מכ' && (
              <>
                <QuickAction
                  title="חיילי הכיתה"
                  description="ניהול חיילי כיתה {user?.kita}"
                  icon={Users}
                  href="/mahalkot"
                />
                <QuickAction
                  title="שיבוצים"
                  description="צפייה בשיבוצים"
                  icon={Calendar}
                  href="/shavzakim"
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

import { Link } from 'react-router-dom';

const QuickAction = ({ title, description, icon: Icon, href }) => {
  return (
    <Link
      to={href}
      className="flex items-center gap-5 p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl hover:from-military-50 hover:to-military-100 transition-all duration-300 group shadow-md hover:shadow-xl transform hover:scale-102"
    >
      <div className="bg-gradient-to-br from-military-600 to-military-700 p-4 rounded-2xl text-white group-hover:from-military-700 group-hover:to-military-800 transition-all duration-300 shadow-lg group-hover:scale-110 transform">
        <Icon size={24} />
      </div>
      <div className="flex-1">
        <h3 className="font-bold text-gray-900 text-lg mb-1">{title}</h3>
        <p className="text-sm text-gray-600 font-medium">{description}</p>
      </div>
    </Link>
  );
};

export default Dashboard;
