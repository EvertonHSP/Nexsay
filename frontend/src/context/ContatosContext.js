import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import contatosApi from '../api/contatos';
import { useAuth } from './AuthContext';
import db from '../database/db';

const ContatosContext = createContext();

export const ContatosProvider = ({ children }) => {
  const [contatos, setContatos] = useState([]);
  const [loadingContatos, setLoadingContatos] = useState(false);
  const [errorContatos, setErrorContatos] = useState(null);
  const { user, isOffline } = useAuth();

  
  const loadContatosFromCache = useCallback(async () => {
    try {
      if (!db.isOpen()) await db.open();
      const cachedContatos = await db.contatos_cache.toArray();
      setContatos(cachedContatos);
    } catch (error) {
      console.error('Erro ao carregar contatos do cache:', error);
      setErrorContatos('Erro ao carregar contatos offline');
    }
  }, []);




  
  const fetchContatos = useCallback(async () => {
    console.group('[fetchContatos] Iniciando busca de contatos');
    
    if (!user?.jwt_token) {
        console.warn('[fetchContatos] Abortando - usuário não autenticado ou token inválido');
        console.groupEnd();
        return;
    }

    console.log('[fetchContatos] Token JWT:', user.jwt_token);
    console.log('[fetchContatos] Modo offline:', isOffline);
    
    setLoadingContatos(true);
    setErrorContatos(null);

    try {
        console.log('[fetchContatos] Chamando API para listar contatos...');
        const response = await contatosApi.listarContatos(user.jwt_token);
        console.log('[fetchContatos] Resposta da API:', response);

        if (!Array.isArray(response)) {
        console.error('[fetchContatos] Resposta inválida - não é array:', {
            tipo: typeof response,
            valor: response
        });
        throw new Error('Dados recebidos não são uma lista de contatos');
        }

        console.log(`[fetchContatos] Recebidos ${response.length} contatos da API`);

        
        if (response.length > 0) {
        console.log('[fetchContatos] Exemplo de contato recebido:', {
            id: response[0].id,
            nome: response[0].nome,
            email: response[0].email,
            estrutura: Object.keys(response[0])
        });
        }

        
        if (db.isOpen()) {
        console.log('[fetchContatos] Banco local aberto - atualizando cache...');
        console.log('[fetchContatos] Schema do contatos_cache:', db.contatos_cache.schema);

        try {
            console.log('[fetchContatos] Limpando cache existente...');
            await db.contatos_cache.clear();
            console.log('[fetchContatos] Cache limpo com sucesso');

            console.log('[fetchContatos] Inserindo novos contatos...');
            await db.contatos_cache.bulkPut(response);
            console.log('[fetchContatos] Cache atualizado com sucesso');

            
            const count = await db.contatos_cache.count();
            console.log(`[fetchContatos] Total de contatos no cache após atualização: ${count}`);
            
            if (count !== response.length) {
            console.warn('[fetchContatos] Discrepância na contagem de contatos!');
            }
        } catch (dbError) {
            console.error('[fetchContatos] Erro detalhado ao atualizar cache:', {
            error: dbError,
            errorMessage: dbError.message,
            stack: dbError.stack,
            dataBeingInserted: response.slice(0, 3) // Mostra apenas os 3 primeiros para não poluir
            });
            throw dbError;
        }
        } else {
        console.warn('[fetchContatos] Banco local não está aberto - pulando cache');
        }

        console.log('[fetchContatos] Atualizando estado do React...');
        setContatos(response);
        console.log('[fetchContatos] Estado atualizado com sucesso');
        
    } catch (error) {
        console.error('[fetchContatos] Erro durante a busca de contatos:', {
        error: error,
        message: error.message,
        stack: error.stack,
        response: error.response,
        config: error.config
        });

        setErrorContatos(error.message);
        
        if (isOffline) {
        console.log('[fetchContatos] Modo offline - tentando carregar do cache...');
        try {
            const cachedContatos = await loadContatosFromCache();
            console.log(`[fetchContatos] Carregados ${cachedContatos.length} contatos do cache`);
        } catch (cacheError) {
            console.error('[fetchContatos] Erro ao carregar do cache:', {
            error: cacheError,
            message: cacheError.message,
            stack: cacheError.stack
            });
            setErrorContatos('Não foi possível carregar contatos offline');
        }
        }
    } finally {
        console.log('[fetchContatos] Finalizando operação');
        setLoadingContatos(false);
        console.groupEnd();
    }
    }, [user?.jwt_token, isOffline, loadContatosFromCache]);




  


  const adicionarContato = async (emailContato) => {
        if (!user?.jwt_token) {
            console.log('[adicionarContato] Usuário não autenticado - abortando');
            return { success: false, message: 'Usuário não autenticado' };
        }

        try {
            console.log('[adicionarContato] Chamando API...');
            const response = await contatosApi.adicionarContato(user.jwt_token, emailContato);
            console.log('[adicionarContato] Resposta da API:', response);

            
            const contato = response.contato || response;
            if (!contato || !contato.id) {
                console.error('[adicionarContato] Resposta inválida da API', response);
                throw new Error('Dados do contato ausentes na resposta');
            }

            const novoContato = {
                id: contato.id,
                nome: contato.nome || 'Novo Contato',
                email: contato.email,
                foto_perfil: contato.foto_perfil || '',
                bloqueio: false,
                sincronizado: true
            };

            console.log('[adicionarContato] Objeto formatado para cache:', novoContato);

            
            setContatos(prev => [...prev, novoContato]);

            
            if (db.isOpen()) {
                try {
                    await db.contatos_cache.put(novoContato);
                    console.log('[adicionarContato] Contato salvo no IndexedDB');
                } catch (dbError) {
                    console.error('[adicionarContato] Erro no IndexedDB:', dbError);
                    throw dbError;
                }
            }

            return { 
                success: true, 
                data: novoContato,
                message: 'Contato adicionado com sucesso' 
            };
        } catch (error) {
            console.error('[adicionarContato] Erro:', {
                error: error.message,
                stack: error.stack,
                response: error.response?.data
            });
            
            return { 
                success: false, 
                message: error.message,
                errorDetails: error.response?.data
            };
        }
    };





  
  useEffect(() => {
    if (user?.jwt_token) {
      if (isOffline) {
        loadContatosFromCache();
      } else {
        fetchContatos();
      }
    }
  }, [user?.jwt_token, isOffline, fetchContatos, loadContatosFromCache]);

    const excluirContato = async (contatoId) => {
    if (!user?.jwt_token) {
        console.log('[excluirContato] Usuário não autenticado - abortando');
        return { success: false, message: 'Usuário não autenticado' };
    }

    try {
        console.log('[excluirContato] Chamando API...');
        const response = await contatosApi.excluirContato(user.jwt_token, contatoId);
        console.log('[excluirContato] Resposta da API:', response);

        
        setContatos(prev => prev.filter(c => c.id !== contatoId));

        
        if (db.isOpen()) {
        try {
            await db.contatos_cache.delete(contatoId);
            console.log('[excluirContato] Contato removido do IndexedDB');
        } catch (dbError) {
            console.error('[excluirContato] Erro no IndexedDB:', dbError);
            throw dbError;
        }
        }

        return { 
        success: true, 
        message: response.message || 'Contato excluído com sucesso' 
        };
    } catch (error) {
        console.error('[excluirContato] Erro:', {
        error: error.message,
        stack: error.stack,
        response: error.response?.data
        });
        
        
        if (error.message.includes('offline') || isOffline) {
        try {
            await db.fila.add({
            tipo: 'excluir_contato',
            dados: { contatoId },
            timestamp: new Date().getTime()
            });
            console.log('[excluirContato] Operação adicionada à fila offline');
            
            
            setContatos(prev => prev.filter(c => c.id !== contatoId));
            await db.contatos_cache.delete(contatoId);
            
            return { 
            success: true, 
            message: 'Contato marcado para exclusão quando online' 
            };
        } catch (queueError) {
            console.error('[excluirContato] Erro ao adicionar à fila:', queueError);
            return { 
            success: false, 
            message: 'Falha ao registrar exclusão offline' 
            };
        }
        }
        
        return { 
        success: false, 
        message: error.message,
        errorDetails: error.response?.data
        };
    }
    };

    const bloquearContato = async (contatoId, bloquear) => {
        if (!user?.jwt_token) {
            console.log('[bloquearContato] Usuário não autenticado - abortando');
            return { success: false, message: 'Usuário não autenticado' };
        }

        try {
            let response;
            if (bloquear) {
            console.log('[bloquearContato] Chamando API para bloquear...');
            response = await contatosApi.bloquearContato(user.jwt_token, contatoId, true);
            } else {
            console.log('[bloquearContato] Chamando API para desbloquear...');
            response = await contatosApi.desbloquearContato(user.jwt_token, contatoId);
            }
            
            console.log('[bloquearContato] Resposta da API:', response);

            // Atualiza o estado local
            setContatos(prev => prev.map(contato => 
            contato.id === contatoId 
                ? { ...contato, bloqueio: response.bloqueado } 
                : contato
            ));

            // Atualiza o IndexedDB
            if (db.isOpen()) {
            try {
                await db.contatos_cache.update(contatoId, { bloqueio: response.bloqueado });
                console.log('[bloquearContato] Status de bloqueio atualizado no IndexedDB');
            } catch (dbError) {
                console.error('[bloquearContato] Erro no IndexedDB:', dbError);
                throw dbError;
            }
            }

            return { 
            success: true, 
            message: response.message,
            bloqueado: response.bloqueado
            };
        } catch (error) {
            console.error('[bloquearContato] Erro:', {
            error: error.message,
            stack: error.stack,
            response: error.response?.data
            });
            
            // Em caso de offline, adicione à fila de sincronização
            if (error.message.includes('offline') || isOffline) {
            try {
                await db.fila.add({
                tipo: 'bloquear_contato',
                dados: { contatoId, bloquear },
                timestamp: new Date().getTime()
                });
                console.log('[bloquearContato] Operação adicionada à fila offline');
                
                // Atualiza o estado localmente
                setContatos(prev => prev.map(contato => 
                contato.id === contatoId 
                    ? { ...contato, bloqueio: bloquear } 
                    : contato
                ));
                
                if (db.isOpen()) {
                await db.contatos_cache.update(contatoId, { bloqueio: bloquear });
                }
                
                return { 
                success: true, 
                message: 'Bloqueio marcado para sincronização quando online',
                bloqueado: bloquear
                };
            } catch (queueError) {
                console.error('[bloquearContato] Erro ao adicionar à fila:', queueError);
                return { 
                success: false, 
                message: 'Falha ao registrar bloqueio offline' 
                };
            }
            }
            
            return { 
            success: false, 
            message: error.message,
            errorDetails: error.response?.data
            };
        }
        };

  return (
    <ContatosContext.Provider
      value={{
        contatos,
        loadingContatos,
        errorContatos,
        adicionarContato,
        excluirContato,
        bloquearContato,
        recarregarContatos: fetchContatos
      }}
    >
      {children}
    </ContatosContext.Provider>
  );
};

export const useContatos = () => useContext(ContatosContext);