import { Shield } from 'lucide-react';

const Loading = () => {
  return (
    <div className="min-h-screen bg-military-50 flex items-center justify-center">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <Shield className="w-16 h-16 text-military-600 animate-pulse" />
        </div>
        <div className="spinner mx-auto mb-4"></div>
        <p className="text-gray-600 font-medium">טוען...</p>
      </div>
    </div>
  );
};

export default Loading;
