import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, UserPlus, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../services/api';

const Register = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    plugaId: '',
    plugaName: '',
    gdud: '',
    role: 'חייל',
    isNewMaf: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [plugot, setPlugot] = useState([]);
  const [isFirstUser, setIsFirstUser] = useState(false);

  useEffect(() => {
    const loadPlugot = async () => {
      try {
        const response = await api.get('/plugot');
        setPlugot(response.data.plugot || []);
        // אם אין פלוגות, זה אומר שאין משתמשים (משתמש ראשון יוצר את הפלוגה)
        if (response.data.plugot.length === 0) {
          setIsFirstUser(true);
        }
      } catch (error) {
        console.error('Error loading plugot:', error);
      }
    };
    loadPlugot();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      setError('הסיסמאות אינן תואמות');
      return;
    }

    if (formData.password.length < 6) {
      setError('הסיסמה חייבת להכיל לפחות 6 תווים');
      return;
    }

    // אם לא משתמש ראשון ולא מפ חדש, חובה לבחור פלוגה
    if (!isFirstUser && !formData.isNewMaf && !formData.plugaId) {
      setError('חובה לבחור פלוגה');
      return;
    }

    // אם מפ חדש, חובה שם פלוגה
    if (!isFirstUser && formData.isNewMaf && !formData.plugaName) {
      setError('חובה להזין שם פלוגה');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (formData.isNewMaf) {
        // בקשת הצטרפות למפ חדש
        const response = await api.post('/register', {
          username: formData.username,
          password: formData.password,
          full_name: formData.fullName,
          pluga_name: formData.plugaName,
          gdud: formData.gdud
        });

        if (response.data.message) {
          setSuccess(response.data.message);
          toast.success(response.data.message);
          // אחרי 3 שניות, נווט ללוגין
          setTimeout(() => {
            navigate('/login');
          }, 3000);
        }
      } else {
        // רישום רגיל
        const result = await register(
          formData.username,
          formData.password,
          formData.fullName,
          isFirstUser ? null : formData.plugaId,
          isFirstUser ? null : formData.role
        );

        if (result.success) {
          toast.success('נרשמת בהצלחה!');
          navigate('/', { replace: true });
        } else {
          setError(result.error);
          toast.error(result.error);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'שגיאה ברישום');
      toast.error(err.response?.data?.error || 'שגיאה ברישום');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-military-600 to-military-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-white p-4 rounded-full shadow-lg">
              <Shield className="w-12 h-12 text-military-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Shavzak</h1>
          <p className="text-military-200">מערכת ניהול שיבוצים צבאית</p>
        </div>

        {/* Register Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            רישום למערכת
          </h2>

          {isFirstUser && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                ℹ️ המשתמש הראשון במערכת יקבל הרשאות מ"פ אוטומטית
              </p>
            </div>
          )}

          {!isFirstUser && plugot.length > 0 && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                ℹ️ אנא בחר את הפלוגה שאליה אתה משתייך
              </p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <Shield className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="label">שם מלא</label>
              <input
                type="text"
                name="fullName"
                value={formData.fullName}
                onChange={handleChange}
                className="input-field"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="label">שם משתמש</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="label">סיסמה</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="input-field"
                required
                minLength={6}
              />
              <p className="text-xs text-gray-500 mt-1">לפחות 6 תווים</p>
            </div>

            <div>
              <label className="label">אימות סיסמה</label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="input-field"
                required
              />
            </div>

            {!isFirstUser && (
              <>
                <div className="border-t border-gray-200 pt-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      name="isNewMaf"
                      checked={formData.isNewMaf}
                      onChange={handleChange}
                      className="w-4 h-4 text-military-600 rounded"
                    />
                    <span className="text-gray-700 font-medium">
                      אני מפקד פלוגה חדש (בקשת הצטרפות)
                    </span>
                  </label>
                  <p className="text-xs text-gray-500 mt-1 mr-7">
                    סמן אם אתה מפקד פלוגה חדש ורוצה להצטרף למערכת
                  </p>
                </div>

                {formData.isNewMaf ? (
                  <>
                    <div>
                      <label className="label">שם הפלוגה *</label>
                      <input
                        type="text"
                        name="plugaName"
                        value={formData.plugaName}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="לדוגמה: פלוגה א', פלוגה 1"
                        required
                      />
                    </div>

                    <div>
                      <label className="label">גדוד (אופציונלי)</label>
                      <input
                        type="text"
                        name="gdud"
                        value={formData.gdud}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="לדוגמה: גדוד נחל, גדוד 52"
                      />
                    </div>

                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        ⚠️ הבקשה תישלח לאישור המפקד הראשי במערכת. תקבל הודעה כשהבקשה תאושר.
                      </p>
                    </div>
                  </>
                ) : plugot.length > 0 ? (
                  <>
                    <div>
                      <label className="label">פלוגה *</label>
                      <select
                        name="plugaId"
                        value={formData.plugaId}
                        onChange={handleChange}
                        className="input-field"
                        required
                      >
                        <option value="">בחר פלוגה</option>
                        {plugot.map((pluga) => (
                          <option key={pluga.id} value={pluga.id}>
                            פלוגה {pluga.name} {pluga.gdud && `- גדוד ${pluga.gdud}`}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="label">תפקיד</label>
                      <select
                        name="role"
                        value={formData.role}
                        onChange={handleChange}
                        className="input-field"
                      >
                        <option value="חייל">חייל</option>
                        <option value="מכ">מפקד כיתה (מ״כ)</option>
                        <option value="ממ">מפקד מחלקה (מ״מ)</option>
                        <option value="מפ">מפקד פלוגה (מ״פ)</option>
                      </select>
                      <p className="text-xs text-gray-500 mt-1">בחר את התפקיד שלך ביחידה</p>
                    </div>
                  </>
                ) : null}
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary flex items-center justify-center gap-2 py-3"
            >
              {loading ? (
                <>
                  <div className="spinner w-5 h-5 border-2"></div>
                  <span>נרשם...</span>
                </>
              ) : (
                <>
                  <UserPlus size={20} />
                  <span>הירשם</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              כבר יש לך חשבון?{' '}
              <Link
                to="/login"
                className="text-military-600 hover:text-military-700 font-medium"
              >
                התחבר כאן
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-military-200 text-sm">
          <p>נבנה בגאווה לצה"ל 🇮🇱</p>
        </div>
      </div>
    </div>
  );
};

export default Register;
