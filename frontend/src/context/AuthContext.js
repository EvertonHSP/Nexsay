import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authApi from '../api/auth';
import { saveUserSession, getCurrentUser, clearUserSession } from '../database/usuarios';
import db from '../database/db'; 

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isOffline, setIsOffline] = useState(false);
  const navigate = useNavigate();


  useEffect(() => {
    const handleOnline = () => {
      console.log('Conexão restabelecida');
      setIsOffline(false);
    };
    
    const handleOffline = () => {
      console.log('Modo offline ativado');
      setIsOffline(true);
    };

   
    setIsOffline(!navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  
  const checkSession = async (jwtToken) => {
    try {
      const response = await authApi.getProfile(jwtToken);
      return {
        isValid: true,
        userData: response
      };
    } catch (error) {
      if (error.response?.status === 401) {
        return { isValid: false };
      }
      console.error('Erro ao verificar sessão:', error);
      throw error;
    }
  };

  
  const handleLogout = useCallback(async () => {
    try {
      if (user?.jwt_token && !isOffline) {
        await authApi.logout(user.jwt_token);
      }
    } catch (error) {
      console.error('Erro no logout API:', error);
    } finally {
      try {
        await clearUserSession();
        setUser(null);
        setIsOffline(false);
        navigate('/login');
      } catch (dbError) {
        console.error('Erro ao limpar sessão:', dbError);
      }
    }
  }, [user?.jwt_token, isOffline, navigate]);

  
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        
        if (!db.isOpen()) {
          await db.open().catch(err => {
            console.error('Erro ao abrir o banco:', err);
            throw err;
          });
        }

        const storedUser = await getCurrentUser();
        
        if (storedUser?.jwt_token) {
          try {
            const { isValid, userData } = await checkSession(storedUser.jwt_token);
            
            if (isValid) {
              const updatedUser = {
                ...storedUser,
                ...userData
              };
              setUser(updatedUser);
              await saveUserSession(updatedUser);
            } else {
              await handleLogout();
            }
          } catch (error) {
            console.log('Modo offline ativado - usando dados locais', error);
            setIsOffline(true);
            setUser(storedUser);
          }
        }
      } catch (error) {
        console.error('Erro na inicialização:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [navigate, handleLogout]);


  const register = async (email, password, nome) => {
    try {
      const response = await authApi.register(email, password, nome);
      console.log('Resposta do registro:', response.status);
      console.log('Resposta do registro:', response);
      console.log('Resposta do registro:', response.data.status);
      console.log('Resposta do registro:', response.data);
      return response.status;
    } catch (error) {
      throw error.response?.data || error;
    }
  };

  const verifyRegister = async (email, code) => {
    try {
      const response = await authApi.verifyRegister(email, code);
      console.log('Resposta completa:', response);
      
      
      const responseData = response.data || response;
      
      if (!responseData.access_token || !responseData.user_id) {
        console.error('Estrutura inesperada:', responseData);
        throw new Error('Dados essenciais faltando na resposta');
      }

      const userData = {
        id: responseData.user_id || responseData.id,
        email: responseData.email || email,
        nome: responseData.nome || 'Usuário',
        foto_perfil: responseData.foto_perfil || '',
        jwt_token: responseData.access_token
      };

      console.log('Dados do usuário preparados:', userData);
      
      await saveUserSession(userData);
      setUser(userData);
      
      return { success: true };

    } catch (error) {
      console.error('Erro na verificação:', {
        error: error.message,
        response: error.response?.data,
        stack: error.stack
      });
      
      throw new Error(error.response?.data?.message || 'Falha na verificação do código');
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authApi.login(email, password);
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  };

  const verifyLogin = async (email, code) => {
    try {
      const response = await authApi.verifyLogin(email, code);
      console.log('AuthContext: Resposta da API:', response.data);
      console.log("AuthContext: Resposta da API:", response);
      
      if (!response || !response.access_token || !response.user_id) {
        console.error('Estrutura de resposta inválida:', response);
        throw new Error('Resposta da API em formato inválido');
      }

      const userData = {
        id: response.user_id,
        email: response.email || email, 
        nome: response.nome || 'Usuário',
        foto_perfil: response.foto_perfil || '',
        jwt_token: response.access_token
      };

      console.log('Dados do usuário:', userData);
      
      await saveUserSession(userData);
      setUser(userData);
      
      return { success: true };

    } catch (error) {
      console.error('Erro no verifyLogin:', {
        error: error.message,
        response: error.response?.data,
        stack: error.stack
      });
      
      throw new Error(error.response?.data?.message || 'Falha na verificação 2FA');
    }
  };

  const refreshSession = async () => {
    if (!user?.jwt_token) return false;
    
    try {
      const { isValid, userData } = await checkSession(user.jwt_token);
      if (isValid) {
        const updatedUser = {
          ...user,
          ...userData
        };
        setUser(updatedUser);
        await saveUserSession(updatedUser);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Refresh session error:', error);
      return false;
    }
  };

return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isOffline,
        isAuthenticated: !!user?.jwt_token,
        register,
        verifyRegister,
        login,
        verifyLogin,
        logout: handleLogout,
        refreshSession
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);