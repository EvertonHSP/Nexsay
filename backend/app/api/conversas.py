from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Usuario, Conversa, Mensagem, Contato, Log, LogCategoria, LogSeveridade
from app.extensions import db
from uuid import uuid4
from datetime import datetime
from flask import request
import json
from enum import Enum

def registrar_log(usuario_id, categoria, severidade, acao, detalhe=None, metadados=None, ip_origem=None):
    """Função de log reutilizada do contatos.py"""
    if ip_origem is None:
        ip_origem = request.remote_addr
    
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

class ConversationResource(Resource):
    @jwt_required()
    def post(self):
        """Cria uma nova conversa entre usuários (RF01)"""
        parser = reqparse.RequestParser()
        parser.add_argument('contato_id', type=str, required=True, help="ID do contato é obrigatório")
        args = parser.parse_args()

        usuario_atual_id = get_jwt_identity()
        contato_id = args['contato_id']

        try:
            
            try:
                contato_id = str(contato_id)
            except Exception:
                return {"error": "ID do contato inválido"}, 400

            
            contato = Contato.query.filter_by(
                id_usuario=usuario_atual_id,
                id_contato=contato_id,
                bloqueio=False
            ).first()

            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.ALERTA,
                    acao="CRIAR_CONVERSA_FALHA",
                    detalhe="Contato não encontrado ou bloqueado",
                    metadados={"contato_id": contato_id}
                )
                return {"error": "Contato não encontrado ou está bloqueado"}, 403

            
            conversa_existente = Conversa.query.filter(
                ((Conversa.id_usuario1 == usuario_atual_id) & 
                 (Conversa.id_usuario2 == contato_id)) |
                ((Conversa.id_usuario1 == contato_id) & 
                 (Conversa.id_usuario2 == usuario_atual_id))
            ).first()

            if conversa_existente:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.INFO,
                    acao="CONVERSA_JA_EXISTE",
                    detalhe="Conversa já existente entre os usuários",
                    metadados={
                        "conversa_id": str(conversa_existente.id),
                        "contato_id": contato_id
                    }
                )
                return {
                    "message": "Conversa já existe",
                    "id": str(conversa_existente.id)
                }, 200

            
            nova_conversa = Conversa(
                id=uuid4(),
                id_usuario1=usuario_atual_id,
                id_usuario2=contato_id
            )

            db.session.add(nova_conversa)
            db.session.commit()

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.INFO,
                acao="CRIAR_CONVERSA_SUCESSO",
                detalhe="Nova conversa criada com sucesso",
                metadados={
                    "conversa_id": str(nova_conversa.id),
                    "contato_id": contato_id
                }
            )

            return {
                "message": "Conversa criada com sucesso",
                "id": str(nova_conversa.id),
                "contato_id": contato_id
            }, 201

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.ERRO,
                acao="CRIAR_CONVERSA_ERRO",
                detalhe=str(e),
                metadados={"contato_id": contato_id}
            )
            return {"error": "Erro ao criar conversa"}, 500

    @jwt_required()
    def get(self):
        """Lista todas as conversas do usuário"""
        try:
            usuario_atual_id = get_jwt_identity()

            
            conversas = db.session.query(Conversa).filter(
                (Conversa.id_usuario1 == usuario_atual_id) |
                (Conversa.id_usuario2 == usuario_atual_id)
            ).all()

            
            conversas_formatadas = []
            for conversa in conversas:
                
                outro_usuario_id = conversa.id_usuario2 if conversa.id_usuario1 == usuario_atual_id else conversa.id_usuario1
                
                
                outro_usuario = Usuario.query.get(outro_usuario_id)
                if not outro_usuario:
                    continue

                
                ultima_mensagem = Mensagem.query.filter_by(
                    id_conversa=conversa.id
                ).order_by(Mensagem.data_envio.desc()).first()

                conversas_formatadas.append({
                    "id": str(conversa.id),
                    "outro_usuario": str(outro_usuario.id),
                    "nome": outro_usuario.nome,
                    "email": outro_usuario.email,
                    "prioridade": ultima_mensagem.data_envio.isoformat() if ultima_mensagem else None,
                    "data_criacao": conversa.data_criacao.isoformat()
                })

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.INFO,
                acao="LISTAR_CONVERSAS",
                detalhe=f"Listadas {len(conversas_formatadas)} conversas"
            )

            return {
                "message": "Lista de conversas obtida com sucesso",
                "conversas": conversas_formatadas,
                "total": len(conversas_formatadas)
            }, 200

        except Exception as e:
            registrar_log(
                usuario_id=usuario_atual_id if 'usuario_atual_id' in locals() else None,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.ERRO,
                acao="ERRO_LISTAR_CONVERSAS",
                detalhe=str(e)
            )
            return {"error": "Erro ao listar conversas"}, 500

    @jwt_required()
    def delete(self, conversa_id):
        """Remove uma conversa para o usuário atual (apaga suas mensagens)"""
        try:
            conversa_id = str(conversa_id)
        except Exception:
            return {"error": "ID da conversa inválido"}, 400

        usuario_atual_id = get_jwt_identity()

        try:
            
            conversa = Conversa.query.filter(
                ((Conversa.id_usuario1 == usuario_atual_id) |
                 (Conversa.id_usuario2 == usuario_atual_id)) &
                (Conversa.id == conversa_id)
            ).first()

            if not conversa:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONVERSA,
                    severidade=LogSeveridade.ALERTA,
                    acao="EXCLUIR_CONVERSA_FALHA",
                    detalhe="Conversa não encontrada",
                    metadados={"conversa_id": conversa_id}
                )
                return {"error": "Conversa não encontrada"}, 404

            
            Mensagem.query.filter_by(
                id_conversa=conversa_id,
                id_usuario=usuario_atual_id
            ).update({"exclusao": True})

            db.session.commit()

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.INFO,
                acao="EXCLUIR_CONVERSA_SUCESSO",
                detalhe="Mensagens do usuário na conversa marcadas como excluídas",
                metadados={"conversa_id": conversa_id}
            )

            return {
                "message": "Suas mensagens nesta conversa foram removidas",
                "conversa_id": conversa_id
            }, 200

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONVERSA,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUIR_CONVERSA_ERRO",
                detalhe=str(e),
                metadados={"conversa_id": conversa_id}
            )
            return {"error": "Erro ao remover mensagens da conversa"}, 500


