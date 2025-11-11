import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Shield, Plus, Users, Trash2 } from 'lucide-react';
import ROLES from '../constants/roles';
import { toast } from 'react-toastify';

const Mahalkot = () => {
  const { user } = useAuth();
  const [mahalkot, setMahalkot] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // Reload mahalkot when the user's pluga_id changes (after creating a pluga)
    loadMahalkot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.pluga_id]);

  const loadMahalkot = async () => {
    try {
      if (!user?.pluga_id) {
        // אין פלוגה משוייכת — לא ניתן לטעון מחלקות
        setMahalkot([]);
        setLoading(false);
        return;
      }
      const response = await api.get(`/plugot/${user.pluga_id}/mahalkot`);
      setMahalkot(response.data.mahalkot || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading mahalkot:', error);
      toast.error('שגיאה בטעינת מחלקות');
      setLoading(false);
    }
  };

  const deleteMahlaka = async (mahlakaId) => {
    if (!window.confirm('בטוח שברצונך למחוק את המחלקה? פעולה זו תמחק גם את כל החיילים שבתוכה.')) return;

    try {
      await api.delete(`/mahalkot/${mahlakaId}`);
      toast.success('המחלקה נמחקה');
      loadMahalkot();
    } catch (error) {
      console.error('Delete mahlaka error', error);
      toast.error(error.response?.data?.error || 'שגיאה במחיקת המחלקה');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">מחלקות</h1>
          <p className="text-gray-600 mt-1">{mahalkot.length} מחלקות</p>
        </div>
                {user.role === 'מפ' && (
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus size={20} />
            <span>הוסף מחלקה</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mahalkot.map((mahlaka) => (
          <div key={mahlaka.id} className="card hover:shadow-lg transition-shadow" style={{ borderTop: `4px solid ${mahlaka.color}` }}>
            <div className="flex items-center justify-between mb-4">
              <div className="bg-gray-100 p-3 rounded-lg" style={{ backgroundColor: `${mahlaka.color}20` }}>
                <Shield className="w-8 h-8" style={{ color: mahlaka.color }} />
              </div>
              <div className="flex items-center gap-2">
                <span className="badge badge-blue">{mahlaka.soldiers_count} חיילים</span>
                {user.role === 'מפ' && (
                  <button
                    onClick={() => deleteMahlaka(mahlaka.id)}
                    className="btn-ghost text-red-600"
                    title="מחק מחלקה"
                  >
                    <Trash2 size={18} />
                  </button>
                )}
              </div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">מחלקה {mahlaka.number}</h3>
            <div className="flex items-center gap-2 text-gray-600">
              <Users size={16} />
              <span className="text-sm">{mahlaka.soldiers_count} לוחמים</span>
            </div>
          </div>
        ))}
      </div>

      {mahalkot.length === 0 && (
        <div className="text-center py-12">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">אין מחלקות במערכת</p>
        </div>
      )}

      {showModal && (
        <MahlakaModal
          plugaId={user.pluga_id}
          onClose={() => setShowModal(false)}
          onSave={() => {
            setShowModal(false);
            loadMahalkot();
          }}
        />
      )}
    </div>
  );
};

// roles imported from constants

const MahlakaModal = ({ plugaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    number: '',
    color: '#' + Math.floor(Math.random()*16777215).toString(16),
  });
  const [loading, setLoading] = useState(false);
  const [createdMahlakaId, setCreatedMahlakaId] = useState(null);
  const [showSoldiersImport, setShowSoldiersImport] = useState(false);
  const [soldiersFormData, setSoldiersFormData] = useState({
    mm: { name: '', date: '' },
    samal: { name: '', date: '' },
    mkXa: { name: '', date: '' },
    mkXb: { name: '', date: '' },
    mkXg: { name: '', date: '' },
    kitaA: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
    kitaB: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
    kitaG: { soldiers: [{ name: '', role: 'לוחם' }], date: '' }
  });
  const [soldierImportLoading, setSoldierImportLoading] = useState(false);
  const [useSharedDate, setUseSharedDate] = useState(false);
  const [sharedDate, setSharedDate] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (!plugaId) {
        toast.error('ראשית צור פלוגה לפני הוספת מחלקה');
        return;
      }

      const response = await api.post('/mahalkot', { ...formData, pluga_id: plugaId });
      const mahlaka = response.data.mahlaka || response.data;
      setCreatedMahlakaId(mahlaka.id);
      toast.success('המחלקה נוצרה בהצלחה');
      setShowSoldiersImport(true);
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה ביצירת מחלקה');
      setLoading(false);
    }
  };

  const parseSoldiersInput = (text) => {
    const lines = text.trim().split('\n').filter(l => l.trim());
    const soldiers = [];
    let currentKita = '';
    let currentKitaDate = '';

    lines.forEach((line) => {
      line = line.trim();
      if (!line) return;

      // Check if this is a kita header (starts with "כיתה" or "מחלקה")
      const kitaMatch = line.match(/^(כיתה|מחלקה)\s+([^\s-]+)\s*-\s*(.+)$/);
      if (kitaMatch) {
        currentKita = kitaMatch[2].trim();
        currentKitaDate = kitaMatch[3].trim();
        return;
      }

      // Check if this is a role line (תפקיד - שם - תאריך)
      // Roles: מ"מ, סמל, מ"כ, נהג, etc.
      const roleMatch = line.match(/^([א-ת״ן\s"]+?)\s*-\s*(.+?)\s*(?:-\s*(.+))?$/);
      if (roleMatch) {
        const role = roleMatch[1].trim();
        const name = roleMatch[2].trim();
        const date = roleMatch[3]?.trim() || currentKitaDate || '';
        
        // Normalize role (remove typographic quotes) and check known prefixes
        const normRole = role.replace(/[\"״]/g, '').trim();
        if (normRole.includes('ממ') || normRole.includes('מכ') || normRole === 'סמל' || normRole.includes('נהג')) {
          soldiers.push({ name, role: normRole, kita: currentKita, unavailable_date: date });
          return;
        }
      }

      // Otherwise, it's a soldier name
      if (line && !line.match(/^שמות|^כיתה/i)) {
        // Check if name has a role suffix (like "אביב גמזו - נהג")
        const nameRoleMatch = line.match(/^(.+?)\s*-\s*(נהג)$/);
        if (nameRoleMatch) {
          soldiers.push({ 
            name: nameRoleMatch[1].trim(), 
            role: nameRoleMatch[2].trim(), 
            kita: currentKita,
            unavailable_date: currentKitaDate 
          });
        } else {
          soldiers.push({ 
            name: line, 
            role: 'לוחם',
            kita: currentKita,
            unavailable_date: currentKitaDate 
          });
        }
      }
    });

    return soldiers;
  };

  const buildSoldiersListFromForm = () => {
    const soldiers = [];
    const mahlakaNum = formData.number;

    const formatDateForBackend = (d) => {
      if (!d) return '';
      // if already in DD.MM.YYYY
      if (/^\d{2}\.\d{2}\.\d{4}$/.test(d)) return d;
      // if in yyyy-mm-dd
      const m = d.match(/^(\d{4})-(\d{2})-(\d{2})$/);
      if (m) return `${m[3]}.${m[2]}.${m[1]}`;
      return d;
    };

    // Add ממ"ו
    if (soldiersFormData.mm.name) {
      soldiers.push({ 
        name: soldiersFormData.mm.name, 
        role: 'מ"מ', 
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mm.date),
        mahlaka_id: createdMahlakaId
      });
    }

    // Add סמל
    if (soldiersFormData.samal.name) {
      soldiers.push({ 
        name: soldiersFormData.samal.name, 
        role: 'סמל', 
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.samal.date),
        mahlaka_id: createdMahlakaId
      });
    }

    // Add מ"כ לכל כיתה
    if (soldiersFormData.mkXa.name) {
      soldiers.push({ 
        name: soldiersFormData.mkXa.name, 
        role: `מ"כ ${mahlakaNum}א`, 
        kita: `${mahlakaNum}א`, 
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXa.date),
        mahlaka_id: createdMahlakaId
      });
    }
    if (soldiersFormData.mkXb.name) {
      soldiers.push({ 
        name: soldiersFormData.mkXb.name, 
        role: `מ"כ ${mahlakaNum}ב`, 
        kita: `${mahlakaNum}ב`, 
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXb.date),
        mahlaka_id: createdMahlakaId
      });
    }
    if (soldiersFormData.mkXg.name) {
      soldiers.push({ 
        name: soldiersFormData.mkXg.name, 
        role: `מ"כ ${mahlakaNum}ג`, 
        kita: `${mahlakaNum}ג`, 
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXg.date),
        mahlaka_id: createdMahlakaId
      });
    }

    // Add soldiers from כיתה א
    soldiersFormData.kitaA.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: soldier.role,
          kita: `${mahlakaNum}א`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaA.date),
          mahlaka_id: createdMahlakaId
        });
      }
    });

    // Add soldiers from כיתה ב
    soldiersFormData.kitaB.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: soldier.role,
          kita: `${mahlakaNum}ב`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaB.date),
          mahlaka_id: createdMahlakaId
        });
      }
    });

    // Add soldiers from כיתה ג
    soldiersFormData.kitaG.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: soldier.role,
          kita: `${mahlakaNum}ג`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaG.date),
          mahlaka_id: createdMahlakaId
        });
      }
    });

    return soldiers;
  };

  const handleSoldiersImport = async (e) => {
    e.preventDefault();

    const soldiersList = buildSoldiersListFromForm();

    if (soldiersList.length === 0) {
      toast.warning('אנא הוסף לפחות חייל אחד או סמל/מ"מ"');
      return;
    }

    setSoldierImportLoading(true);

    try {
      const response = await api.post('/soldiers/bulk', {
        mahlaka_id: createdMahlakaId,
        soldiers: soldiersList
      });

      if (response.data.success_count > 0) {
        toast.success(`${response.data.success_count} חיילים הוספו בהצלחה`);
      }

      if (response.data.errors && response.data.errors.length > 0) {
        response.data.errors.slice(0, 5).forEach(err => toast.warning(err));
        if (response.data.errors.length > 5) {
          toast.info(`ועוד ${response.data.errors.length - 5} שגיאות נוספות`);
        }
      }

      setTimeout(() => {
        setCreatedMahlakaId(null);
        setShowSoldiersImport(false);
        setSoldiersFormData({
          mm: { name: '', date: '' },
          samal: { name: '', date: '' },
          mkXa: { name: '', date: '' },
          mkXb: { name: '', date: '' },
          mkXg: { name: '', date: '' },
          kitaA: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
          kitaB: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
          kitaG: { soldiers: [{ name: '', role: 'לוחם' }], date: '' }
        });
        onSave();
      }, 1000);
    } catch (error) {
      toast.error(error.response?.data?.error || 'שגיאה בהוספת חיילים');
    } finally {
      setSoldierImportLoading(false);
    }
  };

  const handleSkipSoldiers = () => {
    setCreatedMahlakaId(null);
    setShowSoldiersImport(false);
    setSoldiersFormData({
      mm: { name: '', date: '' },
      samal: { name: '', date: '' },
      mkXa: { name: '', date: '' },
      mkXb: { name: '', date: '' },
      mkXg: { name: '', date: '' },
      kitaA: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
      kitaB: { soldiers: [{ name: '', role: 'לוחם' }], date: '' },
      kitaG: { soldiers: [{ name: '', role: 'לוחם' }], date: '' }
    });
    onSave();
  };

  if (showSoldiersImport) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full p-6 max-h-[90vh] overflow-y-auto">
          <h2 className="text-2xl font-bold mb-4">ניהול מחלקה {formData.number}</h2>

          <form onSubmit={handleSoldiersImport} className="space-y-6">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={useSharedDate}
                  onChange={(e) => setUseSharedDate(e.target.checked)}
                />
                <span>כולם יוצאים באותו תאריך</span>
              </label>

              {useSharedDate && (
                <input
                  type="date"
                  value={sharedDate}
                  onChange={(e) => setSharedDate(e.target.value)}
                  className="input-field w-48"
                />
              )}
            </div>
            
            {/* Block 1: ממ"ו */}
            <div className="border-l-4 border-military-600 pl-4">
              <h3 className="font-bold text-lg mb-3">מ"מ (מפקד מחלקה)</h3>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="שם ממ״ו"
                  value={soldiersFormData.mm.name}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mm: { ...soldiersFormData.mm, name: e.target.value } })}
                  className="input-field"
                />
                <input
                  type="date"
                  value={soldiersFormData.mm.date}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mm: { ...soldiersFormData.mm, date: e.target.value } })}
                  className="input-field"
                />
              </div>
            </div>

            {/* Block 2: סמל */}
            <div className="border-l-4 border-blue-600 pl-4">
              <h3 className="font-bold text-lg mb-3">סמל</h3>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="שם סמל"
                  value={soldiersFormData.samal.name}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, samal: { ...soldiersFormData.samal, name: e.target.value } })}
                  className="input-field"
                />
                <input
                  type="date"
                  value={soldiersFormData.samal.date}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, samal: { ...soldiersFormData.samal, date: e.target.value } })}
                  className="input-field"
                />
              </div>
            </div>

            {/* Block 3: מ"כ */}
            <div className="border-l-4 border-green-600 pl-4">
              <h3 className="font-bold text-lg mb-3">מ"כ (מפקדי כיתה)</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder={`שם מ"כ כיתה ${formData.number}א`}
                    value={soldiersFormData.mkXa.name}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXa: { ...soldiersFormData.mkXa, name: e.target.value } })}
                    className="input-field"
                  />
                  <input
                    type="date"
                    value={soldiersFormData.mkXa.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXa: { ...soldiersFormData.mkXa, date: e.target.value } })}
                    className="input-field"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder={`שם מ"כ כיתה ${formData.number}ב`}
                    value={soldiersFormData.mkXb.name}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXb: { ...soldiersFormData.mkXb, name: e.target.value } })}
                    className="input-field"
                  />
                  <input
                    type="date"
                    value={soldiersFormData.mkXb.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXb: { ...soldiersFormData.mkXb, date: e.target.value } })}
                    className="input-field"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder={`שם מ"כ כיתה ${formData.number}ג`}
                    value={soldiersFormData.mkXg.name}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXg: { ...soldiersFormData.mkXg, name: e.target.value } })}
                    className="input-field"
                  />
                  <input
                    type="date"
                    value={soldiersFormData.mkXg.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXg: { ...soldiersFormData.mkXg, date: e.target.value } })}
                    className="input-field"
                  />
                </div>
              </div>
            </div>

            {/* Block 4: חיילים כיתה א */}
            <div className="border-l-4 border-orange-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}א</h3>
              <div className="mb-3">
                <input
                  type="date"
                  value={soldiersFormData.kitaA.date}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, date: e.target.value } })}
                  className="input-field w-full"
                  placeholder="תאריך יציאה"
                />
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaA.soldiers.map((soldier, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaA.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', role: 'לוחם' });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, soldiers: newSoldiers } });
                      }}
                      className="input-field col-span-2"
                    />
                    <select
                      value={soldier.role}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaA.soldiers];
                        newSoldiers[idx].role = e.target.value;
                        setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, soldiers: newSoldiers } });
                      }}
                      className="input-field"
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Block 5: חיילים כיתה ב */}
            <div className="border-l-4 border-purple-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}ב</h3>
              <div className="mb-3">
                <input
                  type="date"
                  value={soldiersFormData.kitaB.date}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, date: e.target.value } })}
                  className="input-field w-full"
                  placeholder="תאריך יציאה"
                />
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaB.soldiers.map((soldier, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaB.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', role: 'לוחם' });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, soldiers: newSoldiers } });
                      }}
                      className="input-field col-span-2"
                    />
                    <select
                      value={soldier.role}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaB.soldiers];
                        newSoldiers[idx].role = e.target.value;
                        setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, soldiers: newSoldiers } });
                      }}
                      className="input-field"
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Block 6: חיילים כיתה ג */}
            <div className="border-l-4 border-pink-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}ג</h3>
              <div className="mb-3">
                <input
                  type="date"
                  value={soldiersFormData.kitaG.date}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, date: e.target.value } })}
                  className="input-field w-full"
                  placeholder="תאריך יציאה"
                />
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaG.soldiers.map((soldier, idx) => (
                  <div key={idx} className="grid grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaG.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', role: 'לוחם' });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, soldiers: newSoldiers } });
                      }}
                      className="input-field col-span-2"
                    />
                    <select
                      value={soldier.role}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaG.soldiers];
                        newSoldiers[idx].role = e.target.value;
                        setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, soldiers: newSoldiers } });
                      }}
                      className="input-field"
                    >
                      {ROLES.map((role) => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button type="submit" disabled={soldierImportLoading} className="flex-1 btn-primary">
                {soldierImportLoading ? 'שומר...' : 'שמור מחלקה עם חיילים'}
              </button>
              <button type="button" onClick={handleSkipSoldiers} className="flex-1 btn-secondary">
                דלג (יצירת מחלקה בלבד)
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-6">הוספת מחלקה חדשה</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">מספר מחלקה</label>
            <input
              type="number"
              value={formData.number}
              onChange={(e) => setFormData({ ...formData, number: parseInt(e.target.value) })}
              className="input-field"
              required
              min="1"
            />
          </div>

          <div>
            <label className="label">צבע</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-16 h-10 rounded cursor-pointer"
              />
              <input
                type="text"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="input-field flex-1"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button type="submit" disabled={loading} className="flex-1 btn-primary">
              {loading ? 'יוצר...' : 'צור מחלקה'}
            </button>
            <button type="button" onClick={onClose} className="flex-1 btn-secondary">ביטול</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Mahalkot;
