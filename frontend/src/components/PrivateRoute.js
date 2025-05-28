import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
  const { user, loading, isAuthenticated, isOffline } = useAuth();
  const location = useLocation();

 
  useEffect(() => {
    if (!loading && !isAuthenticated && !isOffline) {
      
    }
  }, [loading, isAuthenticated, isOffline]);

  if (loading) {
    return (
      <div className="loading-container">
        <div>Verificando autenticação...</div>
      </div>
    );
  }

  
  if (isOffline && user) {
    return children;
  }

  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  
  return children;
};

export default PrivateRoute;