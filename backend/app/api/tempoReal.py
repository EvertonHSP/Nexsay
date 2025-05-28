from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import Usuario, Mensagem, Log, LogCategoria, LogSeveridade
from app.extensions import db
from uuid import uuid4
import json
from enum import Enum
from datetime import datetime

def registrar_log(usuario_id, categoria, severidade, acao, detalhe=None, metadados=None, ip_origem=None):
    """Função de log reutilizada"""
    if ip_origem is None:
        ip_origem = request.remote_addr if request else None
    
    try:
        novo_log = Log(
            id=uuid4(),
            id_usuario=usuario_id,
            categoria=categoria.value if isinstance(categoria, Enum) else categoria,
            severidade=severidade.value if isinstance(severidade, Enum) else severidade,
            acao=acao,
            detalhe=detalhe,
            ip_origem=ip_origem,
            metadados=json.dumps(metadados) if metadados else None
        )
        
        db.session.add(novo_log)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar log: {str(e)}")
        return False


class WebSocketHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.connected_users = {}  
        self.setup_handlers()

    def setup_handlers(self):
        @self.socketio.on('connect')
        @jwt_required()
        def handle_connect():
            try:
                usuario_atual_id = get_jwt_identity()
                self.connected_users[usuario_atual_id] = request.sid

                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.INFO,
                    acao="WEBSOCKET_CONNECT",
                    detalhe="Conexão WebSocket estabelecida"
                )

                emit('connection_success', {'message': 'Conectado com sucesso'})
            except Exception as e:
                emit('connection_error', {'error': str(e)})
                return False

        @self.socketio.on('disconnect')
        def handle_disconnect():
            usuario_atual_id = None
            for user_id, sid in self.connected_users.items():
                if sid == request.sid:
                    usuario_atual_id = user_id
                    break

            if usuario_atual_id:
                self.connected_users.pop(usuario_atual_id, None)
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.INFO,
                    acao="WEBSOCKET_DISCONNECT",
                    detalhe="Conexão WebSocket encerrada"
                )

        @self.socketio.on('join_conversation')
        @jwt_required()
        def handle_join_conversation(data):
            try:
                usuario_atual_id = get_jwt_identity()
                conversa_id = data.get('conversa_id')

                if not conversa_id:
                    emit('error', {'error': 'ID da conversa é obrigatório'})
                    return

                join_room(conversa_id)

                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.INFO,
                    acao="WEBSOCKET_JOIN_CONVERSATION",
                    detalhe="Usuário entrou na sala de conversa",
                    metadados={"conversa_id": conversa_id}
                )

                emit('join_success', {
                    'message': f'Você entrou na conversa {conversa_id}',
                    'conversa_id': conversa_id
                })
            except Exception as e:
                emit('error', {'error': str(e)})

        @self.socketio.on('leave_conversation')
        @jwt_required()
        def handle_leave_conversation(data):
            try:
                usuario_atual_id = get_jwt_identity()
                conversa_id = data.get('conversa_id')

                if not conversa_id:
                    emit('error', {'error': 'ID da conversa é obrigatório'})
                    return

                leave_room(conversa_id)

                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.INFO,
                    acao="WEBSOCKET_LEAVE_CONVERSATION",
                    detalhe="Usuário saiu da sala de conversa",
                    metadados={"conversa_id": conversa_id}
                )

                emit('leave_success', {
                    'message': f'Você saiu da conversa {conversa_id}',
                    'conversa_id': conversa_id
                })
            except Exception as e:
                emit('error', {'error': str(e)})

        @self.socketio.on('new_message')
        @jwt_required()
        def handle_new_message(data):
            try:
                usuario_atual_id = get_jwt_identity()
                conversa_id = data.get('conversa_id')
                mensagem_id = data.get('mensagem_id')

                if not all([conversa_id, mensagem_id]):
                    emit('error', {'error': 'Dados incompletos'})
                    return

                
                mensagem = Mensagem.query.filter_by(
                    id=mensagem_id,
                    id_conversa=conversa_id
                ).first()

                if not mensagem:
                    emit('error', {'error': 'Mensagem não encontrada'})
                    return

                
                conversa = mensagem.conversa
                destinatario_id = conversa.id_usuario2 if conversa.id_usuario1 == usuario_atual_id else conversa.id_usuario1

                
                if destinatario_id in self.connected_users:
                    emit('receive_message', {
                        'mensagem_id': str(mensagem.id),
                        'conversa_id': str(mensagem.id_conversa),
                        'texto': mensagem.texto_criptografado,
                        'data_envio': mensagem.data_envio.isoformat(),
                        'remetente_id': str(mensagem.id_usuario)
                    }, room=self.connected_users[destinatario_id])

                    
                    mensagem.entregue = True
                    db.session.commit()

                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.INFO,
                    acao="WEBSOCKET_MESSAGE_SENT",
                    detalhe="Mensagem enviada via WebSocket",
                    metadados={
                        "conversa_id": conversa_id,
                        "mensagem_id": mensagem_id,
                        "destinatario_id": str(destinatario_id)
                    }
                )

            except Exception as e:
                db.session.rollback()
                emit('error', {'error': str(e)})
                registrar_log(
                    usuario_id=usuario_atual_id if 'usuario_atual_id' in locals() else None,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ERRO,
                    acao="WEBSOCKET_MESSAGE_ERROR",
                    detalhe=str(e),
                    metadados=data
                )

        @self.socketio.on('message_read')
        @jwt_required()
        def handle_message_read(data):
            try:
                usuario_atual_id = get_jwt_identity()
                mensagem_id = data.get('mensagem_id')

                if not mensagem_id:
                    emit('error', {'error': 'ID da mensagem é obrigatório'})
                    return

                
                mensagem = Mensagem.query.get(mensagem_id)

                if not mensagem:
                    emit('error', {'error': 'Mensagem não encontrada'})
                    return

                
                conversa = mensagem.conversa
                if usuario_atual_id not in [str(conversa.id_usuario1), str(conversa.id_usuario2)]:
                    emit('error', {'error': 'Você não tem permissão para marcar esta mensagem como lida'})
                    return

                
                if mensagem.id_usuario != usuario_atual_id and not mensagem.data_visualizacao:
                    mensagem.data_visualizacao = datetime.utcnow()
                    db.session.commit()

                    
                    if str(mensagem.id_usuario) in self.connected_users:
                        emit('message_read_confirmation', {
                            'mensagem_id': str(mensagem.id),
                            'data_visualizacao': mensagem.data_visualizacao.isoformat()
                        }, room=self.connected_users[str(mensagem.id_usuario)])

                    registrar_log(
                        usuario_id=usuario_atual_id,
                        categoria=LogCategoria.MENSAGEM,
                        severidade=LogSeveridade.INFO,
                        acao="WEBSOCKET_MESSAGE_READ",
                        detalhe="Mensagem marcada como lida",
                        metadados={"mensagem_id": mensagem_id}
                    )

                emit('read_success', {
                    'message': 'Mensagem marcada como lida',
                    'mensagem_id': mensagem_id
                })

            except Exception as e:
                db.session.rollback()
                emit('error', {'error': str(e)})
                registrar_log(
                    usuario_id=usuario_atual_id if 'usuario_atual_id' in locals() else None,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ERRO,
                    acao="WEBSOCKET_MESSAGE_READ_ERROR",
                    detalhe=str(e),
                    metadados=data
                )



