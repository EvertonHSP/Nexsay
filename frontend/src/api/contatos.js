import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const listarContatos = async (token) => {
  try {
    const response = await axios.get(`${API_URL}/contatos`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    // Ajuste para pegar a propriedade 'contatos' da resposta
    if (response.data && response.data.contatos) {
      return response.data.contatos; // Retorna apenas o array de contatos
    }
    throw new Error('Formato de resposta inválido');
  } catch (error) {
    // Tratamento de erro mais robusto
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        error.message || 
                        'Erro ao carregar contatos';
    throw new Error(errorMessage);
  }
};

const adicionarContato = async (token, emailContato) => {
  try {
    const response = await axios.post(`${API_URL}/contatos`, {
      email_contato: emailContato
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    // Retorna a resposta completa (o frontend agora é flexível)
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.message || 
                    error.message || 
                    'Erro ao adicionar contato';
    throw new Error(errorMsg);
  }
};

const visualizarContato = async (token, contatoId) => {
  try {
    const response = await axios.get(`${API_URL}/contatos/${contatoId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};

const excluirContato = async (token, contatoId) => {
  try {
    const response = await axios.delete(`${API_URL}/contatos/${contatoId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao excluir contato';
    throw new Error(errorMsg);
  }
};


const bloquearContato = async (token, contatoId, bloquear) => {
  try {
    const response = await axios.put(`${API_URL}/contatos/${contatoId}/bloquear`, {
      bloquear: bloquear
    }, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    return {
      ...response.data,
      bloqueio: response.data.bloqueado // Padroniza para o frontend
    };
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao bloquear/desbloquear contato';
    throw new Error(errorMsg);
  }
};

const desbloquearContato = async (token, contatoId) => {
  try {
    const response = await axios.put(`${API_URL}/contatos/${contatoId}/desbloquear`, {}, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    const errorMsg = error.response?.data?.error || 
                    error.response?.data?.message || 
                    error.message || 
                    'Erro ao desbloquear contato';
    throw new Error(errorMsg);
  }
};

// Atualize o export default
export default {
  listarContatos,
  adicionarContato,
  visualizarContato,
  excluirContato,
  bloquearContato,
  desbloquearContato
};