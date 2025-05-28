import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useContatos } from '../context/ContatosContext';
import AdicionarContato from '../components/AdicionarContato';
import ConversaScreen from '../components/ConversaScreen';
import './style/home.css';

const Home = () => {

  const { user } = useAuth();
  const { contatos, loadingContatos, recarregarContatos, excluirContato, bloquearContato } = useContatos();
  const [showContatosModal, setShowContatosModal] = useState(false);
  const [showAdicionarContato, setShowAdicionarContato] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [menuAbertoId, setMenuAbertoId] = useState(null);
  const [contatoSelecionado, setContatoSelecionado] = useState(null);
  const menuRef = useRef(null);

 
  const filteredContatos = contatos.filter(contato => 
    contato && (
      contato.nome?.toLowerCase().includes(searchTerm.toLowerCase()) || 
      contato.email?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowContatosModal(false);
      setShowAdicionarContato(false);
      setMenuAbertoId(null);
    }
  };

  const handleClickOutside = (event) => {
    if (menuRef.current && !menuRef.current.contains(event.target)) {
      setMenuAbertoId(null);
    }
  };

  const handleContatoAdicionado = () => {
    recarregarContatos();
    setShowAdicionarContato(false);
  };

  const toggleMenu = (contatoId, e) => {
    e.stopPropagation();
    setMenuAbertoId(menuAbertoId === contatoId ? null : contatoId);
  };

  const handleExcluirContato = async (contatoId, e) => {
    e.stopPropagation();
    if (window.confirm('Tem certeza que deseja excluir este contato?')) {
      await excluirContato(contatoId);
      setMenuAbertoId(null);
    }
  };

  const handleBloquearContato = async (contatoId, e) => {
    e.stopPropagation();
    const contato = contatos.find(c => c.id === contatoId);
    const confirmMessage = contato?.bloqueio 
      ? 'Deseja desbloquear este contato?' 
      : 'Deseja bloquear este contato?';
    
    if (window.confirm(confirmMessage)) {
      await bloquearContato(contatoId, !contato?.bloqueio);
      setMenuAbertoId(null);
    }
  };

  const selecionarContato = (contato) => {
    if (!contato.bloqueio) {
      setContatoSelecionado(contato);
      setShowContatosModal(false);
    }
  };


  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

 
  return (
    <div className="home-container">
      <header className="home-header">
        <div className="user-info">
          <h1>Nexsay</h1>
          {user && <span className="user-email">{user.email}</span>}
        </div>
        <button 
          className="nova-conversa-btn"
          onClick={() => setShowContatosModal(true)}
          aria-label="Abrir lista de contatos"
        >
          + Nova Conversa
        </button>
      </header>

      {showContatosModal && (
        <div className="contatos-modal" onClick={() => setShowContatosModal(false)}>
          <div className="contatos-modal-content" onClick={(e) => e.stopPropagation()}>
            {showAdicionarContato ? (
              <AdicionarContato 
                onClose={() => setShowAdicionarContato(false)}
                onSuccess={handleContatoAdicionado}
              />
            ) : (
              <>
                <div className="contatos-modal-header">
                  <h2>Seus Contatos</h2>
                  <button 
                    className="adicionar-contato-btn"
                    onClick={() => setShowAdicionarContato(true)}
                  >
                    + Adicionar Contato
                  </button>
                </div>

                <div className="contatos-search">
                  <input
                    type="text"
                    placeholder="Buscar contatos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>

                <div className="contatos-list">
                  {loadingContatos ? (
                    <div className="loading-contatos">
                      <div className="spinner"></div>
                      <p>Carregando contatos...</p>
                    </div>
                  ) : filteredContatos.length === 0 ? (
                    <p className="no-contatos">Nenhum contato encontrado</p>
                  ) : (
                    filteredContatos.map(contato => (
                      <ContatoItem
                        key={contato.id}
                        contato={contato}
                        menuAberto={menuAbertoId === contato.id}
                        onSelect={selecionarContato}
                        onToggleMenu={toggleMenu}
                        onBloquear={handleBloquearContato}
                        onExcluir={handleExcluirContato}
                        menuRef={menuRef}
                      />
                    ))
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <main className="conversas-container">
        {contatoSelecionado ? (
          <ConversaScreen 
            contato={contatoSelecionado}
            onClose={() => setContatoSelecionado(null)}
          />
        ) : (
          <EmptyState onOpenContatos={() => setShowContatosModal(true)} />
        )}
      </main>
    </div>
  );
};


const ContatoItem = ({ contato, menuAberto, onSelect, onToggleMenu, onBloquear, onExcluir, menuRef }) => (
  <div 
    className={`contato-item ${contato.bloqueio ? 'bloqueado' : ''}`}
    onClick={() => onSelect(contato)}
  >
    <div className="contato-avatar">
      {contato.nome.charAt(0).toUpperCase()}
    </div>
    <div className="contato-info">
      <span className="contato-nome">{contato.nome}</span>
      <span className="contato-email">{contato.email}</span>
    </div>
    
    <div className="contato-menu-container">
      <button 
        className="contato-menu-btn"
        onClick={(e) => onToggleMenu(contato.id, e)}
        aria-label="Abrir menu de opções"
      >
        <span>•••</span>
      </button>
      
      {menuAberto && (
        <div 
          ref={menuRef}
          className="contato-menu-opcoes"
          onClick={(e) => e.stopPropagation()}
        >
          <button 
            className={`menu-opcao ${contato.bloqueio ? 'desbloquear' : 'bloquear'}`}
            onClick={(e) => onBloquear(contato.id, e)}
          >
            {contato.bloqueio ? 'Desbloquear' : 'Bloquear'}
          </button>
          <button 
            className="menu-opcao"
            onClick={(e) => onExcluir(contato.id, e)}
          >
            Excluir
          </button>
        </div>
      )}
    </div>
  </div>
);

const EmptyState = ({ onOpenContatos }) => (
  <div className="empty-state">
    <div className="empty-state-icon">💬</div>
    <h2>Nenhuma conversa selecionada</h2>
    <p>Selecione um contato para iniciar uma conversa</p>
    <button 
      className="empty-state-button"
      onClick={onOpenContatos}
    >
      Iniciar nova conversa
    </button>
  </div>
);

export default Home;