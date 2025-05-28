import Dexie from 'dexie';

const db = new Dexie('ChatAppDB');


db.version(2).stores({
  usuarios_cache: 'id, email, nome, foto_perfil, jwt_token',
  contatos_cache: 'id, nome, foto_perfil, bloqueio, sincronizado',
  conversas_cache: 'id, outro_usuario, nome, email, prioridade, data_criacao',
  mensagens_cache: 'id, id_conversa, texto, id_usuario, data_envio, sincronizado',
  fila: '++id, tipo, dados, ultima_tentativa'
});



db.open().catch(err => {
  console.error('Erro ao abrir o banco:', err);
  setTimeout(() => db.open(), 1000);
});

export default db;