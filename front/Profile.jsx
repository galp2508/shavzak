import { useAuth } from '../context/AuthContext';
import { User, Shield, Mail, Phone, MapPin, Award } from 'lucide-react';

const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">הפרופיל שלי</h1>

      <div className="card">
        <div className="flex items-center gap-6 mb-6">
          <div className="bg-military-600 p-6 rounded-full">
            <User className="w-12 h-12 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{user?.full_name}</h2>
            <p className="text-gray-600">{user?.username}@</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-gray-200">
          <InfoItem icon={Award} label="תפקיד" value={user?.role} />
          <InfoItem icon={Shield} label="פלוגה" value={user?.pluga?.name || '-'} />
          {user?.mahlaka && (
            <InfoItem icon={Shield} label="מחלקה" value={`מחלקה ${user.mahlaka.number}`} />
          )}
          {user?.kita && (
            <InfoItem icon={Shield} label="כיתה" value={`כיתה ${user.kita}`} />
          )}
        </div>
      </div>
    </div>
  );
};

const InfoItem = ({ icon: Icon, label, value }) => (
  <div className="flex items-center gap-3">
    <div className="bg-gray-100 p-2 rounded-lg">
      <Icon size={20} className="text-gray-600" />
    </div>
    <div>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="font-medium text-gray-900">{value}</p>
    </div>
  </div>
);

export default Profile;
