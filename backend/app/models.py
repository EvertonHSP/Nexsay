from datetime import datetime
import uuid
from flask_login import UserMixin
from marshmallow import Schema, fields
from app.extensions import db
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from enum import Enum



# TABELA: usuarios
# -----------------------------------------------------------------------------------------------
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(Text, nullable=True)
    email = Column(Text, nullable=False, unique=True, index=True)
    senha_hash = Column(Text, nullable=False)
    dois_fatores_ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    ultimo_login = Column(DateTime(timezone=True), nullable=True)
    foto_perfil = Column(Text, nullable=True)

    sessoes = relationship("Sessao", back_populates="usuario", cascade="all, delete")
    contatos = relationship("Contato", back_populates="usuario", cascade="all, delete")
    conversas1 = relationship("Conversa", back_populates="usuario1", foreign_keys="Conversa.id_usuario1", cascade="all, delete")
    conversas2 = relationship("Conversa", back_populates="usuario2", foreign_keys="Conversa.id_usuario2", cascade="all, delete")
    mensagens = relationship("Mensagem", back_populates="usuario", cascade="all, delete")
    logs = relationship("Log", back_populates="usuario", cascade="all, delete")
    codigos_2fa = relationship("Codigo2FA", back_populates="usuario", cascade="all, delete")



# TABELA: sessao
# -----------------------------------------------------------------------------------------------
class Sessao(db.Model):
    __tablename__ = "sessoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    jwt_token = Column(Text, nullable=False)
    doisFatoresSessao = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="sessoes")



# TABELA: contatos
# -----------------------------------------------------------------------------------------------
class Contato(db.Model):
    __tablename__ = "contatos"
    __table_args__ = (UniqueConstraint("id_usuario", "id_contato", name="unique_contato_usuario"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    id_contato = Column(UUID(as_uuid=True), nullable=False)
    bloqueio = Column(Boolean, default=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="contatos")



# TABELA: conversas
# -----------------------------------------------------------------------------------------------
class Conversa(db.Model):
    __tablename__ = "conversas"
    __table_args__ = (UniqueConstraint("id_usuario1", "id_usuario2", name="unique_conversa_usuarios"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario1 = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    id_usuario2 = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    usuario1 = relationship("Usuario", back_populates="conversas1", foreign_keys=[id_usuario1])
    usuario2 = relationship("Usuario", back_populates="conversas2", foreign_keys=[id_usuario2])
    mensagens = relationship("Mensagem", back_populates="conversa", cascade="all, delete")



# TABELA: mensagens
# -----------------------------------------------------------------------------------------------
class Mensagem(db.Model):
    __tablename__ = "mensagens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_conversa = Column(UUID(as_uuid=True), ForeignKey("conversas.id", ondelete="CASCADE"))
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    texto_criptografado = Column(Text, nullable=False)
    data_envio = Column(DateTime(timezone=True), server_default=func.now())
    conversa = relationship("Conversa", back_populates="mensagens")
    usuario = relationship("Usuario", back_populates="mensagens", foreign_keys=[id_usuario])


# TABELAs: logs

class LogCategoria(Enum):
    AUTENTICACAO = "Autenticação"
    CONTATO = "Contato"
    CONVERSA = "Conversa"
    MENSAGEM = "Mensagem"
    SISTEMA = "Sistema"

class LogSeveridade(Enum):
    INFO = "Informação"
    ALERTA = "Alerta"
    ERRO = "Erro"
    CRITICO = "Crítico"

class Log(db.Model):
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    categoria = Column(Text, nullable=False)  
    severidade = Column(Text, nullable=False)  
    acao = Column(Text, nullable=False)
    detalhe = Column(Text, nullable=True)
    ip_origem = Column(INET, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadados = Column(Text, nullable=True)  

    usuario = relationship("Usuario", back_populates="logs")



# TABELA: 2FA
# -----------------------------------------------------------------------------------------------
class Codigo2FA(db.Model):
    __tablename__ = "doisfatores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    codigo = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="codigos_2fa")
