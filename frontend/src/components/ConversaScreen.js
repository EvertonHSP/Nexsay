import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useConversa } from '../context/ConversaContext';
import { useAuth } from '../context/AuthContext';
import './style/ConversaScreen.css';

const ConversaScreen = ({ contato, onClose }) => {
  const { user } = useAuth();
  const { 
    enviarMensagem, 
    enviarPrimeiraMensagem, 
    conversas, 
    mensagens, 
    carregarMensagens,
    setMensagens
  } = useConversa();
  
  const [mensagem, setMensagem] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mensagensContainerRef = useRef(null);

  const conversaExistente = useMemo(() => {
    return conversas.find(c => 
      (c.id_usuario2 === contato.id || c.id_usuario1 === contato.id) ||
      (c.outro_usuario && c.outro_usuario.id === contato.id)
    );
  }, [conversas, contato.id]);

  const mensagensOrdenadas = useMemo(() => {
    const conversaId = conversaExistente?.id || 
                     (conversaExistente?.outro_usuario ? conversas.find(c => 
                         c.outro_usuario?.id === contato.id)?.id : null);

    if (!conversaId) return [];

    const msgs = Array.isArray(mensagens[conversaId]) ? mensagens[conversaId] : [];
    return [...msgs].sort((a, b) => new Date(a.data_envio) - new Date(b.data_envio));
  }, [conversaExistente, mensagens, contato.id, conversas]);

  // Função para carregar mensagens
  const carregarMensagensDaConversa = async () => {
    const conversaId = conversaExistente?.id || 
                     (conversaExistente?.outro_usuario ? conversas.find(c => 
                         c.outro_usuario?.id === contato.id)?.id : null);
    
    if (conversaId) {
      try {
        await carregarMensagens(conversaId, 1);
      } catch (err) {
        console.error('Erro ao carregar mensagens:', err);
      }
    }
  };

  // Efeito para polling de mensagens a cada 2 segundos
  useEffect(() => {
    // Carrega imediatamente ao montar ou quando a conversa muda
    carregarMensagensDaConversa();
    
    // Configura o intervalo para polling
    const intervalId = setInterval(carregarMensagensDaConversa, 2000);
    
    // Limpa o intervalo quando o componente desmonta ou a conversa muda
    return () => clearInterval(intervalId);
  }, [conversaExistente, contato.id]);

  // Efeito para rolagem automática
  useEffect(() => {
    if (mensagensContainerRef.current) {
      mensagensContainerRef.current.scrollTop = mensagensContainerRef.current.scrollHeight;
    }
  }, [mensagensOrdenadas]);

const handleEnviarMensagem = async () => {
  if (!mensagem.trim()) return;
  
  setLoading(true);
  setError(null);

  let conversaId = conversaExistente?.id;
  let response;
  let tempMessageId = null;

  try {
    if (!conversaId) {
      // 1. Envia a primeira mensagem e cria conversa
      response = await enviarPrimeiraMensagem(contato.id, mensagem);
      
      if (!response.success) throw new Error(response.message || 'Falha ao criar conversa');

      conversaId = response.data.conversa.id;
      tempMessageId = 'temp-' + Date.now();

      // 2. Atualização otimista - MANTÉM a mensagem do servidor + temporária
      setMensagens(prev => {
        const serverMessage = response.data.mensagem;
        const newMessages = serverMessage 
          ? [{
              ...serverMessage,
              isTemp: false
            }, {
              id: tempMessageId,
              texto: mensagem,
              id_usuario: user.id,
              data_envio: new Date().toISOString(),
              id_conversa: conversaId,
              isTemp: true
            }]
          : [{
              id: tempMessageId,
              texto: mensagem,
              id_usuario: user.id,
              data_envio: new Date().toISOString(),
              id_conversa: conversaId,
              isTemp: true
            }];

        return {
          ...prev,
          [conversaId]: newMessages
        };
      });

      // 3. Carrega mensagens do servidor SEM forçar reload completo
      await carregarMensagens(conversaId, 1, false); // forceReload: false
    } else {
      // Fluxo normal para conversa existente
      response = await enviarMensagem(conversaId, mensagem);
      await carregarMensagens(conversaId, 1, true);
    }

    if (response?.success) setMensagem('');
    else setError(response?.message || 'Erro ao enviar mensagem');
  } catch (err) {
    console.error('Erro:', err);
    setError(err.message || 'Erro ao enviar mensagem');
    
    if (tempMessageId && conversaId) {
      setMensagens(prev => {
        const updated = { ...prev };
        if (updated[conversaId]) {
          updated[conversaId] = updated[conversaId].filter(msg => !msg.isTemp);
          if (updated[conversaId].length === 0) delete updated[conversaId];
        }
        return updated;
      });
    }
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="conversa-screen">
      <div className="conversa-header">
        <button className="back-button" onClick={onClose}>
          &larr; Voltar
        </button>
        <div className="contato-info">
          <div className="contato-avatar">
            {contato.nome.charAt(0).toUpperCase()}
          </div>
          <h3>{contato.nome}</h3>
        </div>
      </div>

      <div className="mensagens-container" ref={mensagensContainerRef}>
        {mensagensOrdenadas.length > 0 ? (
          mensagensOrdenadas.map(msg => (
            <div 
              key={msg.id} 
              className={`mensagem ${msg.id_usuario === user.id ? 'enviada' : 'recebida'}`}
            >
              <div className="mensagem-conteudo">
                <p>{msg.texto}</p>
                <span className="mensagem-hora">
                  {new Date(msg.data_envio).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-conversa">
            <p>Inicie uma nova conversa com {contato.nome}</p>
          </div>
        )}
      </div>

      <div className="mensagem-input-container">
        {error && <div className="error-message">{error}</div>}
        <input
          type="text"
          value={mensagem}
          onChange={(e) => setMensagem(e.target.value)}
          placeholder="Digite sua mensagem..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleEnviarMensagem();
            }
          }}
          disabled={loading}
        />
        <button 
          onClick={handleEnviarMensagem}
          disabled={loading || !mensagem.trim()}
        >
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
};

export default ConversaScreen;