from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from app import bcrypt, mail
from app.models import Usuario, Sessao, Codigo2FA, Contato, Mensagem, Log, LogCategoria, LogSeveridade
from app.extensions import db, mail
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from flask_mail import Message
import random
from flask import request
from enum import Enum
import json


#REGISTRAR LOG-------------------------------------------------------------------------------

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

#enviar email-------------------------------------------------------------------------------

def enviar_email_2fa(email, codigo):
    try:
        
        plain_content = f"Your verification code is: {codigo}\nUse this code to complete your registration/login."
        html_content = f"""<!DOCTYPE html>
        <html><head><meta charset="utf-8"></head>
        <body><p>Your code: <strong>{codigo}</strong></p></body></html>"""
        
        
        
        msg = Message(
            subject="Code",  
            recipients=[email],
            charset='utf-8',
            body=plain_content,
            html=html_content
        )
        
        
        msg.extra_headers = {'Content-Transfer-Encoding': '8bit'}
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"ERRO DETALHADO: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
        if hasattr(e, 'args'):
            print(f"Args do erro: {e.args}")
        return False



#CRIAR A CONTA E VERIFICAR ELA-------------------------------------------------------------------------------

class RegisterResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        parser.add_argument('nome', type=str, required=True)
        args = parser.parse_args()
        
        
        usuario_existente = Usuario.query.filter_by(email=args['email']).first()
        
        if usuario_existente:
            if usuario_existente.dois_fatores_ativo:
                return {"error": "E-mail já registrado e verificado"}, 400
            
            
            usuario_existente.nome = args['nome']
            usuario_existente.senha_hash = bcrypt.generate_password_hash(args['password']).decode('utf-8')
            
           
            Codigo2FA.query.filter_by(id_usuario=usuario_existente.id).delete()
            
            usuario = usuario_existente
        else:
            
            usuario = Usuario(
                nome=args['nome'],
                email=args['email'],
                senha_hash=bcrypt.generate_password_hash(args['password']).decode('utf-8'),
                dois_fatores_ativo=False
            )
            db.session.add(usuario)
        
        db.session.commit()

        
        codigo = str(random.randint(100000, 999999))
        hash_codigo = sha256(codigo.encode()).hexdigest()

        registro_2fa = Codigo2FA(
            id=uuid4(),
            id_usuario=usuario.id,
            codigo=hash_codigo,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(registro_2fa)
        db.session.commit()
        
        
        registrar_log(
            usuario_id=usuario.id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="REGISTRO_TENTATIVA",
            detalhe=f"Novo registro para {args['email']}"
        )
        
        if not enviar_email_2fa(usuario.email, codigo):
            
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ERRO,
                acao="REGISTRO_ERRO_ENVIO_EMAIL",  
                detalhe="Falha ao enviar código 2FA"
            )
            return {"error": "Falha ao enviar código de verificação"}, 500

        return {
            "message": "Código de verificação enviado por e-mail",
            "email": usuario.email,
            "conta_verificada": False
        }, 201

