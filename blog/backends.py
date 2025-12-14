from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db import connection


class PerfilAtivoBackend(ModelBackend):
    """
    Backend de autenticação que verifica se o perfil do usuário está ativo
    usando SQL puro em vez de ORM
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica o usuário verificando:
        1. Se usuário existe
        2. Se senha está correta
        3. Se perfil está ativo
        
        OPERAÇÕES SQL:
        1. SELECT * FROM auth_user WHERE username = %s
        2. SELECT * FROM blog_perfilusuario WHERE usuario_id = %s
        """
        if username is None or password is None:
            return None
        
        try:
            with connection.cursor() as cursor:
                # SQL EXECUTADO:
                # SELECT id, username, password, first_name, last_name, email, 
                #        is_staff, is_active, is_superuser, date_joined, last_login
                # FROM auth_user 
                # WHERE username = %s
                cursor.execute("""
                    SELECT id, username, password, first_name, last_name, email, 
                           is_staff, is_active, is_superuser, date_joined, last_login
                    FROM auth_user 
                    WHERE username = %s
                """, [username])
                
                user_data = cursor.fetchone()
                
                if not user_data:
                    # Usuário não existe
                    return None
                
                # Reconstruir objeto User (necessário para check_password)
                user = User(
                    id=user_data[0],
                    username=user_data[1],
                    password=user_data[2],
                    first_name=user_data[3],
                    last_name=user_data[4],
                    email=user_data[5],
                    is_staff=user_data[6],
                    is_active=user_data[7],
                    is_superuser=user_data[8],
                    date_joined=user_data[9],
                    last_login=user_data[10]
                )
                
                # Verifica a senha (comparação de hash em memória)
                if user.check_password(password):
                    # SQL EXECUTADO:
                    # SELECT id, usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em
                    # FROM blog_perfilusuario 
                    # WHERE usuario_id = %s
                    cursor.execute("""
                        SELECT id, usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em
                        FROM blog_perfilusuario 
                        WHERE usuario_id = %s
                    """, [user.id])
                    
                    perfil_data = cursor.fetchone()
                    
                    if perfil_data:
                        # Verifica se o perfil está ativo
                        ativo = perfil_data[4]
                        
                        if not ativo:
                            # Usuário foi desativado por um admin
                            return None
                        
                        return user
                    else:
                        # Usuário sem perfil
                        return user
                
                return None
                
        except Exception as e:
            # Em caso de erro, não permite login
            print(f"Erro na autenticação: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """
        Recupera usuário pelo ID durante a sessão
        
        OPERAÇÃO SQL:
        SELECT * FROM auth_user WHERE id = %s
        """
        try:
            with connection.cursor() as cursor:
                # SQL EXECUTADO:
                # SELECT id, username, password, first_name, last_name, email, 
                #        is_staff, is_active, is_superuser, date_joined, last_login
                # FROM auth_user 
                # WHERE id = %s
                cursor.execute("""
                    SELECT id, username, password, first_name, last_name, email, 
                           is_staff, is_active, is_superuser, date_joined, last_login
                    FROM auth_user 
                    WHERE id = %s
                """, [user_id])
                
                user_data = cursor.fetchone()
                
                if not user_data:
                    return None
                
                # Reconstruir objeto User
                user = User(
                    id=user_data[0],
                    username=user_data[1],
                    password=user_data[2],
                    first_name=user_data[3],
                    last_name=user_data[4],
                    email=user_data[5],
                    is_staff=user_data[6],
                    is_active=user_data[7],
                    is_superuser=user_data[8],
                    date_joined=user_data[9],
                    last_login=user_data[10]
                )
                
                return user
                
        except Exception as e:
            print(f"Erro ao recuperar usuário: {str(e)}")
            return None


"""
========================================
EXEMPLO DE USO E QUERIES SQL GERADAS
========================================

FLUXO DE AUTENTICAÇÃO:
---------------------

1. Usuário acessa /accounts/login/ e digita:
   - Username: "mateus"
   - Password: "Senh@123"

2. Django chama authenticate():
   
   SQL 1 - BUSCAR USUÁRIO:
   SELECT id, username, password, first_name, last_name, email, 
          is_staff, is_active, is_superuser, date_joined, last_login
   FROM auth_user 
   WHERE username = 'mateus'
   
   Resultado: user_data = (1, 'mateus', 'pbkdf2_sha256$...', '', '', 'mateus@email.com', False, True, False, '2025-12-01', NULL)

3. Verifica senha (em memória):
   user.check_password('Senh@123') → True

4. Verifica perfil ativo:
   
   SQL 2 - VERIFICAR PERFIL:
   SELECT id, usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em
   FROM blog_perfilusuario 
   WHERE usuario_id = 1
   
   Resultado: perfil_data = (1, 1, '12345678900', 'comum', True, '2025-12-01 10:00:00', '2025-12-01 10:00:00')

5. Se ativo = True:
   - Retorna objeto User
   - Django cria sessão
   - Redireciona para página inicial

6. Se ativo = False:
   - Retorna None
   - Login falha
   - Mensagem: "Credenciais inválidas"


CASO: USUÁRIO DESATIVADO
------------------------

1. Admin desativa usuário no painel:
   UPDATE blog_perfilusuario SET ativo = FALSE WHERE usuario_id = 1

2. Usuário tenta fazer login:
   - authenticate() busca usuário: OK
   - Verifica senha: OK
   - Verifica perfil.ativo: FALSE
   - Retorna None → LOGIN BLOQUEADO


CASO: USUÁRIO SEM PERFIL
-------------------------

1. Usuário criado antes da migração (sem perfil):
   - authenticate() busca usuário: OK
   - Verifica senha: OK
   - Busca perfil: perfil_data = None
   - Permite login (usuário antigo)
   - Sistema deveria criar perfil automaticamente


SEGURANÇA
---------

✅ Senha nunca é armazenada em texto plano
✅ Hash PBKDF2-SHA256 é verificado em memória
✅ SQL Injection prevenido com parâmetros %s
✅ Perfil desativado bloqueia login completamente
✅ Erro na query retorna None (falha segura)
"""