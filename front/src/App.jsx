import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { useServerStatus } from './context/ServerStatusContext';
import { setServerDownCallback } from './services/api';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Plugot from './pages/Plugot';
import Mahalkot from './pages/Mahalkot';
import Templates from './pages/Templates';
import Shavzakim from './pages/Shavzakim';
import ShavzakView from './pages/ShavzakView';
import LiveSchedule from './pages/LiveSchedule';
import Profile from './pages/Profile';
import JoinRequests from './pages/JoinRequests';
import Loading from './components/Loading';
import MaintenanceScreen from './components/MaintenanceScreen';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();

  // ⏳ אם עדיין טוען, הצג מסך טעינה
  if (loading) {
    return <Loading />;
  }

  // 🔒 אם אין token, redirect ל-login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // ⏳ אם יש token אבל עדיין לא טען user, המתן
  if (!user) {
    return <Loading />;
  }

  // ✅ הכל טוב, הצג את התוכן
  return children;
};

// Public Route (redirect if logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <Loading />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  const { isServerDown, markServerDown } = useServerStatus();

  // הגדר את ה-callback לזיהוי שרת לא זמין
  useEffect(() => {
    setServerDownCallback(markServerDown);
  }, [markServerDown]);

  // אם השרת לא זמין, הצג מסך תחזוקה
  if (isServerDown) {
    return <MaintenanceScreen />;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="plugot" element={<Plugot />} />
          <Route path="mahalkot" element={<Mahalkot />} />
          <Route path="templates" element={<Templates />} />
          <Route path="live-schedule" element={<LiveSchedule />} />
          <Route path="shavzakim" element={<Shavzakim />} />
          <Route path="shavzakim/:id" element={<ShavzakView />} />
          <Route path="join-requests" element={<JoinRequests />} />
          <Route path="profile" element={<Profile />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
