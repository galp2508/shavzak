import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { FileText, Plus, Clock } from 'lucide-react';
import { toast } from 'react-toastify';

const Templates = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await api.get(`/plugot/${user.pluga_id}/assignment-templates`);
      setTemplates(response.data.templates);
    } catch (error) {
      toast.error('שגיאה בטעינת תבניות');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">תבניות משימות</h1>
          <p className="text-gray-600 mt-1">{templates.length} תבניות</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus size={20} />
          <span>תבנית חדשה</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <div key={template.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-military-100 p-3 rounded-lg">
                <FileText className="w-6 h-6 text-military-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900">{template.name}</h3>
                <p className="text-sm text-gray-600">{template.assignment_type}</p>
              </div>
            </div>

            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Clock size={16} />
                <span>{template.length_in_hours} שעות × {template.times_per_day} פעמים ביום</span>
              </div>
              <div className="flex gap-2 flex-wrap mt-3">
                {template.commanders_needed > 0 && (
                  <span className="badge badge-purple">{template.commanders_needed} מפקדים</span>
                )}
                {template.drivers_needed > 0 && (
                  <span className="badge badge-blue">{template.drivers_needed} נהגים</span>
                )}
                {template.soldiers_needed > 0 && (
                  <span className="badge badge-green">{template.soldiers_needed} לוחמים</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Templates;