class VerificarCodigo2FAResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('codigo', type=str, required=True)
        args = parser.parse_args()

        usuario = Usuario.query.filter_by(email=args['email']).first()
        if not usuario:
            return {"error": "Usuário não encontrado"}, 404

        
        limite_tempo = datetime.now(timezone.utc) - timedelta(minutes=15)
        registro = Codigo2FA.query.filter(
            Codigo2FA.id_usuario == usuario.id,
            Codigo2FA.timestamp >= limite_tempo
        ).order_by(Codigo2FA.timestamp.desc()).first()

        registrar_log(
            usuario_id=usuario.id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="REGISTRO_VALIDAR",
            detalhe="Validar código 2FA"
        )

        if not registro:
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="REGISTRO_VALIDAR_FALHA",
                detalhe="Código 2FA expirado ou não encontrado"
            )
            return {"error": "Código 2FA expirado ou não encontrado"}, 404

        if sha256(args['codigo'].encode()).hexdigest() != registro.codigo:
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="REGISTRO_VALIDAR_FALHA",
                detalhe="Código 2FA inválido"
            )
            return {"error": "Código 2FA inválido"}, 400

        
        usuario.dois_fatores_ativo = True
        usuario.ultimo_login = datetime.utcnow()

        
        additional_claims = {"jti": str(uuid4())}  
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims=additional_claims
        )

        sessao = Sessao(
            id=uuid4(),
            id_usuario=usuario.id,
            jwt_token=additional_claims["jti"],  
            doisFatoresSessao=True
        )
        
        db.session.delete(registro)
        db.session.add(sessao)
        db.session.commit()

        registrar_log(
            usuario_id=usuario.id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="REGISTRO_VALIDAR_SUCESSO",
            detalhe="Registro validado com sucesso!"
        )

        return {
            "success": True,
            "message": "Conta verificada com sucesso!",
            "access_token": token,  
            "user_id": str(usuario.id),  
            "nome": usuario.nome,  
            "email": usuario.email,  
            "foto_perfil": usuario.foto_perfil if usuario.foto_perfil else "",  
            "conta_verificada": True
        }, 200



#LOGIN PRA VALIDAR A SESSAO-----------------------------------------------------------------------------

class LoginResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        usuario = Usuario.query.filter_by(email=args['email']).first()
        
        
        registrar_log(
            usuario_id=usuario.id if usuario else None,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="LOGIN_TENTATIVA",
            detalhe="Tentativa de realizar login"
        )

        if not usuario or not bcrypt.check_password_hash(usuario.senha_hash, args["password"]):
            registrar_log(
                usuario_id=usuario.id if usuario else None,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="LOGIN_TENTATIVA_FALHA",
                detalhe="Credenciais inválidas"
            )
            return {"error": "Credenciais inválidas"}, 401

        
        if not usuario.dois_fatores_ativo:
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="LOGIN_TENTATIVA_FALHA",
                detalhe="Conta não ativada, necessidade de verificação"
            )
            return {"error": "Conta não verificada. Verifique seu email."}, 403

        
        codigo = str(random.randint(100000, 999999))
        hash_codigo = sha256(codigo.encode()).hexdigest()

        registro_2fa = Codigo2FA(
            id=uuid4(),
            id_usuario=usuario.id,
            codigo=hash_codigo,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(registro_2fa)
        db.session.commit()

        if not enviar_email_2fa(usuario.email, codigo):
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ERRO,
                acao="LOGIN_ERRO_ENVIO_EMAIL",
                detalhe="Falha ao enviar código 2FA"
            )
            return {"error": "Falha ao enviar código de verificação"}, 500

        return {
            "message": "Código 2FA enviado para seu email. Verifique para completar o login.",
            "email": usuario.email,
            "conta_verificada": True
        }, 200

