import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import Verify2FA from './Verify2FA';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nome, setNome] = useState('');
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  const { register, verifyRegister } = useAuth();
  const navigate = useNavigate();

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await register(email, password, nome);
      console.log('Resposta do registro:', response);
      if (response === 201) {
        setStep(2); 
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Ocorreu um erro durante o registro');
    }
  };

  const handleVerifySubmit = async (code) => {
    try {
      await verifyRegister(email, code);
      navigate('/'); 
    } catch (err) {
      setError(err.response?.data?.message || 'Código inválido');
    }
  };

  return (
    <>
      {step === 1 ? (
        <div className="auth-container">
          <h2>Criar Conta</h2>
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleRegisterSubmit}>
            <div className="form-group">
              <label>Nome</label>
              <input
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
              />
            </div>
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

export default Register;