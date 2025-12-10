from django import forms
from .models import Post, Categoria, PerfilUsuario, Comentario
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .validators import validar_email_formato, validar_cpf_formato, limpar_cpf, formatar_cpf


class PostForm(forms.ModelForm):
    """
    Formulário para criar e editar posts
    
    OPERAÇÕES SQL QUANDO O FORMULÁRIO É EXIBIDO:
    1. POPULAR DROPDOWN DE CATEGORIAS (ORDENADO ALFABETICAMENTE):
       SELECT * FROM blog_categoria ORDER BY nome ASC
    """
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all().order_by('nome'),
        required=False,
        empty_label="-- Selecione uma categoria --",
        label="Categoria"
    )
    
    class Meta:
        model = Post
        fields = ['titulo', 'conteudo', 'imagem', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título do post'
            }),
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escreva o conteúdo do seu post aqui'
            }),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo')
        if len(titulo) < 5:
            raise forms.ValidationError('O título deve ter pelo menos 5 caracteres.')
        return titulo
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')


class ComentarioForm(forms.ModelForm):
    """
    Formulário para criar e editar comentários
    
    OPERAÇÕES SQL QUANDO O FORMULÁRIO É SALVO:
    
    1. CRIAR COMENTÁRIO:
       INSERT INTO blog_comentario (post_id, autor_id, conteudo, criado_em, atualizado_em)
       VALUES ({post_id}, {autor_id}, '{conteudo}', NOW(), NOW())
    
    2. EDITAR COMENTÁRIO:
       UPDATE blog_comentario 
       SET conteudo = '{novo_conteudo}', atualizado_em = NOW()
       WHERE id = {comentario_id}
    """
    
    class Meta:
        model = Comentario
        fields = ['conteudo']
        widgets = {
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Digite seu comentário...',
                'maxlength': 1000
            })
        }
        labels = {
            'conteudo': 'Comentário'
        }
    
    def clean_conteudo(self):
        conteudo = self.cleaned_data.get('conteudo', '').strip()
        if not conteudo:
            raise forms.ValidationError('O comentário não pode estar vazio.')
        if len(conteudo) < 3:
            raise forms.ValidationError('O comentário deve ter pelo menos 3 caracteres.')
        return conteudo


class CustomUserCreationForm(UserCreationForm):
    """
    Formulário de cadastro personalizado com email e CPF obrigatórios
    
    OPERAÇÕES SQL QUANDO O FORMULÁRIO É SALVO:
    
    1. VERIFICAR SE USERNAME JÁ EXISTE:
       SELECT COUNT(*) FROM auth_user WHERE username = '{username}'
    
    2. VERIFICAR SE EMAIL JÁ EXISTE:
       SELECT COUNT(*) FROM auth_user WHERE email = '{email}'
    
    3. VERIFICAR SE CPF JÁ EXISTE:
       SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = '{cpf}'
    
    4. CRIAR NOVO USUÁRIO:
       INSERT INTO auth_user 
       (username, email, password, is_active, is_staff, is_superuser, date_joined)
       VALUES ('{username}', '{email}', '{hashed_password}', 1, 0, 0, NOW())
    
    5. CRIAR PERFIL DO USUÁRIO:
       INSERT INTO blog_perfilusuario 
       (usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em)
       VALUES ({user_id}, '{cpf}', 'comum', TRUE, NOW(), NOW())
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
        Validação do email
        
        OPERAÇÕES SQL:
        1. Valida formato (em memória)
        2. SELECT COUNT(*) FROM auth_user WHERE email = '{email}'
        """
        email = self.cleaned_data.get('email')
        
        # Valida o formato do email
        validar_email_formato(email)
        
        # SQL EXECUTADO:
        # SELECT COUNT(*) FROM auth_user WHERE email = '{email}'
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está cadastrado no sistema.')
        
        return email
    
    def clean_cpf(self):
        """
        Validação do CPF
        
        OPERAÇÕES SQL:
        1. Valida formato e dígitos verificadores (em memória)
        2. SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = '{cpf}'
        """
        cpf = self.cleaned_data.get('cpf')
        
        # Valida o formato e dígitos verificadores do CPF
        cpf_limpo = validar_cpf_formato(cpf)
        
        # SQL EXECUTADO:
        # SELECT COUNT(*) FROM blog_perfilusuario WHERE cpf = '{cpf_limpo}'
        if PerfilUsuario.objects.filter(cpf=cpf_limpo).exists():
            raise forms.ValidationError('Este CPF já está cadastrado no sistema.')
        
        return cpf_limpo
    
    def clean_username(self):
        """
        Validação do username
        
        OPERAÇÃO SQL:
        SELECT COUNT(*) FROM auth_user WHERE username = '{username}'
        """
        username = self.cleaned_data.get('username')
        
        if len(username) < 3:
            raise forms.ValidationError('O nome de usuário deve ter pelo menos 3 caracteres.')
        
        return username
    
    def save(self, commit=True):
        """
        Salva o usuário e cria o perfil
        
        OPERAÇÕES SQL:
        1. INSERT INTO auth_user (username, email, password, ...)
        2. INSERT INTO blog_perfilusuario (usuario_id, cpf, tipo_usuario, ativo, ...)
        """
        # SQL EXECUTADO:
        # INSERT INTO auth_user 
        # (username, email, password, is_active, date_joined)
        # VALUES ('{username}', '{email}', '{hashed_password}', 1, NOW())
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # SQL EXECUTADO:
            # INSERT INTO blog_perfilusuario 
            # (usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em)
            # VALUES ({user.id}, '{cpf}', 'comum', TRUE, NOW(), NOW())
            PerfilUsuario.objects.create(
                usuario=user,
                cpf=self.cleaned_data['cpf'],
                tipo_usuario='comum',
                ativo=True
            )
        
        return user



