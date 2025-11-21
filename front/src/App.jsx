import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, lazy, Suspense } from 'react';
import { useAuth } from './context/AuthContext';
import { useServerStatus } from './context/ServerStatusContext';
import { setServerDownCallback, setServerUpCallback } from './services/api';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Loading from './components/Loading';
import MaintenanceScreen from './components/MaintenanceScreen';

// Lazy load heavy pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Plugot = lazy(() => import('./pages/Plugot'));
const Mahalkot = lazy(() => import('./pages/Mahalkot'));
const Templates = lazy(() => import('./pages/Templates'));
const SmartSchedule = lazy(() => import('./pages/SmartSchedule'));
const LiveSchedule = lazy(() => import('./pages/LiveSchedule'));
const Profile = lazy(() => import('./pages/Profile'));
const JoinRequests = lazy(() => import('./pages/JoinRequests'));

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
  const { isServerDown, markServerDown, markServerUp } = useServerStatus();

  // הגדר את ה-callbacks לזיהוי מצב השרת
  useEffect(() => {
    setServerDownCallback(markServerDown);
    setServerUpCallback(markServerUp);
  }, [markServerDown, markServerUp]);

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
          <Route index element={<Suspense fallback={<Loading />}><Dashboard /></Suspense>} />
          <Route path="plugot" element={<Suspense fallback={<Loading />}><Plugot /></Suspense>} />
          <Route path="mahalkot" element={<Suspense fallback={<Loading />}><Mahalkot /></Suspense>} />
          <Route path="templates" element={<Suspense fallback={<Loading />}><Templates /></Suspense>} />
          <Route path="live-schedule" element={<Suspense fallback={<Loading />}><LiveSchedule /></Suspense>} />
          <Route path="join-requests" element={<Suspense fallback={<Loading />}><JoinRequests /></Suspense>} />
          <Route path="profile" element={<Suspense fallback={<Loading />}><Profile /></Suspense>} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
