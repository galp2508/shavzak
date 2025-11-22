import { useState } from 'react';
import api from '../../services/api';
import { toast } from 'react-toastify';
import { Shield, X, Users, Plus, Edit, Trash2, UserCheck } from 'lucide-react';
import SoldierEditModal from './SoldierEditModal';
import SoldierDetailsModal from './SoldierDetailsModal';
import { SoldierStatusBadge, StatusChangeModal } from '../SoldierStatusBadge';

const SoldiersModal = ({ mahlaka, soldiers, onClose, onDelete, onRefresh }) => {
  const [editingSoldier, setEditingSoldier] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [viewingSoldier, setViewingSoldier] = useState(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedSoldier, setSelectedSoldier] = useState(null);

  const getRoleBadge = (role) => {
    const badges = {
      'לוחם': 'badge-green',
      'מ"מ': 'badge-purple',
      'מ"כ': 'badge-purple',
      'סמל': 'badge-yellow',
    };
    return badges[role] || 'badge-blue';
  };

  const handleViewDetails = async (soldier) => {
    try {
      const response = await api.get(`/soldiers/${soldier.id}`);
      setViewingSoldier(response.data.soldier);
      setShowDetailsModal(true);
    } catch (error) {
      toast.error('שגיאה בטעינת פרטי חייל');
      console.error(error);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-gradient-to-r from-military-600 to-military-700 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
            <div className="flex items-center gap-3">
              <Shield size={28} style={{ color: mahlaka.color }} />
              <div>
                <h2 className="text-2xl font-bold">מחלקה {mahlaka.number}</h2>
                <p className="text-military-100">{soldiers.length} חיילים</p>
              </div>
            </div>
            <button onClick={onClose} className="text-white hover:text-gray-200">
              <X size={24} />
            </button>
          </div>

          <div className="p-6">
            {soldiers.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p>אין חיילים במחלקה זו</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        שם
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        תפקיד
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        כיתה
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        פעולות
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {soldiers.map((soldier) => (
                      <tr key={soldier.id} className="hover:bg-gray-50">
                        <td
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                          onClick={() => handleViewDetails(soldier)}
                        >
                          <div className="flex items-center gap-3">
                            <div className="bg-military-100 p-2 rounded-full">
                              <Shield size={16} className="text-military-600" />
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="font-medium text-gray-900 hover:text-military-600 transition-colors">
                                {soldier.name}
                              </div>
                              <SoldierStatusBadge
                                soldier={soldier}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedSoldier(soldier);
                                  setShowStatusModal(true);
                                }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`badge ${getRoleBadge(soldier.role)}`}>
                            {soldier.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {soldier.kita || 'אין כיתה'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedSoldier(soldier);
                                setShowStatusModal(true);
                              }}
                              className="text-green-600 hover:text-green-800"
                              title="שינוי סטטוס"
                            >
                              <UserCheck size={18} />
                            </button>
                            <button
                              onClick={() => {
                                setEditingSoldier(soldier);
                                setShowEditModal(true);
                              }}
                              className="text-blue-600 hover:text-blue-800"
                              title="ערוך"
                            >
                              <Edit size={18} />
                            </button>
                            <button
                              onClick={() => onDelete(soldier.id)}
                              className="text-red-600 hover:text-red-800"
                              title="מחק"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex justify-between items-center rounded-b-xl border-t">
            <button
              onClick={() => {
                setEditingSoldier(null);
                setShowEditModal(true);
              }}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={20} />
              <span>הוסף חייל</span>
            </button>
            <button onClick={onClose} className="btn-secondary">
              סגור
            </button>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <SoldierEditModal
          soldier={editingSoldier}
          mahlakaId={mahlaka.id}
          onClose={() => {
            setShowEditModal(false);
            setEditingSoldier(null);
          }}
          onSave={() => {
            setShowEditModal(false);
            setEditingSoldier(null);
            onRefresh();
          }}
        />
      )}

      {/* Details Modal */}
      {showDetailsModal && viewingSoldier && (
        <SoldierDetailsModal
          soldier={viewingSoldier}
          onClose={() => {
            setShowDetailsModal(false);
            setViewingSoldier(null);
          }}
          onEdit={() => {
            setEditingSoldier(viewingSoldier);
            setShowDetailsModal(false);
            setShowEditModal(true);
          }}
        />
      )}

      {/* Status Change Modal */}
      {showStatusModal && selectedSoldier && (
        <StatusChangeModal
          soldier={selectedSoldier}
          onClose={() => {
            setShowStatusModal(false);
            setSelectedSoldier(null);
          }}
          onUpdate={() => {
            onRefresh();
            setShowStatusModal(false);
            setSelectedSoldier(null);
          }}
        />
      )}
    </>
  );
};

export default SoldiersModal;
