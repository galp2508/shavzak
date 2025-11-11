import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Check, X, Clock, UserPlus } from 'lucide-react';
import { toast } from 'react-toastify';

const JoinRequests = () => {
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const response = await api.get('/join-requests');
      setRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error loading join requests:', error);
      toast.error('שגיאה בטעינת בקשות הצטרפות');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId) => {
    if (!window.confirm('האם אתה בטוח שברצונך לאשר בקשה זו?')) return;

    try {
      const response = await api.post(`/join-requests/${requestId}/approve`);
      toast.success('הבקשה אושרה בהצלחה! פלוגה חדשה נוצרה.');
      loadRequests();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה באישור הבקשה');
    }
  };

  const handleReject = async (requestId) => {
    if (!window.confirm('האם אתה בטוח שברצונך לדחות בקשה זו?')) return;

    try {
      await api.post(`/join-requests/${requestId}/reject`);
      toast.success('הבקשה נדחתה');
      loadRequests();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בדחיית הבקשה');
    }
  };

  const handleDelete = async (requestId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק בקשה זו?')) return;

    try {
      await api.delete(`/join-requests/${requestId}`);
      toast.success('הבקשה נמחקה');
      loadRequests();
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת הבקשה');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">בקשות הצטרפות</h1>
        <p className="text-gray-600 mt-1">
          ניהול בקשות הצטרפות למפקדי פלוגות חדשים
        </p>
      </div>

      {/* Requests List */}
      {requests.length === 0 ? (
        <div className="card text-center py-12">
          <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-700 mb-2">
            אין בקשות ממתינות
          </h3>
          <p className="text-gray-500">
            כל הבקשות עובדו, אין בקשות המתנה כרגע
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {requests.map((request) => (
            <div
              key={request.id}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="bg-military-100 p-3 rounded-lg">
                  <UserPlus className="w-8 h-8 text-military-600" />
                </div>
                <span className="badge badge-yellow">ממתין</span>
              </div>

              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {request.full_name}
              </h3>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-gray-600">
                  <Shield size={16} />
                  <span className="text-sm">
                    פלוגה: {request.pluga_name}
                  </span>
                </div>

                {request.gdud && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Shield size={16} />
                    <span className="text-sm">גדוד: {request.gdud}</span>
                  </div>
                )}

                <div className="text-sm text-gray-500">
                  משתמש: {request.username}
                </div>

                <div className="text-xs text-gray-400">
                  נשלח:{' '}
                  {new Date(request.created_at).toLocaleDateString('he-IL')}
                </div>
              </div>

              <div className="flex gap-2 pt-4 border-t">
                <button
                  onClick={() => handleApprove(request.id)}
                  className="flex-1 btn-primary flex items-center justify-center gap-2"
                  title="אשר בקשה"
                >
                  <Check size={18} />
                  <span>אשר</span>
                </button>
                <button
                  onClick={() => handleReject(request.id)}
                  className="flex-1 btn-secondary flex items-center justify-center gap-2"
                  title="דחה בקשה"
                >
                  <X size={18} />
                  <span>דחה</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JoinRequests;
