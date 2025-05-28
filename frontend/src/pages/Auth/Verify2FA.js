import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Verify2FA = ({ email, onSubmit, onBack, error: propError }) => {
  const [code, setCode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    
    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
      setLocalError('Código inválido');
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onSubmit(code);
      
    } catch (error) {
      setLocalError(error.message);
      setCode('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <h2>Verificação 2FA</h2>
      
      {/* Mensagens de erro */}
      {(propError || localError) && (
        <div className="error-message">
          {propError || localError}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <p>Enviamos um código de verificação para <strong>{email}</strong></p>
        <p>Por favor, verifique sua caixa de entrada e spam.</p>
        
        <div className="form-group">
          <label>Código de 6 dígitos</label>
          <input
            type="text"
            className="verification-code-input"
            value={code}
            onChange={(e) => {
              const value = e.target.value.replace(/\D/g, '').slice(0, 6);
              setCode(value);
              setLocalError('');
            }}
            maxLength="6"
            inputMode="numeric"
            pattern="\d{6}"
            required
            disabled={isSubmitting}
            autoFocus
          />
        </div>
        
        <div className="actions">
          <button 
            type="submit" 
            disabled={isSubmitting || code.length !== 6}
            className="primary-button"
          >
            {isSubmitting ? (
              <>
                <span className="spinner"></span>
                Verificando...
              </>
            ) : 'Verificar'}
          </button>
          
          {onBack && (
            <button 
              type="button" 
              onClick={onBack}
              className="secondary-button"
              disabled={isSubmitting}
            >
              Voltar
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default Verify2FA;