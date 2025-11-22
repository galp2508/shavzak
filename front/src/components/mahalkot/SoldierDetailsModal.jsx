import { useState, useEffect } from 'react';
import api from '../../services/api';
import { Shield, X, Users, Plus, Edit } from 'lucide-react';
import { toast } from 'react-toastify';
import { HOME_ROUND_DAYS } from '../../constants/config';

const SoldierDetailsModal = ({ soldier, onClose, onEdit }) => {
  const [availableRoles, setAvailableRoles] = useState([]);
  const [showAddCertModal, setShowAddCertModal] = useState(false);
  // הסמכות יכולות להיות מערך של אובייקטים {id, name} או מחרוזות (לתאימות לאחור)
  const [certifications, setCertifications] = useState(
    (soldier.certifications || []).map(cert =>
      typeof cert === 'string' ? { id: null, name: cert } : cert
    )
  );

  // טען רשימת תפקידים/הסמכות זמינים
  useEffect(() => {
    const loadAvailableRoles = async () => {
      try {
        const response = await api.get('/available-roles-certifications');
        setAvailableRoles(response.data.roles_certifications || []);
      } catch (error) {
        console.error('Error loading available roles:', error);
        setAvailableRoles(['נהג', 'חמל', 'קצין תורן']);
      }
    };
    loadAvailableRoles();
  }, []);

  // פונקציה שמחזירה הסמכות זמינות לפי תפקיד החייל
  const getAvailableCertificationsForSoldier = () => {
    const commanderRoles = ['ממ', 'מכ', 'סמל'];

    if (commanderRoles.includes(soldier.role)) {
      // מפקדים רואים רק קצין תורן (מפקד יוסף אוטומטית)
      return availableRoles.filter(cert => cert === 'קצין תורן');
    } else {
      // לוחמים רואים רק נהג וחמל
      return availableRoles.filter(cert => cert === 'נהג' || cert === 'חמל');
    }
  };

  // הוסף הסמכה
  const handleAddCertification = async (certName) => {
    try {
      const response = await api.post(`/soldiers/${soldier.id}/certifications`, {
        certification_name: certName
      });
      // הוסף את ההסמכה החדשה עם ה-ID שהתקבל מהשרת
      const newCert = response.data.certification;
      setCertifications([...certifications, { id: newCert.id, name: newCert.name }]);
      toast.success(`הסמכת "${certName}" נוספה בהצלחה`);
      setShowAddCertModal(false);
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בהוספת הסמכה');
    }
  };

  // מחק הסמכה
  const handleDeleteCertification = async (cert) => {
    if (!cert.id) {
      toast.error('לא ניתן למחוק הסמכה זו');
      return;
    }

    if (!window.confirm(`האם למחוק את הסמכת "${cert.name}"?`)) return;

    try {
      await api.delete(`/certifications/${cert.id}`);
      setCertifications(certifications.filter(c => c.id !== cert.id));
      toast.success('ההסמכה נמחקה בהצלחה');
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה במחיקת הסמכה');
    }
  };

  // חישוב סבב יציאה נוכחי
  const calculateCurrentRound = () => {
    if (!soldier.home_round_date) return null;

    const homeRoundDate = new Date(soldier.home_round_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    homeRoundDate.setHours(0, 0, 0, 0);

    const diffTime = today.getTime() - homeRoundDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    // Calculate round number and days into round
    // We use floor for round number to handle negative days correctly
    const roundNumber = Math.floor(diffDays / HOME_ROUND_DAYS);
    
    // Calculate positive modulo for days into round
    const daysIntoCurrentRound = ((diffDays % HOME_ROUND_DAYS) + HOME_ROUND_DAYS) % HOME_ROUND_DAYS;
    
    const nextRoundDate = new Date(homeRoundDate);
    nextRoundDate.setDate(nextRoundDate.getDate() + ((roundNumber + 1) * HOME_ROUND_DAYS));

    return {
      roundNumber: roundNumber + 1, // Display 1-based round number
      daysIntoRound: daysIntoCurrentRound,
      nextRoundDate: nextRoundDate.toLocaleDateString('he-IL'),
      daysUntilNextRound: HOME_ROUND_DAYS - daysIntoCurrentRound
    };
  };

  const currentRound = calculateCurrentRound();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-gradient-to-r from-military-600 to-military-700 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center gap-3">
            <Shield size={28} />
            <h2 className="text-2xl font-bold">{soldier.name}</h2>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X size={24} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-500 uppercase">תפקיד</label>
              <p className="font-medium text-gray-900">{soldier.role}</p>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-gray-500 uppercase">כיתה</label>
              <p className="font-medium text-gray-900">{soldier.kita || 'אין כיתה'}</p>
            </div>
          </div>

          {/* IDs */}
          {(soldier.idf_id || soldier.personal_id) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              {soldier.idf_id && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">מספר אישי</label>
                  <p className="font-medium text-gray-900">{soldier.idf_id}</p>
                </div>
              )}
              {soldier.personal_id && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase">תעודת זהות</label>
                  <p className="font-medium text-gray-900">{soldier.personal_id}</p>
                </div>
              )}
            </div>
          )}

          {/* Contact Info */}
          {(soldier.phone_number || soldier.address) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              {soldier.phone_number && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase flex items-center gap-1">
                    <Users size={14} />
                    טלפון
                  </label>
                  <p className="font-medium text-gray-900">{soldier.phone_number}</p>
                </div>
              )}
              {soldier.address && (
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 uppercase flex items-center gap-1">
                    <Shield size={14} />
                    כתובת
                  </label>
                  <p className="font-medium text-gray-900">{soldier.address}</p>
                </div>
              )}
            </div>
          )}

          {/* Emergency Contact */}
          {(soldier.emergency_contact_name || soldier.emergency_contact_number) && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3">איש קשר לחירום</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {soldier.emergency_contact_name && (
                  <div className="space-y-1">
                    <label className="text-xs text-gray-500 uppercase">שם</label>
                    <p className="font-medium text-gray-900">{soldier.emergency_contact_name}</p>
                  </div>
                )}
                {soldier.emergency_contact_number && (
                  <div className="space-y-1">
                    <label className="text-xs text-gray-500 uppercase">טלפון</label>
                    <p className="font-medium text-gray-900">{soldier.emergency_contact_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Military Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
            {soldier.pakal && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">פק״ל</label>
                <p className="font-medium text-gray-900">{soldier.pakal}</p>
              </div>
            )}
            {soldier.recruit_date && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">תאריך גיוס</label>
                <p className="font-medium text-gray-900">{new Date(soldier.recruit_date).toLocaleDateString('he-IL')}</p>
              </div>
            )}
            {soldier.birth_date && (
              <div className="space-y-1">
                <label className="text-xs text-gray-500 uppercase">תאריך לידה</label>
                <p className="font-medium text-gray-900">{new Date(soldier.birth_date).toLocaleDateString('he-IL')}</p>
              </div>
            )}
          </div>

          {/* Home Round - סבב יציאה */}
          {currentRound && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Shield size={20} className="text-military-600" />
                סבב יציאה נוכחי
              </h3>
              <div className="bg-military-50 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">סבב מספר:</span>
                  <span className="font-bold text-military-700">{currentRound.roundNumber}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">יום בסבב:</span>
                  <span className="font-bold text-military-700">{currentRound.daysIntoRound + 1} מתוך {HOME_ROUND_DAYS}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">ימים עד סבב הבא:</span>
                  <span className="font-bold text-military-700">{currentRound.daysUntilNextRound}</span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-military-200">
                  <span className="text-gray-700">תאריך סבב הבא:</span>
                  <span className="font-bold text-military-700">{currentRound.nextRoundDate}</span>
                </div>
              </div>
            </div>
          )}

          {/* Certifications */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <Shield size={20} className="text-military-600" />
                הסמכות ({certifications.length})
              </h3>
              <button
                onClick={() => setShowAddCertModal(true)}
                className="btn-primary text-sm px-3 py-1 flex items-center gap-1"
              >
                <Plus size={16} />
                הוסף הסמכה
              </button>
            </div>
            {certifications.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {certifications.map((cert, index) => {
                  const commanderRoles = ['ממ', 'מכ', 'סמל'];
                  const isCommanderCert = cert.name === 'מפקד' && commanderRoles.includes(soldier.role);

                  return (
                    <span
                      key={cert.id || `cert-${index}-${cert.name}`}
                      className={`badge ${isCommanderCert ? 'badge-green' : 'badge-blue'} flex items-center gap-2 group`}
                      title={isCommanderCert ? 'הסמכה אוטומטית למפקדים' : ''}
                    >
                      {cert.name}
                      {isCommanderCert && <span className="text-xs">(אוטומטי)</span>}
                      {!isCommanderCert && (
                        <button
                          onClick={() => handleDeleteCertification(cert)}
                          className="opacity-0 group-hover:opacity-100 hover:text-red-600 transition-opacity"
                          title="מחק הסמכה"
                          disabled={!cert.id}
                        >
                          <X size={14} />
                        </button>
                      )}
                    </span>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">אין הסמכות</p>
            )}
          </div>

          {/* Status */}
          {soldier.has_hatashab && (
            <div className="pt-4 border-t">
              <h3 className="font-bold text-gray-900 mb-3">סטטוס</h3>
              <div className="flex flex-wrap gap-2">
                <span className="badge badge-yellow">התש״ב</span>
              </div>
            </div>
          )}

          {/* Unavailable Dates */}
          {(() => {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const upcomingDates = soldier.unavailable_dates?.filter(unavailable => {
              const endDate = unavailable.end_date ? new Date(unavailable.end_date) : new Date(unavailable.date);
              endDate.setHours(23, 59, 59, 999);
              return endDate >= today;
            }) || [];

            return upcomingDates.length > 0 && (
              <div className="pt-4 border-t">
                <h3 className="font-bold text-gray-900 mb-3">תאריכי חופשה / אי זמינות קרובים</h3>
                <div className="space-y-2">
                  {upcomingDates.map((unavailable) => (
                    <div key={unavailable.id} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`badge ${
                          unavailable.unavailability_type === 'גימל' ? 'badge-yellow' :
                          unavailable.unavailability_type === 'בקשת יציאה' ? 'badge-blue' :
                          'badge-gray'
                        }`}>
                          {unavailable.unavailability_type || 'חופשה'}
                          {unavailable.quantity && ` (${unavailable.quantity})`}
                        </span>
                      </div>
                      <div className="font-medium text-gray-900">
                        {new Date(unavailable.date).toLocaleDateString('he-IL')}
                        {unavailable.end_date && (
                          <span> - {new Date(unavailable.end_date).toLocaleDateString('he-IL')}</span>
                        )}
                      </div>
                      {unavailable.reason && (
                        <div className="text-sm text-gray-600 mt-1">{unavailable.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-between items-center rounded-b-xl border-t">
          <button onClick={onEdit} className="btn-primary flex items-center gap-2">
            <Edit size={20} />
            <span>ערוך</span>
          </button>
          <button onClick={onClose} className="btn-secondary">
            סגור
          </button>
        </div>
      </div>

      {/* Add Certification Modal */}
      {showAddCertModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[70]">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">הוסף הסמכה</h3>
              <button
                onClick={() => setShowAddCertModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-4">
                בחר הסמכה להוספה עבור {soldier.name}
              </p>

              {getAvailableCertificationsForSoldier()
                .filter(role => !certifications.some(c => c.name === role))
                .map(role => (
                  <button
                    key={role}
                    onClick={() => handleAddCertification(role)}
                    className="w-full text-right p-3 border-2 border-gray-200 rounded-lg hover:border-military-600 hover:bg-military-50 transition-colors"
                  >
                    {role}
                  </button>
                ))}

              {getAvailableCertificationsForSoldier().filter(role => !certifications.some(c => c.name === role)).length === 0 && (
                <p className="text-center text-gray-500 py-4">
                  כל ההסמכות כבר נוספו
                </p>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowAddCertModal(false)}
                className="btn-secondary"
              >
                ביטול
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SoldierDetailsModal;