"""
========================================
FLUXO COMPLETO DE OPERAÇÕES SQL
========================================

EXEMPLO 1: CRIAR UM POST
--------------------------
1. Usuário acessa /post/novo/
   SQL: SELECT * FROM blog_categoria  (para popular dropdown)

2. Usuário preenche formulário e clica em "Publicar"
   SQL: INSERT INTO blog_post (titulo, slug, autor_id, conteudo, imagem, categoria_id, criado_em, atualizado_em)
        VALUES ('Meu Post', 'meu-post', 1, 'Conteúdo...', 'posts/imagem.jpg', 2, NOW(), NOW())

3. Redirecionamento para página do post
   SQL: SELECT * FROM blog_post WHERE slug = 'meu-post'


EXEMPLO 2: EDITAR UM POST
--------------------------
1. Usuário acessa /post/meu-post/editar/
   SQL 1: SELECT * FROM blog_post WHERE slug = 'meu-post'
   SQL 2: SELECT * FROM blog_categoria  (para popular dropdown)

2. Usuário altera dados e clica em "Atualizar"
   SQL: UPDATE blog_post 
        SET titulo='Novo Título', conteudo='Novo conteúdo', atualizado_em=NOW()
        WHERE id = 1


EXEMPLO 3: CADASTRAR USUÁRIO
-----------------------------
1. Usuário acessa /accounts/signup/
   (Nenhuma query SQL)

2. Usuário preenche dados e clica em "Cadastrar"
   SQL 1: SELECT COUNT(*) FROM auth_user WHERE username = 'novousuario'  (validação)
   SQL 2: SELECT COUNT(*) FROM auth_user WHERE email = 'email@exemplo.com'  (validação)
   SQL 3: INSERT INTO auth_user (username, email, password, date_joined) 
          VALUES ('novousuario', 'email@exemplo.com', 'hashed_pwd', NOW())
   SQL 4: INSERT INTO django_session (session_key, session_data, expire_date)
          VALUES ('abc123...', 'encrypted_data', '2025-12-01 10:00:00')


EXEMPLO 4: DELETAR POST COM CASCADE
------------------------------------
1. Usuário clica em "Excluir post"
   SQL 1: SELECT * FROM blog_post WHERE slug = 'meu-post'

2. Usuário confirma exclusão
   SQL 2: DELETE FROM blog_comentario WHERE post_id = 1  (CASCADE automático)
   SQL 3: DELETE FROM blog_reacaousuariopost WHERE post_id = 1  (CASCADE automático)
   SQL 4: DELETE FROM blog_post WHERE id = 1

========================================
VALIDAÇÕES E QUERIES DE VERIFICAÇÃO
========================================

Todos os formulários do Django executam queries de validação antes de salvar:

1. UNIQUE CONSTRAINTS:
   - Verifica se slug do post é único
   - Verifica se username é único
   - Verifica se email é único

2. FOREIGN KEY VALIDATION:
   - Verifica se categoria existe
   - Verifica se autor existe
   - Verifica se post existe (para comentários)

3. CLEAN METHODS:
   - Executam queries customizadas de validação
   - Exemplo: verificar se email já está cadastrado
"""