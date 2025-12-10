"""
Backend de autenticação customizado

OPERAÇÕES SQL:
1. SELECT em auth_user (busca usuário por username)
2. SELECT em blog_perfilusuario (verifica se perfil está ativo)
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class PerfilAtivoBackend(ModelBackend):
    """
    Backend de autenticação que verifica se o perfil do usuário está ativo
    
    OPERAÇÕES SQL DURANTE AUTENTICAÇÃO:
    
    1. BUSCAR USUÁRIO:
       SELECT * FROM auth_user 
       WHERE username = '{username}'
       LIMIT 1
    
    2. VERIFICAR SENHA:
       (comparação em memória do hash bcrypt)
    
    3. VERIFICAR PERFIL ATIVO:
       SELECT * FROM blog_perfilusuario 
       WHERE usuario_id = {user.id}
       LIMIT 1
    
    4. SE PERFIL.ATIVO = FALSE:
       Bloqueia o login (usuário desativado)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica o usuário verificando:
        1. Se usuário existe
        2. Se senha está correta
        3. Se perfil está ativo
        """
        try:
            # SQL EXECUTADO:
            # SELECT * FROM auth_user 
            # WHERE username = '{username}'
            # LIMIT 1
            user = User.objects.get(username=username)
            
            # Verifica a senha (comparação de hash em memória)
            if user.check_password(password):
                # SQL EXECUTADO:
                # SELECT * FROM blog_perfilusuario 
                # WHERE usuario_id = {user.id}
                # LIMIT 1
                if hasattr(user, 'perfil'):
                    # Verifica se o perfil está ativo
                    if not user.perfil.ativo:
                        # Usuário foi desativado por um admin
                        return None
                    
                    return user
                else:
                    # Usuário sem perfil (criado antes da migração)
                    # Permite login mas deveria criar o perfil
                    return user
            
            return None
            
        except User.DoesNotExist:
            # Usuário não existe
            return None
    
    def get_user(self, user_id):
        """
        Recupera usuário pelo ID durante a sessão
        
        OPERAÇÃO SQL:
        SELECT * FROM auth_user WHERE id = {user_id}
        """
        try:
            # SQL EXECUTADO:
            # SELECT * FROM auth_user WHERE id = {user_id}
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None