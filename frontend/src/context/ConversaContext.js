import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import conversaApi from '../api/conversa';
import { useAuth } from './AuthContext';
import db from '../database/db';

const ConversaContext = createContext();

export const ConversaProvider = ({ children }) => {
  const [conversas, setConversas] = useState([]);
  const [mensagens, setMensagens] = useState({}); // { conversaId: [mensagens] }
  const [loadingConversas, setLoadingConversas] = useState(false);
  const [loadingMensagens, setLoadingMensagens] = useState(false);
  const [errorConversas, setErrorConversas] = useState(null);
  const [errorMensagens, setErrorMensagens] = useState(null);
  const { user, isOffline } = useAuth();
  

  
  const loadConversasFromCache = useCallback(async () => {
    try {
      if (!db.isOpen()) await db.open();
      const cachedConversas = await db.conversas_cache.toArray();
      
      
      const conversasFormatadas = await Promise.all(cachedConversas.map(async conversa => {
        const outroUsuarioId = conversa.id_usuario1 === user.id ? conversa.id_usuario2 : conversa.id_usuario1;
        const outroUsuario = await db.contatos_cache.get(outroUsuarioId) || await db.usuarios_cache.get(outroUsuarioId);
        
        return {
          ...conversa,
          outro_usuario: {
            id: outroUsuarioId,
            nome: outroUsuario?.nome || 'Usuário desconhecido',
            foto_perfil: outroUsuario?.foto_perfil || null
          }
        };
      }));
      
      setConversas(conversasFormatadas);
    } catch (error) {
      console.error('Erro ao carregar conversas do cache:', error);
      setErrorConversas('Erro ao carregar conversas offline');
    }
  }, [user?.id]);

  
  const fetchConversas = useCallback(async () => {
    if (!user?.jwt_token) return;
    
    setLoadingConversas(true);
    setErrorConversas(null);

    try {
      const response = await conversaApi.listarConversas(user.jwt_token);
      
      
      if (db.isOpen()) {
        await db.conversas_cache.clear();
        await db.conversas_cache.bulkPut(response);
      }

      setConversas(response);
    } catch (error) {
      setErrorConversas(error.message);
      if (isOffline) await loadConversasFromCache();
    } finally {
      setLoadingConversas(false);
    }
  }, [user?.jwt_token, isOffline, loadConversasFromCache]);

  
  const verificarConversaExistente = useCallback(async (userId1, userId2) => {
    try {
      if (!db.isOpen()) await db.open();
      
      return await db.conversas_cache
        .where('[id_usuario1+id_usuario2]')
        .equals([userId1, userId2])
        .or('[id_usuario1+id_usuario2]')
        .equals([userId2, userId1])
        .first();
    } catch (error) {
      console.error('Erro ao verificar conversa:', error);
      return null;
    }
  }, []);

  
  const criarConversa = async (contatoId) => {
    if (!user?.jwt_token) {
      return { success: false, message: 'Usuário não autenticado' };
    }

    try {
      
      const conversaExistente = await verificarConversaExistente(user.id, contatoId);
      if (conversaExistente) {
        return { 
          success: true, 
          data: conversaExistente,
          message: 'Conversa já existente' 
        };
      }

      const response = await conversaApi.criarConversa(user.jwt_token, contatoId);
      
      
      const contato = await db.contatos_cache.get(contatoId);
      const conversaFormatada = {
        ...response,
        outro_usuario: {
          id: contatoId,
          nome: contato?.nome || 'Contato',
          foto_perfil: contato?.foto_perfil || null
        }
      };

      
      setConversas(prev => [...prev, conversaFormatada]);
      
      
      if (db.isOpen()) {
        await db.conversas_cache.put(response);
      }

      return { success: true, data: conversaFormatada };
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
      return { success: false, message: error.message };
    }
  };



  
  const excluirConversa = async (conversaId) => {
    if (!user?.jwt_token) {
      return { success: false, message: 'Usuário não autenticado' };
    }

    try {
      const response = await conversaApi.excluirConversa(user.jwt_token, conversaId);
      
      
      setConversas(prev => prev.filter(c => c.conversa_id !== conversaId));
      
      
      if (db.isOpen()) {
        await db.conversas_cache.delete(conversaId);
      }

      return { success: true, message: response.message };
    } catch (error) {
      console.error('Erro ao excluir conversa:', error);
      return { success: false, message: error.message };
    }
  };


const carregarMensagens = async (conversaId, page = 1) => {
    if (!user?.jwt_token) {
        return { success: false, message: 'Usuário não autenticado' };
    }
    
    setLoadingMensagens(true);
    setErrorMensagens(null);

    try {
        let mensagensData = [];
        let paginas = 1; // Valor padrão
        
        if (isOffline) {
            // Carrega do cache offline
            if (db.isOpen()) {
                mensagensData = await db.mensagens_cache
                    .where('id_conversa').equals(conversaId)
                    .sortBy('data_envio');
            }
        } else {
            // Carrega da API
            const response = await conversaApi.listarMensagens(user.jwt_token, conversaId, page);
            
            // Verifica se a resposta tem a estrutura esperada
            if (response.mensagens && Array.isArray(response.mensagens)) {
                mensagensData = response.mensagens;
                paginas = response.paginas || 1; // Armazena o número de páginas
            } else if (Array.isArray(response)) {
                mensagensData = response;
            } else {
                throw new Error('Formato de mensagens inválido da API');
            }
        }

        // Atualiza o estado mantendo as mensagens existentes
        setMensagens(prev => {
            const existingMessages = prev[conversaId] || [];
            
            // Filtra para evitar duplicatas
            const newMessages = mensagensData.filter(newMsg => 
                !existingMessages.some(existingMsg => existingMsg.id === newMsg.id)
            );
            
            return {
                ...prev,
                [conversaId]: [...existingMessages, ...newMessages]
            };
        });
        
        return { 
            success: true, 
            data: mensagensData,
            hasMore: paginas > page // Usa a variável paginas que foi definida
        };
    } catch (error) {
        console.error('Erro ao carregar mensagens:', error);
        setErrorMensagens(error.message);
        return { success: false, message: error.message };
    } finally {
        setLoadingMensagens(false);
    }
};


  const excluirMensagem = async (conversaId, mensagemId) => {
    if (!user?.jwt_token) {
      return { success: false, message: 'Usuário não autenticado' };
    }

    try {
      // Otimistic update
      setMensagens(prev => ({
        ...prev,
        [conversaId]: prev[conversaId].filter(m => m.id !== mensagemId)
      }));

      const response = await conversaApi.excluirMensagem(user.jwt_token, conversaId, mensagemId);

      // Atualiza o cache
      if (db.isOpen()) {
        await db.mensagens_cache.delete(mensagemId);
      }

      return { success: true, data: response };
    } catch (error) {
      // Recarrega as mensagens em caso de erro
      await carregarMensagens(conversaId);
      return { success: false, message: error.message };
    }
  };

const enviarPrimeiraMensagem = async (contatoId, texto) => {
  if (!user?.jwt_token) {
    console.error('Usuário não autenticado');
    return { success: false, message: 'Usuário não autenticado' };
  }

  try {
    // 1. Cria a porra da conversa
    const conversaResponse = await conversaApi.criarConversa(user.jwt_token, contatoId);
    
    console.log('Status da resposta:', conversaResponse.status);
    console.log('Dados da conversa:', conversaResponse.data);

    if (![200, 201].includes(conversaResponse.status)) {
      console.error('Falha ao criar conversa:', conversaResponse.data?.message);
      return { 
        success: false, 
        message: conversaResponse.data?.message || 'Erro ao criar conversa' 
      };
    }

    const conversaId = conversaResponse.data.id;
    if (!conversaId) {
      console.error('ID da conversa não retornado!');
      return { success: false, message: 'ID da conversa inválido' };
    }

    // 2. Manda a porra da mensagem
    const mensagemResponse = await conversaApi.enviarMensagem(user.jwt_token, conversaId, texto);
    
    if (![200, 201].includes(mensagemResponse.status)) {
      console.error('Falha ao enviar mensagem:', mensagemResponse.data?.message);
      return { 
        success: false, 
        message: mensagemResponse.data?.message || 'Erro ao enviar mensagem' 
      };
    }

    // 3. Atualiza o estado com a porra toda
    const contato = await db.contatos_cache.get(contatoId);
    const novaConversa = {
      ...conversaResponse.data,
      outro_usuario: {
        id: contatoId,
        nome: contato?.nome || 'Contato',
        foto_perfil: contato?.foto_perfil || null
      },
      mensagens: [mensagemResponse.data] // Adiciona a mensagem direto na conversa
    };

    // Atualiza o estado das conversas
    setConversas(prev => [...prev, novaConversa]);
    
    // Atualiza o estado das mensagens
    setMensagens(prev => ({
      ...prev,
      [conversaId]: [mensagemResponse.data]
    }));

    // 4. Salva no IndexedDB
    if (db.isOpen()) {
      await db.conversas_cache.put(conversaResponse.data);
      await db.mensagens_cache.put(mensagemResponse.data);
    }

    return { 
      success: true, 
      data: {
        conversa: novaConversa,
        mensagem: mensagemResponse.data
      }
    };

  } catch (error) {
    console.error('Erro do caralho:', {
      error: error.message,
      stack: error.stack,
      response: error.response?.data
    });
    return { 
      success: false, 
      message: error.response?.data?.error || error.message,
      errorDetails: error.response?.data
    };
  }
};


 // 1. Garanta que o estado inicial está correto


// 2. Versão segura da função enviarMensagem
const enviarMensagem = async (conversaId, texto) => {
    if (!user?.jwt_token) {
        return { success: false, message: 'Usuário não autenticado' };
    }

    try {
        // Verificação mais robusta da conversa
        let conversa = conversas.find(c => c.id === conversaId);
        if (!conversa && db.isOpen()) {
            conversa = await db.conversas_cache.get(conversaId);
        }
        
        if (!conversa) {
            console.error('Conversa não encontrada:', conversaId);
            throw new Error('Conversa não encontrada');
        }

        // Mensagem temporária
        const tempId = `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const novaMensagem = {
            id: tempId,
            id_conversa: conversaId,
            id_usuario: user.id,
            texto: texto,
            data_envio: new Date().toISOString(),
            sincronizado: false
        };

        // Atualização otimista com proteção total
        setMensagens(prev => {
            // Garante que prev é um objeto
            const prevState = typeof prev === 'object' && prev !== null ? prev : {};
            // Garante que prev[conversaId] é um array
            const mensagensAtuais = Array.isArray(prevState[conversaId]) 
                ? prevState[conversaId] 
                : [];
            
            return {
                ...prevState,
                [conversaId]: [...mensagensAtuais, novaMensagem]
            };
        });

        // Envio para a API
        const response = await conversaApi.enviarMensagem(user.jwt_token, conversaId, texto);

        if (!response.data) {
            throw new Error('Resposta da API inválida');
        }

        const mensagemParaArmazenar = {
            id: response.data.id || tempId,
            id_conversa: conversaId,
            id_usuario: user.id,
            texto: texto,
            data_envio: new Date().toISOString(),
            sincronizado: true
        };

        
        setMensagens(prev => {
            const prevState = typeof prev === 'object' && prev !== null ? prev : {};
            const mensagensAtuais = Array.isArray(prevState[conversaId]) 
                ? prevState[conversaId] 
                : [];
            
            return {
                ...prevState,
                [conversaId]: [
                    ...mensagensAtuais.filter(m => m.id !== tempId),
                    mensagemParaArmazenar
                ]
            };
        });

       
        if (db.isOpen()) {
            try {
                await db.mensagens_cache.put(mensagemParaArmazenar);
            } catch (dbError) {
                console.error('Erro ao salvar no IndexedDB:', dbError);
            }
        }

        return { success: true, data: mensagemParaArmazenar };
    } catch (error) {
        console.error('Erro no envio da mensagem:', {
            error: error.message,
            stack: error.stack,
            conversaId,
            texto
        });

        
        setMensagens(prev => {
            const prevState = typeof prev === 'object' && prev !== null ? prev : {};
            const mensagensAtuais = Array.isArray(prevState[conversaId]) 
                ? prevState[conversaId] 
                : [];
            
            return {
                ...prevState,
                [conversaId]: mensagensAtuais.filter(m => !m.id.startsWith('temp-'))
            };
        });

        return { 
            success: false, 
            message: error.message,
            error: error.response?.data || error 
        };
    }
};
 

  return (
    <ConversaContext.Provider
      value={{
        conversas,
        mensagens,
        loadingConversas,
        loadingMensagens,
        errorConversas,
        errorMensagens,
        criarConversa,
        excluirConversa,
        enviarMensagem,
        carregarMensagens,
        excluirMensagem,
        enviarPrimeiraMensagem,
        recarregarConversas: fetchConversas,
        verificarConversaExistente
      }}
    >
      {children}
    </ConversaContext.Provider>
  );
};

export const useConversa = () => useContext(ConversaContext);