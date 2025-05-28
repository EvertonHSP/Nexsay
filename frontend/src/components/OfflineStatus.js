import React from 'react';
import { useAuth } from '../context/AuthContext';
import '../index.css';

const OfflineStatus = () => {
  const { isOffline } = useAuth();

  if (!isOffline) return null;

  return (
    <div className="offline-banner">
      <div className="offline-content">
        ⚠️ Você está offline. Algumas funcionalidades podem estar limitadas.
      </div>
    </div>
  );
};

export default OfflineStatus;