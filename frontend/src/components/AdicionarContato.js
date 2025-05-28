import React, { useState } from 'react';
import { useContatos } from '../context/ContatosContext';
import './style/AdicionarContato.css'; 

const AdicionarContato = ({ onClose }) => {
  const [email, setEmail] = useState('');
  const [mensagem, setMensagem] = useState('');
  const { adicionarContato } = useContatos();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const resultado = await adicionarContato(email);
    
    if (resultado.success) {
      setMensagem('Contato adicionado com sucesso!');
      setEmail('');
      setTimeout(() => {
        setMensagem('');
        onClose();
      }, 1500);
    } else {
      setMensagem(resultado.message);
    }
  };

  return (
    <div className="adicionar-contato-form">
      <h3>Adicionar Novo Contato</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Digite o email do contato"
          required
        />
        <button type="submit">Adicionar</button>
        <button type="button" onClick={onClose}>Cancelar</button>
      </form>
      {mensagem && <p className="mensagem">{mensagem}</p>}
    </div>
  );
};

export default AdicionarContato;