class MessageResource(Resource):
    @jwt_required()
    def post(self, conversa_id):
        """Envia uma mensagem em uma conversa"""
        parser = reqparse.RequestParser()
        parser.add_argument('texto', type=str, required=True, help="Texto da mensagem é obrigatório")
        args = parser.parse_args()

        usuario_atual_id = get_jwt_identity()
        if not conversa_id:
            return {"error": "ID da conversa não fornecido"}, 400

        try:
            conversa_id = str(conversa_id)
        except Exception:
            return {"error": "ID da conversa inválido"}, 400

        try:
            # Verifica se a conversa existe e pertence ao usuário
            conversa = Conversa.query.filter(
                ((Conversa.id_usuario1 == usuario_atual_id) |
                (Conversa.id_usuario2 == usuario_atual_id)) &
                (Conversa.id == str(conversa_id))  # Garanta que ambos são strings
            ).first()

            if not conversa:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ALERTA,
                    acao="ENVIAR_MENSAGEM_FALHA",
                    detalhe="Conversa não encontrada",
                    metadados={"conversa_id": conversa_id}
                )
                return {"error": "Conversa não encontrada"}, 404

            
            id_destino = conversa.id_usuario2 if str(conversa.id_usuario1) == usuario_atual_id else conversa.id_usuario1

            
            if not args['texto'].strip():
                return {"error": "O texto da mensagem não pode estar vazio"}, 422

            
            nova_mensagem = Mensagem(
                id=uuid4(),
                id_conversa=conversa_id,
                id_usuario=usuario_atual_id,
                texto_criptografado=args['texto']
            )

            db.session.add(nova_mensagem)
            db.session.commit()

            
            db.session.refresh(nova_mensagem)

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.MENSAGEM,
                severidade=LogSeveridade.INFO,
                acao="ENVIAR_MENSAGEM_SUCESSO",
                detalhe="Nova mensagem criada",
                metadados={
                    "conversa_id": conversa_id,
                    "mensagem_id": str(nova_mensagem.id),
                    "destinatario_id": str(id_destino)
                }
            )

            return {
                "id": str(nova_mensagem.id),
                "message": "Mensagem enviada com sucesso",
                "remetente_id": str(usuario_atual_id),
                "destinatario_id": str(id_destino),
                "data_envio": nova_mensagem.data_envio.isoformat()  # Data gerada pelo banco
            }, 201

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.MENSAGEM,
                severidade=LogSeveridade.ERRO,
                acao="ENVIAR_MENSAGEM_ERRO",
                detalhe=str(e),
                metadados={"conversa_id": conversa_id}
            )
            return {"error": "Erro ao enviar mensagem"}, 500

    @jwt_required()
    def get(self, conversa_id):
        """Busca mensagens de uma conversa"""
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, help="Número da página", location='args')
        parser.add_argument('per_page', type=int, default=20, help="Itens por página", location='args')
        args = parser.parse_args()

        usuario_atual_id = get_jwt_identity()

        try:
            conversa_id = str(conversa_id)
            
            
            conversa = Conversa.query.filter(
                ((Conversa.id_usuario1 == usuario_atual_id) |
                (Conversa.id_usuario2 == usuario_atual_id)) &
                (Conversa.id == conversa_id)
            ).first()

            if not conversa:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ALERTA,
                    acao="BUSCAR_MENSAGENS_FALHA",
                    detalhe="Conversa não encontrada",
                    metadados={"conversa_id": conversa_id}
                )
                return {"error": "Conversa não encontrada"}, 404

            
            mensagens = Mensagem.query.filter_by(
                id_conversa=conversa_id
            ).order_by(
                Mensagem.data_envio.desc()
            ).paginate(
                page=args['page'],
                per_page=args['per_page'],
                error_out=False
            )

            
            mensagens_formatadas = []
            for mensagem in mensagens.items:
                mensagem_data = {
                    "id": str(mensagem.id),
                    "id_conversa":str(mensagem.id_conversa),
                    "texto": mensagem.texto_criptografado,
                    "id_usuario": str(mensagem.id_usuario),
                    "data_envio": mensagem.data_envio.isoformat() if mensagem.data_envio else None
                }
                mensagens_formatadas.append(mensagem_data)

            return {
                "message": "Mensagens obtidas com sucesso",
                "mensagens": mensagens_formatadas,
                "total": mensagens.total,
                "paginas": mensagens.pages,
                "pagina_atual": mensagens.page
            }, 200

        except Exception as e:
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.MENSAGEM,
                severidade=LogSeveridade.ERRO,
                acao="BUSCAR_MENSAGENS_ERRO",
                detalhe=str(e),
                metadados={"conversa_id": conversa_id}
            )
            return {"error": f"Erro ao buscar mensagens: {str(e)}"}, 500
    
    @jwt_required()
    def delete(self, conversa_id, mensagem_id):
        """Apaga uma mensagem para o usuário atual (RF05)"""
        usuario_atual_id = get_jwt_identity()

        try:
            conversa_id = str(conversa_id)
            mensagem_id = str(mensagem_id)
        except Exception:
            return {"error": "ID inválido"}, 400

        try:
            
            conversa = Conversa.query.filter(
                ((Conversa.id_usuario1 == usuario_atual_id) |
                 (Conversa.id_usuario2 == usuario_atual_id)) &
                (Conversa.id == conversa_id)
            ).first()

            if not conversa:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ALERTA,
                    acao="EXCLUIR_MENSAGEM_FALHA",
                    detalhe="Conversa não encontrada",
                    metadados={
                        "conversa_id": conversa_id,
                        "mensagem_id": mensagem_id
                    }
                )
                return {"error": "Conversa não encontrada"}, 404

            
            mensagem = Mensagem.query.filter_by(
                id=mensagem_id,
                id_conversa=conversa_id
            ).first()

            if not mensagem:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ALERTA,
                    acao="EXCLUIR_MENSAGEM_FALHA",
                    detalhe="Mensagem não encontrada",
                    metadados={
                        "conversa_id": conversa_id,
                        "mensagem_id": mensagem_id
                    }
                )
                return {"error": "Mensagem não encontrada"}, 404

            
            if mensagem.id_usuario == usuario_atual_id:
                mensagem.exclusao = True
                db.session.commit()

                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.INFO,
                    acao="EXCLUIR_MENSAGEM_SUCESSO",
                    detalhe="Mensagem marcada como excluída",
                    metadados={
                        "conversa_id": conversa_id,
                        "mensagem_id": mensagem_id
                    }
                )

                return {
                    "message": "Mensagem removida com sucesso",
                    "mensagem_id": mensagem_id
                }, 200
            else:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.MENSAGEM,
                    severidade=LogSeveridade.ALERTA,
                    acao="EXCLUIR_MENSAGEM_NAO_AUTORIZADO",
                    detalhe="Tentativa de excluir mensagem de outro usuário",
                    metadados={
                        "conversa_id": conversa_id,
                        "mensagem_id": mensagem_id
                    }
                )
                return {"error": "Você só pode excluir suas próprias mensagens"}, 403

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.MENSAGEM,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUIR_MENSAGEM_ERRO",
                detalhe=str(e),
                metadados={
                    "conversa_id": conversa_id,
                    "mensagem_id": mensagem_id
                }
            )
            return {"error": "Erro ao excluir mensagem"}, 500
        

