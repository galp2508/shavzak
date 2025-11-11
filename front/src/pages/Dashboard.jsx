import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Users, Shield, Calendar, Award, Clock, CheckCircle
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

      // סכום חיילים בכל מחלקה (מקביל לקריאות /mahalkot/:id/soldiers)
      const soldierCountsPromises = mahalkot.map((m) =>
        api.get(`/mahalkot/${m.id}/soldiers`).then((r) => r.data.soldiers?.length || 0).catch(() => 0)
      );
      const counts = await Promise.all(soldierCountsPromises);
      const totalSoldiers = counts.reduce((a, b) => a + b, 0);

      setStats({
        mahalkot: mahalkot.length,
        total_soldiers: totalSoldiers,
        commanders: 0, // לא קיים endpoint ישיר — ניתן להרחיב בעתיד
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
      <div className="card bg-gradient-to-r from-military-600 to-military-700 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              שלום, {user?.full_name} 👋
            </h1>
            <p className="text-military-100">
              {user?.role} · {pluga?.name || user?.pluga_id || 'טוען...'}
            </p>
          </div>
          <Shield className="w-16 h-16 opacity-50" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="card hover:shadow-lg transition-shadow animate-slideIn"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.color} p-3 rounded-lg text-white`}>
                  <Icon size={24} />
                </div>
              </div>
              <h3 className="text-gray-600 text-sm mb-1">{stat.title}</h3>
              <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
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
                  description="צפייה ועריכת מחלקות"
                  icon={Shield}
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
      className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group border border-gray-200"
    >
      <div className="bg-military-600 p-3 rounded-lg text-white group-hover:bg-military-700 transition-colors">
        <Icon size={20} />
      </div>
      <div className="flex-1">
        <h3 className="font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </a>
  );
};

export default Dashboard;
