from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Usuario, Contato, Log, LogCategoria, LogSeveridade, Conversa
from app.extensions import db
from uuid import uuid4
from datetime import datetime
from flask import request
import json
from enum import Enum

# Função de log aprimorada
def registrar_log(usuario_id, categoria, severidade, acao, detalhe=None, metadados=None, ip_origem=None):
    """
    Registra uma ação no sistema de logs aprimorado
    :param usuario_id: UUID do usuário que realizou a ação
    :param categoria: Categoria do log (usar LogCategoria)
    :param severidade: Nível de severidade (usar LogSeveridade)
    :param acao: Descrição da ação (máx. 255 chars)
    :param detalhe: Detalhes adicionais (opcional)
    :param metadados: Dados adicionais em formato JSON (opcional)
    :param ip_origem: Endereço IP de origem (capturado automaticamente se None)
    """
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

class ContactListResource(Resource):
    @jwt_required()
    def get(self):
        """Lista todos os contatos do usuário"""
        try:
            usuario_atual_id = get_jwt_identity()
            
            
            contatos = db.session.query(
                Contato,
                Usuario.nome,
                Usuario.email,
                Usuario.foto_perfil
            ).join(
                Usuario, 
                Usuario.id == Contato.id_contato
            ).filter(
                Contato.id_usuario == usuario_atual_id
            ).order_by(
                Usuario.nome.asc()
            ).all()

            
            contatos_formatados = []
            for contato, nome, email, foto_perfil in contatos:
                contatos_formatados.append({
                    "id": str(contato.id_contato),
                    "nome": nome,
                    "email": email,
                    "foto_perfil": foto_perfil,
                    "bloqueio": contato.bloqueio,
                    "data_criacao": contato.data_criacao.isoformat()
                })

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao="LISTAR_CONTATOS",
                detalhe=f"Listados {len(contatos_formatados)} contatos"
            )

            return {
                "message": "Lista de contatos obtida com sucesso",
                "contatos": contatos_formatados,
                "total": len(contatos_formatados)
            }, 200

        except Exception as e:
            registrar_log(
                usuario_id=usuario_atual_id if 'usuario_atual_id' in locals() else None,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="ERRO_LISTAR_CONTATOS",
                detalhe=str(e)
            )
            return {"error": "Erro ao listar contatos"}, 500

    @jwt_required()
    def post(self):
        """Adiciona um novo contato à lista do usuário"""
        parser = reqparse.RequestParser()
        parser.add_argument('email_contato', type=str, required=True, help="E-mail do contato é obrigatório")
        args = parser.parse_args()

        usuario_atual_id = get_jwt_identity()
        
        try:
            
            contato = Usuario.query.filter_by(email=args['email_contato']).first()
            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="ADICIONAR_CONTATO_FALHA",
                    detalhe="Contato não encontrado no sistema",
                    metadados={"email_contato": args['email_contato']}
                )
                return {"error": "Usuário com este e-mail não encontrado"}, 404

            
            if str(contato.id) == usuario_atual_id:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="ADICIONAR_CONTATO_FALHA",
                    detalhe="Tentativa de auto-adicionar como contato"
                )
                return {"error": "Você não pode se adicionar como contato"}, 400

            
            contato_existente = Contato.query.filter_by(
                id_usuario=usuario_atual_id,
                id_contato=contato.id
            ).first()

            if contato_existente:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.INFO,
                    acao="ADICIONAR_CONTATO_REPETIDO",
                    detalhe="Contato já existente na lista",
                    metadados={"id_contato": str(contato.id)}
                )
                return {"message": "Este contato já está na sua lista"}, 200

            
            novo_contato = Contato(
                id=uuid4(),
                id_usuario=usuario_atual_id,
                id_contato=contato.id,
                bloqueio=False
            )

            db.session.add(novo_contato)
            db.session.commit()

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao="ADICIONAR_CONTATO_SUCESSO",
                detalhe="Novo contato adicionado com sucesso",
                metadados={
                    "id_contato": str(contato.id),
                    "email_contato": args['email_contato']
                }
            )

            return {
                "message": "Contato adicionado com sucesso",
                "contato": {
                    "id": str(contato.id),
                    "nome": contato.nome,
                    "email": contato.email,
                    "foto_perfil": contato.foto_perfil
                }
            }, 201

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="ADICIONAR_CONTATO_ERRO",
                detalhe=str(e),
                metadados={"email_contato": args['email_contato']}
            )
            return {"error": "Erro ao adicionar contato"}, 500


