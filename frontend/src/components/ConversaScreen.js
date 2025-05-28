import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useConversa } from '../context/ConversaContext';
import { useAuth } from '../context/AuthContext';
import './style/ConversaScreen.css';

const ConversaScreen = ({ contato, onClose }) => {
  console.log('Componente ConversaScreen renderizado');
  console.log('Contato recebido:', contato);
  
  const { user } = useAuth();
  console.log('Usuário atual:', user);
  
  const { 
    enviarMensagem, 
    enviarPrimeiraMensagem, 
    conversas, 
    mensagens, 
    carregarMensagens 
  } = useConversa();
  
  console.log('Conversas do contexto:', conversas);
  console.log('Mensagens do contexto:', mensagens);

  const [mensagem, setMensagem] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mensagensContainerRef = useRef(null);

  
    const conversaExistente = useMemo(() => {
    const conversa = conversas.find(c => 
      (c.id_usuario2 === contato.id || c.id_usuario1 === contato.id) ||
      (c.outro_usuario && c.outro_usuario.id === contato.id)
    );
    console.log('Conversa existente calculada:', conversa);
    return conversa;
  }, [conversas, contato.id]);

  
const mensagensOrdenadas = useMemo(() => {
    const conversaId = conversaExistente?.id || 
                     (conversaExistente?.outro_usuario ? conversas.find(c => 
                         c.outro_usuario?.id === contato.id)?.id : null);

    if (!conversaId) return [];

    const msgs = Array.isArray(mensagens[conversaId]) ? mensagens[conversaId] : [];

    
    return [...msgs].sort((a, b) => new Date(a.data_envio) - new Date(b.data_envio));
}, [conversaExistente, mensagens, contato.id, conversas]);


  
useEffect(() => {
    const carregar = async () => {
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

    const timer = setTimeout(carregar, 100);
    return () => clearTimeout(timer);
}, [conversaExistente, contato.id]);

  
  useEffect(() => {
    console.log('useEffect [mensagensOrdenadas] executado - Rolagem automática');
    if (mensagensContainerRef.current) {
      console.log('Executando scroll para o final das mensagens');
      mensagensContainerRef.current.scrollTop = mensagensContainerRef.current.scrollHeight;
    }
  }, [mensagensOrdenadas]);

    const handleEnviarMensagem = async () => {
        console.log('handleEnviarMensagem chamado');
        if (!mensagem.trim()) return;
        
        setLoading(true);
        setError(null);

        try {
        const conversaId = conversaExistente?.id || 
                        (conversaExistente?.outro_usuario ? conversas.find(c => 
                            c.outro_usuario?.id === contato.id)?.id : null);
        
        let response;
        if (conversaId) {
            response = await enviarMensagem(conversaId, mensagem);
        } else {
            response = await enviarPrimeiraMensagem(contato.id, mensagem);
        }

        if (response.success) {
            setMensagem('');
            // Não recarregue as mensagens imediatamente
            // A mensagem já foi adicionada via optimistic update
        } else {
            setError(response.message || 'Erro ao enviar mensagem');
        }
        } catch (err) {
        console.error('Erro:', err);
        setError('Erro ao enviar mensagem');
        } finally {
        setLoading(false);
        }
    };

  console.log('Renderizando JSX...');
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
          onChange={(e) => {
            console.log('Mensagem alterada:', e.target.value);
            setMensagem(e.target.value);
          }}
          placeholder="Digite sua mensagem..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              console.log('Enter pressionado, enviando mensagem');
              handleEnviarMensagem();
            }
          }}
          disabled={loading}
        />
        <button 
          onClick={() => {
            console.log('Botão enviar clicado');
            handleEnviarMensagem();
          }}
          disabled={loading || !mensagem.trim()}
        >
          {loading ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
};

export default ConversaScreen;