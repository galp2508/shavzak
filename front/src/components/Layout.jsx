import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Home, Users, Shield, FileText,
  Calendar, LogOut, User, Menu, X, UserCheck
} from 'lucide-react';
import { useState } from 'react';

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'דשבורד', href: '/', icon: Home, roles: ['מפ', 'ממ', 'מכ'] },
    { name: 'פלוגות', href: '/plugot', icon: Shield, roles: ['מפ'] },
    { name: 'מחלקות', href: '/mahalkot', icon: Users, roles: ['מפ', 'ממ'] },
    { name: 'תבניות משימות', href: '/templates', icon: FileText, roles: ['מפ'] },
    { name: 'שיבוצים', href: '/shavzakim', icon: Calendar, roles: ['מפ', 'ממ', 'מכ'] },
  ];

  // הוסף "בקשות הצטרפות" רק למפ ראשי (מפ ללא pluga_id)
  if (user?.role === 'מפ' && !user?.pluga_id) {
    navigation.push({
      name: 'בקשות הצטרפות',
      href: '/join-requests',
      icon: UserCheck,
      roles: ['מפ']
    });
  }

  const filteredNav = navigation.filter(item => 
    item.roles.includes(user?.role)
  );

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-military-700 text-white shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md hover:bg-military-600"
              >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
              <Shield className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">Shavzak</h1>
                <p className="text-xs text-military-200">מערכת ניהול שיבוצים</p>
              </div>
            </div>

            {/* User Info */}
            <div className="flex items-center gap-4">
              <Link
                to="/profile"
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-military-600 transition-colors"
              >
                <User size={20} />
                <div className="hidden sm:block text-right">
                  <p className="text-sm font-medium">{user?.full_name}</p>
                  <p className="text-xs text-military-200">{user?.role}</p>
                </div>
              </Link>
              <button
                onClick={logout}
                className="p-2 rounded-lg hover:bg-military-600 transition-colors"
                title="התנתק"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 right-0 z-40 w-64 bg-white border-l border-gray-200
            transform transition-transform duration-300 ease-in-out
            ${sidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
            top-16 lg:top-0 lg:mt-0
          `}
        >
          <nav className="p-4 space-y-1">
            {filteredNav.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors
                    ${active
                      ? 'bg-military-600 text-white shadow-md'
                      : 'text-gray-700 hover:bg-gray-100'
                    }
                  `}
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
