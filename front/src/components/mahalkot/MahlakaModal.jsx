import { useState, useEffect } from 'react';
import api from '../../services/api';
import { toast } from 'react-toastify';

const MahlakaModal = ({ plugaId, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    number: '',
    color: '#' + Math.floor(Math.random()*16777215).toString(16),
  });
  const [loading, setLoading] = useState(false);
  const [createdMahlakaId, setCreatedMahlakaId] = useState(null);
  const [showSoldiersImport, setShowSoldiersImport] = useState(false);
  const [soldiersFormData, setSoldiersFormData] = useState({
    mm: { name: '', date: '', role: 'ממ', certifications: [] },
    samal: { name: '', date: '', role: 'סמל', certifications: [] },
    mkXa: { name: '', date: '', role: 'מכ', certifications: [] },
    mkXb: { name: '', date: '', role: 'מכ', certifications: [] },
    mkXg: { name: '', date: '', role: 'מכ', certifications: [] },
    kitaA: { soldiers: [{ name: '', certifications: [] }], date: '' },
    kitaB: { soldiers: [{ name: '', certifications: [] }], date: '' },
    kitaG: { soldiers: [{ name: '', certifications: [] }], date: '' }
  });
  const [soldierImportLoading, setSoldierImportLoading] = useState(false);
  const [useSharedDate, setUseSharedDate] = useState(false);
  const [sharedDate, setSharedDate] = useState('');
  const [availableCertifications, setAvailableCertifications] = useState([]);

  useEffect(() => {
    const fetchCertifications = async () => {
      try {
        const response = await api.get('/available-roles-certifications');
        setAvailableCertifications(response.data.roles_certifications || []);
      } catch (error) {
        console.error('Error loading certifications:', error);
      }
    };
    fetchCertifications();
  }, []);

  // פונקציה שמחזירה הסמכות זמינות לפי תפקיד
  const getAvailableCertificationsForRole = (role) => {
    const commanderRoles = ['ממ', 'מכ', 'סמל'];

    if (commanderRoles.includes(role)) {
      // מפקדים רואים רק קצין תורן (מפקד יוסף אוטומטית)
      return availableCertifications.filter(cert => cert === 'קצין תורן');
    } else {
      // לוחמים רואים רק נהג וחמל
      return availableCertifications.filter(cert => cert === 'נהג' || cert === 'חמל');
    }
  };

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
        role: 'ממ',
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mm.date),
        mahlaka_id: createdMahlakaId,
        certifications: soldiersFormData.mm.certifications || []
      });
    }

    // Add סמל
    if (soldiersFormData.samal.name) {
      soldiers.push({
        name: soldiersFormData.samal.name,
        role: 'סמל',
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.samal.date),
        mahlaka_id: createdMahlakaId,
        certifications: soldiersFormData.samal.certifications || []
      });
    }

    // Add מ"כ לכל כיתה
    if (soldiersFormData.mkXa.name) {
      soldiers.push({
        name: soldiersFormData.mkXa.name,
        role: 'מכ',
        kita: `${mahlakaNum}א`,
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXa.date),
        mahlaka_id: createdMahlakaId,
        certifications: soldiersFormData.mkXa.certifications || []
      });
    }
    if (soldiersFormData.mkXb.name) {
      soldiers.push({
        name: soldiersFormData.mkXb.name,
        role: 'מכ',
        kita: `${mahlakaNum}ב`,
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXb.date),
        mahlaka_id: createdMahlakaId,
        certifications: soldiersFormData.mkXb.certifications || []
      });
    }
    if (soldiersFormData.mkXg.name) {
      soldiers.push({
        name: soldiersFormData.mkXg.name,
        role: 'מכ',
        kita: `${mahlakaNum}ג`,
        unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.mkXg.date),
        mahlaka_id: createdMahlakaId,
        certifications: soldiersFormData.mkXg.certifications || []
      });
    }

    // Add soldiers from כיתה א - תפקיד "לוחם" אוטומטית
    soldiersFormData.kitaA.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: 'לוחם',
          kita: `${mahlakaNum}א`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaA.date),
          mahlaka_id: createdMahlakaId,
          certifications: soldier.certifications || []
        });
      }
    });

    // Add soldiers from כיתה ב - תפקיד "לוחם" אוטומטית
    soldiersFormData.kitaB.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: 'לוחם',
          kita: `${mahlakaNum}ב`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaB.date),
          mahlaka_id: createdMahlakaId,
          certifications: soldier.certifications || []
        });
      }
    });

    // Add soldiers from כיתה ג - תפקיד "לוחם" אוטומטית
    soldiersFormData.kitaG.soldiers.forEach((soldier) => {
      if (soldier.name) {
        soldiers.push({
          name: soldier.name,
          role: 'לוחם',
          kita: `${mahlakaNum}ג`,
          unavailable_date: useSharedDate ? formatDateForBackend(sharedDate) : formatDateForBackend(soldiersFormData.kitaG.date),
          mahlaka_id: createdMahlakaId,
          certifications: soldier.certifications || []
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
          mm: { name: '', date: '', role: 'ממ', certifications: [] },
          samal: { name: '', date: '', role: 'סמל', certifications: [] },
          mkXa: { name: '', date: '', role: 'מכ', certifications: [] },
          mkXb: { name: '', date: '', role: 'מכ', certifications: [] },
          mkXg: { name: '', date: '', role: 'מכ', certifications: [] },
          kitaA: { soldiers: [{ name: '', certifications: [] }], date: '' },
          kitaB: { soldiers: [{ name: '', certifications: [] }], date: '' },
          kitaG: { soldiers: [{ name: '', certifications: [] }], date: '' }
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
      mm: { name: '', date: '', role: 'ממ', certifications: [] },
      samal: { name: '', date: '', role: 'סמל', certifications: [] },
      mkXa: { name: '', date: '', role: 'מכ', certifications: [] },
      mkXb: { name: '', date: '', role: 'מכ', certifications: [] },
      mkXg: { name: '', date: '', role: 'מכ', certifications: [] },
      kitaA: { soldiers: [{ name: '', certifications: [] }], date: '' },
      kitaB: { soldiers: [{ name: '', certifications: [] }], date: '' },
      kitaG: { soldiers: [{ name: '', certifications: [] }], date: '' }
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
              <div className={useSharedDate ? "grid grid-cols-1 gap-3" : "grid grid-cols-2 gap-3"}>
                <input
                  type="text"
				  placeholder={'שם מ"מ'}
                  value={soldiersFormData.mm.name}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mm: { ...soldiersFormData.mm, name: e.target.value } })}
                  className="input-field"
                />
                {!useSharedDate && (
                  <input
                    type="date"
                    value={soldiersFormData.mm.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mm: { ...soldiersFormData.mm, date: e.target.value } })}
                    className="input-field"
                  />
                )}
              </div>
              {soldiersFormData.mm.name && (
                <div className="mt-2">
                  <label className="block text-sm font-medium mb-1">הסמכות (Ctrl לבחירה מרובה)</label>
                  <select
                    multiple
                    value={soldiersFormData.mm.certifications || []}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setSoldiersFormData({ ...soldiersFormData, mm: { ...soldiersFormData.mm, certifications: selected } });
                    }}
                    className="input-field w-full h-20"
                  >
                    {getAvailableCertificationsForRole('ממ').map((cert) => (
                      <option key={cert} value={cert}>{cert}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Block 2: סמל */}
            <div className="border-l-4 border-blue-600 pl-4">
              <h3 className="font-bold text-lg mb-3">סמל</h3>
              <div className={useSharedDate ? "grid grid-cols-1 gap-3" : "grid grid-cols-2 gap-3"}>
                <input
                  type="text"
                  placeholder="שם סמל"
                  value={soldiersFormData.samal.name}
                  onChange={(e) => setSoldiersFormData({ ...soldiersFormData, samal: { ...soldiersFormData.samal, name: e.target.value } })}
                  className="input-field"
                />
                {!useSharedDate && (
                  <input
                    type="date"
                    value={soldiersFormData.samal.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, samal: { ...soldiersFormData.samal, date: e.target.value } })}
                    className="input-field"
                  />
                )}
              </div>
              {soldiersFormData.samal.name && (
                <div className="mt-2">
                  <label className="block text-sm font-medium mb-1">הסמכות (Ctrl לבחירה מרובה)</label>
                  <select
                    multiple
                    value={soldiersFormData.samal.certifications || []}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setSoldiersFormData({ ...soldiersFormData, samal: { ...soldiersFormData.samal, certifications: selected } });
                    }}
                    className="input-field w-full h-20"
                  >
                    {getAvailableCertificationsForRole('סמל').map((cert) => (
                      <option key={cert} value={cert}>{cert}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Block 3: מ"כ */}
            <div className="border-l-4 border-green-600 pl-4">
              <h3 className="font-bold text-lg mb-3">מ"כ (מפקדי כיתה)</h3>
              <div className="space-y-3">
                <div>
                  <div className={useSharedDate ? "grid grid-cols-1 gap-3" : "grid grid-cols-2 gap-3"}>
                    <input
                      type="text"
                      placeholder={`שם מ"כ כיתה ${formData.number}א`}
                      value={soldiersFormData.mkXa.name}
                      onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXa: { ...soldiersFormData.mkXa, name: e.target.value } })}
                      className="input-field"
                    />
                    {!useSharedDate && (
                      <input
                        type="date"
                        value={soldiersFormData.mkXa.date}
                        onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXa: { ...soldiersFormData.mkXa, date: e.target.value } })}
                        className="input-field"
                      />
                    )}
                  </div>
                  {soldiersFormData.mkXa.name && (
                    <div className="mt-2">
                      <select
                        multiple
                        value={soldiersFormData.mkXa.certifications || []}
                        onChange={(e) => {
                          const selected = Array.from(e.target.selectedOptions, option => option.value);
                          setSoldiersFormData({ ...soldiersFormData, mkXa: { ...soldiersFormData.mkXa, certifications: selected } });
                        }}
                        className="input-field w-full h-16 text-sm"
                        title="הסמכות (Ctrl)"
                      >
                        {getAvailableCertificationsForRole('מכ').map((cert) => (
                          <option key={cert} value={cert}>{cert}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                <div>
                  <div className={useSharedDate ? "grid grid-cols-1 gap-3" : "grid grid-cols-2 gap-3"}>
                    <input
                      type="text"
                      placeholder={`שם מ"כ כיתה ${formData.number}ב`}
                      value={soldiersFormData.mkXb.name}
                      onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXb: { ...soldiersFormData.mkXb, name: e.target.value } })}
                      className="input-field"
                    />
                    {!useSharedDate && (
                      <input
                        type="date"
                        value={soldiersFormData.mkXb.date}
                        onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXb: { ...soldiersFormData.mkXb, date: e.target.value } })}
                        className="input-field"
                      />
                    )}
                  </div>
                  {soldiersFormData.mkXb.name && (
                    <div className="mt-2">
                      <select
                        multiple
                        value={soldiersFormData.mkXb.certifications || []}
                        onChange={(e) => {
                          const selected = Array.from(e.target.selectedOptions, option => option.value);
                          setSoldiersFormData({ ...soldiersFormData, mkXb: { ...soldiersFormData.mkXb, certifications: selected } });
                        }}
                        className="input-field w-full h-16 text-sm"
                        title="הסמכות (Ctrl)"
                      >
                        {getAvailableCertificationsForRole('מכ').map((cert) => (
                          <option key={cert} value={cert}>{cert}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                <div>
                  <div className={useSharedDate ? "grid grid-cols-1 gap-3" : "grid grid-cols-2 gap-3"}>
                    <input
                      type="text"
                      placeholder={`שם מ"כ כיתה ${formData.number}ג`}
                      value={soldiersFormData.mkXg.name}
                      onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXg: { ...soldiersFormData.mkXg, name: e.target.value } })}
                      className="input-field"
                    />
                    {!useSharedDate && (
                      <input
                        type="date"
                        value={soldiersFormData.mkXg.date}
                        onChange={(e) => setSoldiersFormData({ ...soldiersFormData, mkXg: { ...soldiersFormData.mkXg, date: e.target.value } })}
                        className="input-field"
                      />
                    )}
                  </div>
                  {soldiersFormData.mkXg.name && (
                    <div className="mt-2">
                      <select
                        multiple
                        value={soldiersFormData.mkXg.certifications || []}
                        onChange={(e) => {
                          const selected = Array.from(e.target.selectedOptions, option => option.value);
                          setSoldiersFormData({ ...soldiersFormData, mkXg: { ...soldiersFormData.mkXg, certifications: selected } });
                        }}
                        className="input-field w-full h-16 text-sm"
                        title="הסמכות (Ctrl)"
                      >
                        {getAvailableCertificationsForRole('מכ').map((cert) => (
                          <option key={cert} value={cert}>{cert}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Block 4: חיילים כיתה א */}
            <div className="border-l-4 border-orange-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}א</h3>
              {!useSharedDate && (
                <div className="mb-3">
                  <input
                    type="date"
                    value={soldiersFormData.kitaA.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, date: e.target.value } })}
                    className="input-field w-full"
                    placeholder="תאריך יציאה"
                  />
                </div>
              )}

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaA.soldiers.map((soldier, idx) => (
                  <div key={idx} className="flex gap-2 items-start">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaA.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', certifications: [] });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, soldiers: newSoldiers } });
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && soldier.name === '' && soldiersFormData.kitaA.soldiers.length > 1) {
                          e.preventDefault();
                          const newSoldiers = soldiersFormData.kitaA.soldiers.filter((_, i) => i !== idx);
                          setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, soldiers: newSoldiers } });
                        }
                      }}
                      className="input-field flex-1"
                    />
                    <select
                      multiple
                      value={soldier.certifications || []}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaA.soldiers];
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        newSoldiers[idx].certifications = selected;
                        setSoldiersFormData({ ...soldiersFormData, kitaA: { ...soldiersFormData.kitaA, soldiers: newSoldiers } });
                      }}
                      className="input-field w-32 h-10"
                      title="הסמכות (Ctrl לבחירה מרובה)"
                    >
                      {getAvailableCertificationsForRole('לוחם').map((cert) => (
                        <option key={cert} value={cert}>{cert}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Block 5: חיילים כיתה ב */}
            <div className="border-l-4 border-purple-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}ב</h3>
              {!useSharedDate && (
                <div className="mb-3">
                  <input
                    type="date"
                    value={soldiersFormData.kitaB.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, date: e.target.value } })}
                    className="input-field w-full"
                    placeholder="תאריך יציאה"
                  />
                </div>
              )}

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaB.soldiers.map((soldier, idx) => (
                  <div key={idx} className="flex gap-2 items-start">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaB.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', certifications: [] });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, soldiers: newSoldiers } });
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && soldier.name === '' && soldiersFormData.kitaB.soldiers.length > 1) {
                          e.preventDefault();
                          const newSoldiers = soldiersFormData.kitaB.soldiers.filter((_, i) => i !== idx);
                          setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, soldiers: newSoldiers } });
                        }
                      }}
                      className="input-field flex-1"
                    />
                    <select
                      multiple
                      value={soldier.certifications || []}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaB.soldiers];
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        newSoldiers[idx].certifications = selected;
                        setSoldiersFormData({ ...soldiersFormData, kitaB: { ...soldiersFormData.kitaB, soldiers: newSoldiers } });
                      }}
                      className="input-field w-32 h-10"
                      title="הסמכות (Ctrl לבחירה מרובה)"
                    >
                      {getAvailableCertificationsForRole('לוחם').map((cert) => (
                        <option key={cert} value={cert}>{cert}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Block 6: חיילים כיתה ג */}
            <div className="border-l-4 border-pink-600 pl-4">
              <h3 className="font-bold text-lg mb-3">חיילים כיתה {formData.number}ג</h3>
              {!useSharedDate && (
                <div className="mb-3">
                  <input
                    type="date"
                    value={soldiersFormData.kitaG.date}
                    onChange={(e) => setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, date: e.target.value } })}
                    className="input-field w-full"
                    placeholder="תאריך יציאה"
                  />
                </div>
              )}

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {soldiersFormData.kitaG.soldiers.map((soldier, idx) => (
                  <div key={idx} className="flex gap-2 items-start">
                    <input
                      type="text"
                      placeholder="שם חייל"
                      value={soldier.name}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaG.soldiers];
                        newSoldiers[idx].name = e.target.value;
                        if (idx === newSoldiers.length - 1 && e.target.value.trim()) {
                          newSoldiers.push({ name: '', certifications: [] });
                        }
                        setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, soldiers: newSoldiers } });
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Backspace' && soldier.name === '' && soldiersFormData.kitaG.soldiers.length > 1) {
                          e.preventDefault();
                          const newSoldiers = soldiersFormData.kitaG.soldiers.filter((_, i) => i !== idx);
                          setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, soldiers: newSoldiers } });
                        }
                      }}
                      className="input-field flex-1"
                    />
                    <select
                      multiple
                      value={soldier.certifications || []}
                      onChange={(e) => {
                        const newSoldiers = [...soldiersFormData.kitaG.soldiers];
                        const selected = Array.from(e.target.selectedOptions, option => option.value);
                        newSoldiers[idx].certifications = selected;
                        setSoldiersFormData({ ...soldiersFormData, kitaG: { ...soldiersFormData.kitaG, soldiers: newSoldiers } });
                      }}
                      className="input-field w-32 h-10"
                      title="הסמכות (Ctrl לבחירה מרובה)"
                    >
                      {getAvailableCertificationsForRole('לוחם').map((cert) => (
                        <option key={cert} value={cert}>{cert}</option>
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

export default MahlakaModal;
