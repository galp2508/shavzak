import React from 'react';

const MaintenanceScreen = ({ onRetry }) => {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      fontFamily: 'Arial, sans-serif',
      textAlign: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        borderRadius: '20px',
        padding: '40px',
        maxWidth: '500px',
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)'
      }}>
        {/* אייקון כלי עבודה */}
        <div style={{ fontSize: '80px', marginBottom: '20px' }}>
          🔧
        </div>

        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '20px',
          fontWeight: 'bold'
        }}>
          אנחנו תחת שיפוצים
        </h1>

        <p style={{
          fontSize: '1.2rem',
          marginBottom: '30px',
          opacity: 0.9
        }}>
          השרת לא זמין כרגע
          <br />
          אנא נסה שוב בעוד מספר שניות
        </p>

        {/* כפתור נסה שוב */}
        <button
          onClick={onRetry}
          style={{
            background: 'white',
            color: '#667eea',
            border: 'none',
            borderRadius: '10px',
            padding: '15px 40px',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
            marginBottom: '20px'
          }}
          onMouseOver={(e) => {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
          }}
          onMouseOut={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
          }}
        >
          🔄 נסה שוב
        </button>

        {/* אנימציית נקודות */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '10px',
          marginTop: '10px'
        }}>
          <div className="dot" style={{
            width: '15px',
            height: '15px',
            borderRadius: '50%',
            background: 'white',
            animation: 'bounce 1.4s infinite ease-in-out both',
            animationDelay: '-0.32s'
          }}></div>
          <div className="dot" style={{
            width: '15px',
            height: '15px',
            borderRadius: '50%',
            background: 'white',
            animation: 'bounce 1.4s infinite ease-in-out both',
            animationDelay: '-0.16s'
          }}></div>
          <div className="dot" style={{
            width: '15px',
            height: '15px',
            borderRadius: '50%',
            background: 'white',
            animation: 'bounce 1.4s infinite ease-in-out both'
          }}></div>
        </div>
      </div>

      {/* CSS Keyframes בתוך style tag */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default MaintenanceScreen;
