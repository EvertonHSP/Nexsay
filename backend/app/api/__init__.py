from flask import Blueprint
from flask_restful import Api
from app.api.auth import (
    RegisterResource,
    LoginResource,
    LogoutResource,
    VerificarCodigo2FAResource,
    VerificarLogin2FAResource,
    ConfirmarExclusaoContaResource,
    ExcluirContaResource,
    UserProfileResource
)
from app.api.contatos import (
    ContactListResource,
    ContactDetailResource,
    ContactBlockResource,
    ContactUnblockResource,
    ContactDeleteResource
)
from app.api.conversas import (
    ConversationResource,
    MessageResource
)

api_bp = Blueprint('api', __name__, url_prefix='/api')  
api = Api(api_bp)

# Rotas de autenticação
api.add_resource(RegisterResource, '/auth/register')
api.add_resource(VerificarCodigo2FAResource, '/auth/verify-register')
api.add_resource(LoginResource, '/auth/login')
api.add_resource(VerificarLogin2FAResource, '/auth/verify-login')
api.add_resource(LogoutResource, '/auth/logout')
api.add_resource(UserProfileResource, '/auth/me')
api.add_resource(ExcluirContaResource, '/auth/excluir')
api.add_resource(ConfirmarExclusaoContaResource, '/auth/confirmar-exclusao')
# Rotas dos contatos
api.add_resource(ContactListResource, '/contatos')
api.add_resource(ContactBlockResource, '/contatos/<string:contato_id>/bloquear')
api.add_resource(ContactDetailResource, '/contatos/<string:contato_id>')
api.add_resource(ContactDeleteResource, '/contatos/<string:contato_id>', endpoint='delete_contact')
api.add_resource(ContactUnblockResource, '/contatos/<string:contato_id>/desbloquear')
# Rotas de conversas e mensagens
api.add_resource(ConversationResource, '/conversas', '/conversas/<string:conversa_id>')
api.add_resource(MessageResource, 
                '/conversas/<string:conversa_id>/mensagens', 
                '/conversas/<string:conversa_id>/mensagens/<string:mensagem_id>')

def init_app(app):
    """Função de inicialização que deve ser importada no app/__init__.py"""
    app.register_blueprint(api_bp)