class VerificarLogin2FAResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True)
        parser.add_argument('codigo', type=str, required=True)
        args = parser.parse_args()

        usuario = Usuario.query.filter_by(email=args['email']).first()
        if not usuario:
            return {"error": "Usuário não encontrado"}, 404

        
        limite_tempo = datetime.now(timezone.utc) - timedelta(minutes=15)
        registro = Codigo2FA.query.filter(
            Codigo2FA.id_usuario == usuario.id,
            Codigo2FA.timestamp >= limite_tempo
        ).order_by(Codigo2FA.timestamp.desc()).first()

        registrar_log(
            usuario_id=usuario.id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="LOGIN_VALIDAR",
            detalhe="Validar código 2FA"
        )

        if not registro:
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="LOGIN_VALIDAR_FALHA",
                detalhe="Código 2FA expirado ou não encontrado"
            )
            return {"error": "Código 2FA expirado ou não encontrado"}, 404

        if sha256(args['codigo'].encode()).hexdigest() != registro.codigo:
            registrar_log(
                usuario_id=usuario.id,
                categoria=LogCategoria.AUTENTICACAO,
                severidade=LogSeveridade.ALERTA,
                acao="LOGIN_VALIDAR_FALHA",
                detalhe="Código 2FA inválido"
            )
            return {"error": "Código 2FA inválido"}, 400

        registrar_log(
            usuario_id=usuario.id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="LOGIN_VALIDAR_SUCESSO",
            detalhe="Login verificado com sucesso!"
        )

        
        usuario.ultimo_login = datetime.utcnow()

        
        additional_claims = {"jti": str(uuid4())}
        token = create_access_token(
            identity=str(usuario.id),
            additional_claims=additional_claims
        )

        sessao = Sessao(
            id=uuid4(),
            id_usuario=usuario.id,
            jwt_token=additional_claims["jti"],
            doisFatoresSessao=True
        )
        
        db.session.delete(registro)  
        db.session.add(sessao)
        db.session.commit()

        print(json.dumps({"success": True, "message": "Login verificado com sucesso!", "access_token": token, "user": {"id": str(usuario.id), "nome": usuario.nome, "email": usuario.email, "foto_perfil": usuario.foto_perfil if usuario.foto_perfil else ""}}, indent=None))
        

        return {
            "success": True,
            "message": "Login verificado com sucesso!",
            "access_token": token,  
            "user_id": str(usuario.id),  
            "nome": usuario.nome,  
            "email": usuario.email,  
            "foto_perfil": usuario.foto_perfil if usuario.foto_perfil else ""  
        }, 200


#LOGOUT PRA INVALIDAR A SESSAO-----------------------------------------------------------------------------

class LogoutResource(Resource):
    @jwt_required()
    def post(self):
        """Encerra apenas a sessão atual"""
        usuario_id = get_jwt_identity()
        jti = get_jwt()["jti"]
        
        
        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.AUTENTICACAO,
            severidade=LogSeveridade.INFO,
            acao="LOGOUT",
            detalhe=f"Encerramento de sessão (JTI: {jti})",
            ip_origem=request.remote_addr
        )
        
        
        Sessao.query.filter_by(
            id_usuario=usuario_id,
            jwt_token=jti
        ).delete()
        db.session.commit()
        
        return {"message": "Sessão atual encerrada com sucesso"}, 200

#VALIDAR A SESSAO-----------------------------------------------------------------------------

class UserProfileResource(Resource):
    @jwt_required()
    def get(self):
        
        usuario_id = get_jwt_identity()
        
        
        jti = get_jwt()["jti"]
        
        
        sessao = Sessao.query.filter_by(
            id_usuario=usuario_id,
            jwt_token=jti,
            doisFatoresSessao=True
        ).first()
        
        if not sessao:
            return {"error": "Sessão não encontrada ou não verificada"}, 401
        
        
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return {"error": "Usuário não encontrado"}, 404
        
        
        return {
            "id": str(usuario.id),
            "nome": usuario.nome,
            "email": usuario.email,
            "dois_fatores_ativo": usuario.dois_fatores_ativo,
            "data_criacao": usuario.data_criacao.isoformat() if usuario.data_criacao else None,
            "ultimo_login": usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
            "foto_perfil": usuario.foto_perfil
        }, 200

#excluir conta-----------------------------------------------------------------------------

class ExcluirContaResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.CONTA,
            severidade=LogSeveridade.INFO,
            acao="EXCLUSAO_CONTA_SOLICITADA",
            detalhe="Solicitação de exclusão de conta iniciada"
        )

        if not usuario:
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUSAO_CONTA_FALHA",
                detalhe="Usuário não encontrado"
            )
            return {"error": "Usuário não encontrado"}, 404
            
        
        if not bcrypt.check_password_hash(usuario.senha_hash, args['password']):
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ALERTA,
                acao="EXCLUSAO_CONTA_FALHA",
                detalhe="Senha incorreta fornecida"
            )
            return {"error": "Senha incorreta"}, 401

        
        jti = get_jwt()["jti"]
        sessao = Sessao.query.filter_by(
            id_usuario=usuario_id,
            jwt_token=jti
        ).first()
        
        if not sessao or not sessao.doisFatoresSessao:
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ALERTA,
                acao="EXCLUSAO_CONTA_FALHA",
                detalhe="Autenticação em duas etapas necessária"
            )
            return {"error": "Autenticação em duas etapas necessária"}, 403
        
        
        codigo = str(random.randint(100000, 999999))
        hash_codigo = sha256(codigo.encode()).hexdigest()

        registro_2fa = Codigo2FA(
            id=uuid4(),
            id_usuario=usuario_id,
            codigo=hash_codigo,
            timestamp=datetime.now(timezone.utc)
        )
        
        db.session.add(registro_2fa)
        db.session.commit()

        if not enviar_email_2fa(usuario.email, codigo):
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUSAO_CONTA_FALHA",
                detalhe="Falha ao enviar código de verificação por email"
            )
            return {"error": "Falha ao enviar código de verificação"}, 500

        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.CONTA,
            severidade=LogSeveridade.INFO,
            acao="EXCLUSAO_CONTA_CODIGO_ENVIADO",
            detalhe="Código de confirmação enviado para email do usuário"
        )

        return {"message": "Código de confirmação enviado para seu email"}, 200

class ConfirmarExclusaoContaResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('codigo', type=str, required=True)
        args = parser.parse_args()

        usuario_id = get_jwt_identity()
        
        
        limite_tempo = datetime.now(timezone.utc) - timedelta(minutes=15)
        registro = Codigo2FA.query.filter(
            Codigo2FA.id_usuario == usuario_id,
            Codigo2FA.timestamp >= limite_tempo
        ).order_by(Codigo2FA.timestamp.desc()).first()

        if not registro:
            return {"error": "Código 2FA expirado ou não encontrado"}, 404

        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.CONTA,
            severidade=LogSeveridade.INFO,
            acao="EXCLUSAO_CONTA_VALIDAR",
            detalhe="Validação de código 2FA para exclusão de conta"
        )

        if sha256(args['codigo'].encode()).hexdigest() != registro.codigo:
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ALERTA,
                acao="EXCLUSAO_CONTA_VALIDAR_FALHA",
                detalhe="Código 2FA inválido fornecido para exclusão de conta"
            )
            return {"error": "Código 2FA inválido"}, 400

        
        db.session.delete(registro)
        
        # Obtém o usuário
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            registrar_log(
                usuario_id=usuario_id,
                categoria=LogCategoria.CONTA,
                severidade=LogSeveridade.ERRO,
                acao="EXCLUSAO_CONTA_FALHA",
                detalhe="Usuário não encontrado durante processo de exclusão"
            )
            return {"error": "Usuário não encontrado"}, 404

        
        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.CONTA,
            severidade=LogSeveridade.INFO,
            acao="EXCLUSAO_CONTA_INICIADA",
            detalhe="Processo de exclusão de conta iniciado",
            ip_origem=request.remote_addr
        )

        
        usuario.email = f"deleted_{uuid4().hex}@deleted.com"
        usuario.nome = "Usuário Excluído"
        usuario.senha_hash = bcrypt.generate_password_hash(uuid4().hex).decode('utf-8')
        usuario.foto_perfil = None
        usuario.dois_fatores_ativo = False

        
        Contato.query.filter_by(id_usuario=usuario_id).delete()

        
        Sessao.query.filter_by(id_usuario=usuario_id).delete()

        
        Codigo2FA.query.filter_by(id_usuario=usuario_id).delete()

        
        mensagens = Mensagem.query.filter_by(id_usuario=usuario_id).all()
        for msg in mensagens:
            msg.texto_criptografado = "[mensagem removida]"
            msg.exclusao = True

        db.session.commit()

        registrar_log(
            usuario_id=usuario_id,
            categoria=LogCategoria.CONTA,
            severidade=LogSeveridade.INFO,
            acao="EXCLUSAO_CONTA_CONCLUIDA",
            detalhe="Conta excluída e dados anonimizados com sucesso"
        )

        return {
            "message": "Conta excluída com sucesso",
            "logout": True  
        }, 200



