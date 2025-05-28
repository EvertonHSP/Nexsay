import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const criarConversa = async (token, contatoId) => {
  try {
    const response = await axios.post(`${API_URL}/conversas`, {
      contato_id: contatoId
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao criar conversa';
    throw new Error(errorMsg);
  }
};

const listarConversas = async (token) => {
  try {
    const response = await axios.get(`${API_URL}/conversas`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data.conversas || [];
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao carregar conversas';
    throw new Error(errorMsg);
  }
};

const excluirConversa = async (token, conversaId) => {
  try {
    const response = await axios.delete(`${API_URL}/conversas/${conversaId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao excluir conversa';
    throw new Error(errorMsg);
  }
};

const enviarMensagem = async (token, conversaId, texto) => {
  try {
    const response = await axios.post(`${API_URL}/conversas/${conversaId}/mensagens`, {
      texto: texto
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao enviar mensagem';
    throw new Error(errorMsg);
  }
};

const listarMensagens = async (token, conversaId, page = 1, perPage = 20) => {
  try {
    const response = await axios.get(`${API_URL}/conversas/${conversaId}/mensagens`, {
      params: { page, per_page: perPage },
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao carregar mensagens';
    throw new Error(errorMsg);
  }
};

const excluirMensagem = async (token, conversaId, mensagemId) => {
  try {
    const response = await axios.delete(`${API_URL}/conversas/${conversaId}/mensagens/${mensagemId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao excluir mensagem';
    throw new Error(errorMsg);
  }
};

// Adicione as novas funções ao export
export default {
  criarConversa,
  listarConversas,
  excluirConversa,
  enviarMensagem,
  listarMensagens,
  excluirMensagem
};