import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Users, Shield, Calendar,
  Activity, Award, Clock, CheckCircle
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [pluga, setPluga] = useState(null);
  const [loading, setLoading] = useState(true);

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

      // סכום חיילים בכל מחלקה וספירת מפקדים
      const soldiersPromises = mahalkot.map((m) =>
        api.get(`/mahalkot/${m.id}/soldiers`).then((r) => r.data.soldiers || []).catch(() => [])
      );
      const soldiersArrays = await Promise.all(soldiersPromises);
      const allSoldiers = soldiersArrays.flat();

      const totalSoldiers = allSoldiers.length;

      // ספירת מפקדים: ממ, מכ, וסמל
      const commanderCount = allSoldiers.filter(soldier =>
        soldier.role === 'ממ' ||
        soldier.role === 'מכ' ||
        soldier.role === 'סמל'
      ).length;

      setStats({
        mahalkot: mahalkot.length,
        total_soldiers: totalSoldiers,
        commanders: commanderCount,
        shavzakim: shavzakim.length,
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
      title: 'מחלקות',
      value: stats?.mahalkot || 0,
      icon: Shield,
      color: 'bg-blue-500',
    },
    {
      title: 'סה״כ חיילים',
      value: stats?.total_soldiers || 0,
      icon: Users,
      color: 'bg-green-500',
    },
    {
      title: 'מפקדים',
      value: stats?.commanders || 0,
      icon: Award,
      color: 'bg-purple-500',
    },
    {
      title: 'שיבוצים',
      value: stats?.shavzakim || 0,
      icon: Calendar,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome */}
      <div className="card bg-gradient-to-br from-military-600 via-military-700 to-military-800 text-white shadow-2xl border-none overflow-hidden relative">
        <div className="absolute top-0 left-0 w-64 h-64 bg-white opacity-5 rounded-full -translate-x-32 -translate-y-32"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-white opacity-5 rounded-full translate-x-48 translate-y-48"></div>
        <div className="flex items-center justify-between relative z-10">
          <div>
            <h1 className="text-4xl font-bold mb-3 tracking-tight">
              שלום, {user?.full_name} 👋
            </h1>
            <p className="text-military-100 text-lg font-medium flex items-center gap-2">
              <span className="bg-white/20 px-3 py-1 rounded-full">{user?.role}</span>
              <span>·</span>
              <span>{pluga?.name || user?.pluga_id || 'טוען...'}</span>
            </p>
          </div>
          <div className="bg-white bg-opacity-20 p-4 rounded-2xl backdrop-blur-sm">
            <Activity className="w-20 h-20" />
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
              </div>
            </div>
          );
        })}
      </div>

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

const QuickAction = ({ title, description, icon: Icon, href }) => {
  return (
    <a
      href={href}
      className="flex items-center gap-5 p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl hover:from-military-50 hover:to-military-100 transition-all duration-300 group shadow-md hover:shadow-xl transform hover:scale-102"
    >
      <div className="bg-gradient-to-br from-military-600 to-military-700 p-4 rounded-2xl text-white group-hover:from-military-700 group-hover:to-military-800 transition-all duration-300 shadow-lg group-hover:scale-110 transform">
        <Icon size={24} />
      </div>
      <div className="flex-1">
        <h3 className="font-bold text-gray-900 text-lg mb-1">{title}</h3>
        <p className="text-sm text-gray-600 font-medium">{description}</p>
      </div>
    </a>
  );
};

export default Dashboard;
