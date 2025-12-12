"""
Formulários do blog - VERSÃO 100% SQL PURO
Todos os .objects foram removidos e substituídos por SQL direto
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import connection
from django.core.exceptions import ValidationError
from .validators import validar_email_formato, validar_cpf_formato, limpar_cpf, formatar_cpf


class PostForm(forms.Form):
    """
    Formulário para criar e editar posts - SQL PURO
    
    OPERAÇÕES SQL:
    1. Buscar categorias: SELECT * FROM blog_categoria ORDER BY nome
    """
    
    titulo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o título do post'
        }),
        label='Título'
    )
    
    conteudo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Escreva o conteúdo do seu post aqui'
        }),
        label='Conteúdo'
    )
    
    imagem = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label='Imagem'
    )
    
    categoria = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoria'
    )
    
    def __init__(self, *args, **kwargs):
        """
        Busca categorias do banco usando SQL puro
        
        SQL EXECUTADO:
        SELECT id, nome FROM blog_categoria ORDER BY nome ASC
        """
        super().__init__(*args, **kwargs)
        
        # SQL: Buscar categorias
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nome 
                FROM blog_categoria 
                ORDER BY nome ASC
            """)
            
            categorias = cursor.fetchall()
        
        # Criar choices para o dropdown
        choices = [('', '-- Selecione uma categoria --')]
        choices.extend([(cat[0], cat[1]) for cat in categorias])
        
        self.fields['categoria'].choices = choices
    
    def clean_titulo(self):
        """Valida título"""
        titulo = self.cleaned_data.get('titulo', '').strip()
        
        if len(titulo) < 5:
            raise ValidationError('O título deve ter pelo menos 5 caracteres.')
        
        return titulo
    
    def clean_conteudo(self):
        """Valida conteúdo"""
        conteudo = self.cleaned_data.get('conteudo', '').strip()
        
        if not conteudo:
            raise ValidationError('O conteúdo não pode estar vazio.')
        
        return conteudo


class ComentarioForm(forms.Form):
    """
    Formulário para criar e editar comentários - SQL PURO
    """
    
    conteudo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Digite seu comentário...',
            'maxlength': 1000
        }),
        label='Comentário',
        max_length=1000
    )
    
    def clean_conteudo(self):
        """Valida conteúdo do comentário"""
        conteudo = self.cleaned_data.get('conteudo', '').strip()
        
        if not conteudo:
            raise ValidationError('O comentário não pode estar vazio.')
        
        if len(conteudo) < 3:
            raise ValidationError('O comentário deve ter pelo menos 3 caracteres.')
        
        return conteudo


