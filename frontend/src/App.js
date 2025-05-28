import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ContatosProvider } from './context/ContatosContext';
import { ConversaProvider } from './context/ConversaContext'; 
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Home from './pages/Home';
import PrivateRoute from './components/PrivateRoute';
import Layout from './components/Layout';
import Verify2FA from './pages/Auth/Verify2FA';
import OfflineStatus from './components/OfflineStatus';

function App() {
  return (
    <Router>
      <AuthProvider>
        <ContatosProvider>
          <ConversaProvider> 
            <OfflineStatus />
            <Routes>
              {/* Rotas públicas */}
              <Route path="/Login" element={<Login />} />
              <Route path="/Register" element={<Register />} />
              <Route path="/Verify-2fa" element={<Verify2FA />} />

              {/* Rotas protegidas */}
              <Route element={<Layout />}>
                <Route
                  path="/"
                  element={
                    <PrivateRoute>
                      <Home />
                    </PrivateRoute>
                  }
                />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ConversaProvider>
        </ContatosProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;