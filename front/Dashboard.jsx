import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  Users, Shield, Calendar, TrendingUp, 
  Activity, Award, Clock, CheckCircle 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await api.get('/stats');
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
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
      change: '+2',
    },
    {
      title: 'סה״כ חיילים',
      value: stats?.total_soldiers || 0,
      icon: Users,
      color: 'bg-green-500',
      change: '+12',
    },
    {
      title: 'מפקדים',
      value: stats?.commanders || 0,
      icon: Award,
      color: 'bg-purple-500',
      change: '+1',
    },
    {
      title: 'שיבוצים',
      value: stats?.shavzakim || 0,
      icon: Calendar,
      color: 'bg-orange-500',
      change: '+3',
    },
  ];

  const chartData = [
    { name: 'מחלקה 1', soldiers: 25, commanders: 3, drivers: 4 },
    { name: 'מחלקה 2', soldiers: 23, commanders: 3, drivers: 3 },
    { name: 'מחלקה 3', soldiers: 27, commanders: 4, drivers: 5 },
    { name: 'מחלקה 4', soldiers: 20, commanders: 2, drivers: 3 },
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
              {user?.role} · {user?.pluga?.name || 'טוען...'}
            </p>
          </div>
          <Activity className="w-16 h-16 opacity-50" />
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
                <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
                  {stat.change}
                </span>
              </div>
              <h3 className="text-gray-600 text-sm mb-1">{stat.title}</h3>
              <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <TrendingUp size={24} className="text-military-600" />
            התפלגות כוח אדם
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="soldiers" fill="#34996e" name="לוחמים" />
              <Bar dataKey="commanders" fill="#D4AF37" name="מפקדים" />
              <Bar dataKey="drivers" fill="#3b82f6" name="נהגים" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Quick Actions */}
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
                  title="הוספת חייל"
                  description="רישום חייל חדש במערכת"
                  icon={Users}
                  href="/soldiers"
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
                  href="/soldiers"
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
                  href="/soldiers"
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

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Activity size={24} className="text-military-600" />
          פעילות אחרונה
        </h2>
        <div className="space-y-4">
          <ActivityItem
            title="שיבוץ שבוע 46 נוצר"
            time="לפני שעתיים"
            type="success"
          />
          <ActivityItem
            title="נוסף חייל חדש למחלקה 2"
            time="לפני 4 שעות"
            type="info"
          />
          <ActivityItem
            title="עודכן תבנית משימה 'סיור'"
            time="אתמול"
            type="warning"
          />
        </div>
      </div>
    </div>
  );
};

const QuickAction = ({ title, description, icon: Icon, href }) => {
  return (
    <a
      href={href}
      className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
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

const ActivityItem = ({ title, time, type }) => {
  const colors = {
    success: 'bg-green-100 text-green-800',
    info: 'bg-blue-100 text-blue-800',
    warning: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <div className="flex items-center gap-4 pb-4 border-b border-gray-100 last:border-0 last:pb-0">
      <div className={`w-2 h-2 rounded-full ${colors[type]}`}></div>
      <div className="flex-1">
        <p className="font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">{time}</p>
      </div>
    </div>
  );
};

export default Dashboard;