class CustomUserCreationForm(UserCreationForm):
    """
    Formulário de cadastro personalizado - SQL PURO
    
    OPERAÇÕES SQL:
    1. SELECT COUNT(*) FROM auth_user WHERE username = %s
    2. SELECT COUNT(*) FROM auth_user WHERE email = %s
    3. SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = %s
    """
    
    email = forms.EmailField(
        required=True,
        label='Email',
        help_text='Digite um email válido (ex: usuario@dominio.com)',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario@dominio.com'
        })
    )
    
    cpf = forms.CharField(
        required=True,
        label='CPF',
        max_length=14,
        help_text='Digite seu CPF (apenas números ou com formatação)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'maxlength': '14'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'cpf', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escolha um nome de usuário'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
    
    def clean_email(self):
        """
        Validação do email usando SQL PURO
        
        OPERAÇÃO SQL:
        SELECT COUNT(*) FROM auth_user WHERE email = %s
        """
        email = self.cleaned_data.get('email')
        
        # Valida o formato do email
        validar_email_formato(email)
        
        # SQL: Verificar se email já existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM auth_user 
                WHERE email = %s
            """, [email])
            
            count = cursor.fetchone()[0]
        
        if count > 0:
            raise ValidationError('Este email já está cadastrado no sistema.')
        
        return email
    
    def clean_cpf(self):
        """
        Validação do CPF usando SQL PURO
        
        OPERAÇÃO SQL:
        SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = %s
        """
        cpf = self.cleaned_data.get('cpf')
        
        # Valida o formato e dígitos verificadores do CPF
        cpf_limpo = validar_cpf_formato(cpf)
        
        # SQL: Verificar se CPF já existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM blog_perfilusuario 
                WHERE cpf = %s
            """, [cpf_limpo])
            
            count = cursor.fetchone()[0]
        
        if count > 0:
            raise ValidationError('Este CPF já está cadastrado no sistema.')
        
        return cpf_limpo
    
    def clean_username(self):
        """
        Validação do username usando SQL PURO
        
        OPERAÇÃO SQL:
        SELECT COUNT(*) FROM auth_user WHERE username = %s
        """
        username = self.cleaned_data.get('username')
        
        if len(username) < 3:
            raise ValidationError('O nome de usuário deve ter pelo menos 3 caracteres.')
        
        # SQL: Verificar se username já existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM auth_user 
                WHERE username = %s
            """, [username])
            
            count = cursor.fetchone()[0]
        
        if count > 0:
            raise ValidationError('Este nome de usuário já está em uso.')
        
        return username
    
    def save(self, commit=True):
        """
        Salva o usuário e cria o perfil usando SQL PURO
        
        OPERAÇÕES SQL:
        1. INSERT INTO auth_user (username, email, password, ...)
        2. INSERT INTO blog_perfilusuario (usuario_id, cpf, ...)
        """
        from django.contrib.auth.hashers import make_password
        from django.db import transaction
        
        if not commit:
            # Se não for para commitar, retorna None
            return None
        
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        cpf = self.cleaned_data['cpf']
        
        # Hash da senha
        hashed_password = make_password(password)
        
        # Transação atômica: cria usuário + perfil
        with transaction.atomic():
            with connection.cursor() as cursor:
                # SQL 1: Inserir usuário
                cursor.execute("""
                    INSERT INTO auth_user 
                    (username, email, password, is_active, is_staff, 
                     is_superuser, date_joined, first_name, last_name)
                    VALUES (%s, %s, %s, TRUE, FALSE, FALSE, NOW(), '', '')
                    RETURNING id
                """, [username, email, hashed_password])
                
                user_id = cursor.fetchone()[0]
                
                # SQL 2: Inserir perfil
                cursor.execute("""
                    INSERT INTO blog_perfilusuario 
                    (usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em)
                    VALUES (%s, %s, 'comum', TRUE, NOW(), NOW())
                """, [user_id, cpf])
        
        # Reconstruir objeto User para retornar (necessário para login)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, password, first_name, last_name, email, 
                       is_staff, is_active, is_superuser, date_joined, last_login
                FROM auth_user 
                WHERE id = %s
            """, [user_id])
            
            user_data = cursor.fetchone()
        
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
        
        # Marcar como "do banco" para que o Django não tente salvar novamente
        user._state.adding = False
        user._state.db = 'default'
        
        return user


"""
========================================
CONVERSÃO COMPLETA PARA SQL PURO
========================================

ANTES (ORM):
------------
Categoria.objects.all().order_by('nome')
User.objects.filter(email=email).exists()
PerfilUsuario.objects.filter(cpf=cpf).exists()
PerfilUsuario.objects.create(...)

DEPOIS (SQL PURO):
------------------
SELECT * FROM blog_categoria ORDER BY nome
SELECT COUNT(*) FROM auth_user WHERE email = %s
SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = %s
INSERT INTO blog_perfilusuario VALUES (...)

========================================
BENEFÍCIOS:
========================================
✅ 100% SQL puro
✅ Controle total sobre queries
✅ Sem "magia" do ORM
✅ Queries visíveis e auditáveis

========================================
LOCALIZAÇÃO DAS QUERIES:
========================================

PostForm.__init__() - linha 50
  → SELECT blog_categoria

CustomUserCreationForm.clean_email() - linha 148
  → SELECT COUNT auth_user WHERE email

CustomUserCreationForm.clean_cpf() - linha 173
  → SELECT COUNT blog_perfilusuario WHERE cpf

CustomUserCreationForm.clean_username() - linha 198
  → SELECT COUNT auth_user WHERE username

CustomUserCreationForm.save() - linha 245
  → INSERT auth_user
  → INSERT blog_perfilusuario
  → SELECT auth_user (para retornar objeto)
"""