class ContactDetailResource(Resource):
    @jwt_required()
    def get(self, contato_id):
        """Visualiza informações detalhadas de um contato específico"""
        
        try:
            contato_id = str(contato_id) 
        except Exception as e:
            return {"error": "ID do contato inválido"}, 400
        try:
            usuario_atual_id = get_jwt_identity()
            
            
            contato = db.session.query(
                Contato,
                Usuario.nome,
                Usuario.email,
                Usuario.foto_perfil,
                Usuario.data_criacao
            ).join(
                Usuario, 
                Usuario.id == Contato.id_contato
            ).filter(
                Contato.id_usuario == usuario_atual_id,
                Contato.id_contato == contato_id
            ).first()

            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="VISUALIZAR_CONTATO_FALHA",
                    detalhe="Contato não encontrado na lista do usuário",
                    metadados={"id_contato": contato_id}
                )
                return {"error": "Contato não encontrado na sua lista"}, 404

            contato_obj, nome, email, foto_perfil, data_criacao = contato

            
            conversa = db.session.query(Conversa).filter(
                ((Conversa.id_usuario1 == usuario_atual_id) & 
                (Conversa.id_usuario2 == contato_id)) |
                ((Conversa.id_usuario1 == contato_id) & 
                (Conversa.id_usuario2 == usuario_atual_id))
            ).first()

            
            if conversa:
                conversa_id = str(conversa.id)
                tem_conversa = True
            else:
                conversa_id = None
                tem_conversa = False

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao="VISUALIZAR_CONTATO_SUCESSO",
                detalhe=f"Visualizado contato {nome}",
                metadados={"id_contato": contato_id}
            )

            return {
                "message": "Informações do contato obtidas com sucesso",
                "contato": {
                    "id": contato_id,
                    "nome": nome,
                    "email": email,
                    "foto_perfil": foto_perfil,
                    "data_cadastro": data_criacao.isoformat(),
                    "bloqueado": contato_obj.bloqueio,
                    "data_adicionado": contato_obj.data_criacao.isoformat(),
                    "tem_conversa": conversa is not None,
                    "conversa_id": str(conversa.id) if conversa else None
                }
            }, 200

        except Exception as e:
            registrar_log(
                usuario_id=usuario_atual_id if 'usuario_atual_id' in locals() else None,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="VISUALIZAR_CONTATO_ERRO",
                detalhe=str(e),
                metadados={"id_contato": contato_id}
            )
            return {"error": "Erro ao visualizar contato"}, 500


class ContactBlockResource(Resource):
    @jwt_required()
    def put(self, contato_id):
        """Bloqueia ou desbloqueia um contato"""
        usuario_atual_id = get_jwt_identity()
        
        try:
            
            contato = Contato.query.filter_by(
                id_usuario=usuario_atual_id,
                id_contato=contato_id
            ).first()

            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="BLOQUEAR_CONTATO_FALHA",
                    detalhe="Contato não encontrado na lista do usuário",
                    metadados={"id_contato": contato_id}
                )
                return {"error": "Contato não encontrado na sua lista"}, 404

            
            novo_status = not contato.bloqueio
            contato.bloqueio = novo_status
            db.session.commit()

            acao = "BLOQUEAR_CONTATO" if novo_status else "DESBLOQUEAR_CONTATO"
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao=acao,
                detalhe=f"Status de bloqueio alterado para {novo_status}",
                metadados={"id_contato": contato_id}
            )

            return {
                "message": "Contato bloqueado com sucesso" if novo_status else "Contato desbloqueado com sucesso",
                "bloqueado": novo_status,
                "contato_id": contato_id
            }, 200

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="BLOQUEAR_CONTATO_ERRO",
                detalhe=str(e),
                metadados={"id_contato": contato_id}
            )
            return {"error": "Erro ao alterar status de bloqueio do contato"}, 500
        
class ContactUnblockResource(Resource):
    @jwt_required()
    def put(self, contato_id):
        """Desbloqueia um contato previamente bloqueado"""
        usuario_atual_id = get_jwt_identity()
        
        try:
            
            contato = Contato.query.filter_by(
                id_usuario=usuario_atual_id,
                id_contato=contato_id
            ).first()

            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="DESBLOQUEAR_CONTATO_FALHA",
                    detalhe="Contato não encontrado na lista do usuário",
                    metadados={"id_contato": contato_id}
                )
                return {"error": "Contato não encontrado na sua lista"}, 404

            
            if not contato.bloqueio:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.INFO,
                    acao="DESBLOQUEAR_CONTATO_JA_DESBLOQUEADO",
                    detalhe="Tentativa de desbloquear contato já desbloqueado",
                    metadados={"id_contato": contato_id}
                )
                return {"message": "Este contato já está desbloqueado"}, 200

            
            contato.bloqueio = False
            db.session.commit()

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao="DESBLOQUEAR_CONTATO_SUCESSO",
                detalhe="Contato desbloqueado com sucesso",
                metadados={"id_contato": contato_id}
            )

            return {
                "message": "Contato desbloqueado com sucesso",
                "bloqueado": False,
                "contato_id": contato_id
            }, 200

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="DESBLOQUEAR_CONTATO_ERRO",
                detalhe=str(e),
                metadados={"id_contato": contato_id}
            )
            return {"error": "Erro ao desbloquear contato"}, 500

class ContactDeleteResource(Resource):
    @jwt_required()
    def delete(self, contato_id):
        """Remove um contato da lista do usuário"""
        usuario_atual_id = get_jwt_identity()
        
        try:
            
            contato = Contato.query.filter_by(
                id_usuario=usuario_atual_id,
                id_contato=contato_id
            ).first()

            if not contato:
                registrar_log(
                    usuario_id=usuario_atual_id,
                    categoria=LogCategoria.CONTATO,
                    severidade=LogSeveridade.ALERTA,
                    acao="EXCLUIR_CONTATO_FALHA",
                    detalhe="Contato não encontrado na lista do usuário",
                    metadados={"id_contato": contato_id}
                )
                return {"error": "Contato não encontrado na sua lista"}, 404

            
            db.session.delete(contato)
            db.session.commit()

            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.INFO,
                acao="EXCLUIR_CONTATO_SUCESSO",
                detalhe="Contato removido com sucesso",
                metadados={"id_contato": contato_id}
            )

            return {
                "message": "Contato removido com sucesso",
                "contato_id": contato_id
            }, 200

        except Exception as e:
            db.session.rollback()
            registrar_log(
                usuario_id=usuario_atual_id,
                categoria=LogCategoria.CONTATO,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUIR_CONTATO_ERRO",
                detalhe=str(e),
                metadados={"id_contato": contato_id}
            )
            return {"error": "Erro ao remover contato"}, 500