import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom'; // Adicione o Link
import Verify2FA from './Verify2FA';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  const { login, verifyLogin } = useAuth();
  const navigate = useNavigate();

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      await login(email, password);
      setStep(2);
    } catch (err) {
      setError(err.message || 'Ocorreu um erro durante o login');
    }
  };

  const handleVerifySubmit = async (code) => {
    try {
      setError('');
      const result = await verifyLogin(email, code);
      
      if (result?.success) {
        await new Promise(resolve => setTimeout(resolve, 100));
        navigate('/');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  return (
    <>
      {step === 1 ? (
        <div className="auth-container">
          <h2>Login</h2>
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit">Continuar</button>
            
            {/* Adicione este link para o registro */}
            <div className="auth-footer">
              <span>Não tem uma conta? </span>
              <Link to="/register">Registre-se</Link>
            </div>
          </form>
        </div>
      ) : (
        <Verify2FA 
          email={email}
          onSubmit={handleVerifySubmit}
          onBack={() => setStep(1)}
          error={error}
        />
      )}
    </>
  );
};

export default Login;