from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

"""
TABELAS CRIADAS NO BANCO DE DADOS:
1. blog_categoria
2. blog_post
3. blog_comentario
4. blog_reacaousuariopost
5. blog_perfilusuario (NOVA)
6. auth_user (tabela padrão do Django)
"""


class PerfilUsuario(models.Model):
    """
    TABELA: blog_perfilusuario
    
    SQL DE CRIAÇÃO:
    CREATE TABLE blog_perfilusuario (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER UNIQUE NOT NULL,
        cpf VARCHAR(11) UNIQUE NOT NULL,
        tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'comum',
        ativo BOOLEAN NOT NULL DEFAULT TRUE,
        criado_em TIMESTAMP NOT NULL,
        atualizado_em TIMESTAMP NOT NULL,
        
        CONSTRAINT fk_usuario 
            FOREIGN KEY (usuario_id) 
            REFERENCES auth_user(id) 
            ON DELETE CASCADE
    );
    
    ÍNDICES CRIADOS AUTOMATICAMENTE:
    - PRIMARY KEY: id
    - UNIQUE INDEX: usuario_id (um perfil por usuário)
    - UNIQUE INDEX: cpf (CPF único no sistema)
    - INDEX: tipo_usuario (para filtrar por tipo)
    """
    
    # Tipos de usuário disponíveis
    TIPO_USUARIO_CHOICES = [
        ('comum', 'Usuário Comum'),
        ('admin', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='perfil'
    )
    # Campo: usuario_id INTEGER UNIQUE NOT NULL
    # FOREIGN KEY: Referencia auth_user.id
    # ON DELETE CASCADE: Se usuário for excluído, perfil também é excluído
    # UNIQUE: Um perfil por usuário
    
    cpf = models.CharField(max_length=11, unique=True)
    # Campo: cpf VARCHAR(11) UNIQUE NOT NULL
    # Armazena CPF SEM formatação (apenas números)
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='comum'
    )
    # Campo: tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'comum'
    # Valores possíveis: 'comum' ou 'admin'
    
    ativo = models.BooleanField(default=True)
    # Campo: ativo BOOLEAN NOT NULL DEFAULT TRUE
    # Se FALSE, usuário não pode fazer login
    
    criado_em = models.DateTimeField(auto_now_add=True)
    # Campo: criado_em TIMESTAMP NOT NULL DEFAULT NOW()
    
    atualizado_em = models.DateTimeField(auto_now=True)
    # Campo: atualizado_em TIMESTAMP NOT NULL
    
    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
    
    def __str__(self):
        return f"Perfil de {self.usuario.username} ({self.get_tipo_usuario_display()})"
    
    def is_admin(self):
        """
        Verifica se o usuário é admin
        
        OPERAÇÃO SQL: Nenhuma (acesso em memória ao campo tipo_usuario)
        """
        return self.tipo_usuario == 'admin'
    
    def desativar(self):
        """
        Desativa o usuário (não exclui, apenas impede login)
        
        OPERAÇÃO SQL:
        UPDATE blog_perfilusuario 
        SET ativo = FALSE, atualizado_em = NOW()
        WHERE id = {self.id}
        """
        self.ativo = False
        self.save()
    
    def ativar(self):
        """
        Reativa o usuário
        
        OPERAÇÃO SQL:
        UPDATE blog_perfilusuario 
        SET ativo = TRUE, atualizado_em = NOW()
        WHERE id = {self.id}
        """
        self.ativo = True
        self.save()


@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Signal que cria automaticamente um perfil quando um usuário é criado
    
    OPERAÇÃO SQL (executada APÓS criação de usuário):
    Se created=True (novo usuário):
        INSERT INTO blog_perfilusuario 
        (usuario_id, cpf, tipo_usuario, ativo, criado_em, atualizado_em)
        VALUES ({instance.id}, '{cpf}', 'comum', TRUE, NOW(), NOW())
    
    NOTA: O CPF precisa ser definido manualmente após a criação
    """
    # Este signal será usado para garantir que todo usuário tenha um perfil
    # O CPF será definido durante o cadastro
    pass


class Categoria(models.Model):
    """
    TABELA: blog_categoria
    
    SQL DE CRIAÇÃO:
    CREATE TABLE blog_categoria (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100) UNIQUE NOT NULL
    );
    """
    
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Post(models.Model):
    """
    TABELA: blog_post
    """
    
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='posts/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Comentario(models.Model):
    """
    TABELA: blog_comentario
    
    SQL DE CRIAÇÃO:
    CREATE TABLE blog_comentario (
        id SERIAL PRIMARY KEY,
        post_id INTEGER NOT NULL,
        autor_id INTEGER,
        conteudo VARCHAR(1000) NOT NULL,
        criado_em TIMESTAMP NOT NULL,
        atualizado_em TIMESTAMP NOT NULL,
        
        CONSTRAINT fk_post 
            FOREIGN KEY (post_id) 
            REFERENCES blog_post(id) 
            ON DELETE CASCADE,
            
        CONSTRAINT fk_autor 
            FOREIGN KEY (autor_id) 
            REFERENCES auth_user(id) 
            ON DELETE SET NULL
    );
    """
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    conteudo = models.TextField(max_length=1000)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)  # NOVO: para edição

    def __str__(self):
        return f'Comentário de {self.autor} em {self.post}'


class ReacaoUsuarioPost(models.Model):
    """
    TABELA: blog_reacaousuariopost
    """
    
    TIPOS_REACAO = [
        ('curtir', '👍 Curtir'),
        ('amei', '❤️ Amei'),
        ('engraçado', '😂 Engraçado'),
        ('não_gostei', '👎 Não gostei'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reacoes')
    tipo_reacao = models.CharField(max_length=50, choices=TIPOS_REACAO, default='curtir')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'post')
        verbose_name = 'Reação do Usuário'
        verbose_name_plural = 'Reações dos Usuários'

    def __str__(self):
        return f'{self.usuario} -> {self.get_tipo_reacao_display()} em {self.post}'

    @staticmethod
    def get_emoji(tipo_reacao):
        emojis = {
            'curtir': '👍',
            'amei': '❤️',
            'engraçado': '😂',
            'não_gostei': '👎',
        }
        return emojis.get(tipo_reacao, '👍')
    
"""
RELACIONAMENTOS E QUERIES COMUNS:

1. BUSCAR TODOS OS POSTS DE UM AUTOR:
   Python: Post.objects.filter(autor=usuario)
   SQL: SELECT * FROM blog_post WHERE autor_id = {usuario.id}

2. BUSCAR TODOS OS COMENTÁRIOS DE UM POST:
   Python: post.comentarios.all()
   SQL: SELECT * FROM blog_comentario WHERE post_id = {post.id}

3. CONTAR CURTIDAS DE UM POST:
   Python: post.reacoes.count()
   SQL: SELECT COUNT(*) FROM blog_reacaousuariopost WHERE post_id = {post.id}

4. VERIFICAR SE USUÁRIO CURTIU UM POST:
   Python: post.reacoes.filter(usuario=usuario).exists()
   SQL: SELECT EXISTS(SELECT 1 FROM blog_reacaousuariopost WHERE post_id={post.id} AND usuario_id={usuario.id})

5. BUSCAR POSTS POR CATEGORIA:
   Python: Post.objects.filter(categoria=categoria)
   SQL: SELECT * FROM blog_post WHERE categoria_id = {categoria.id}

6. BUSCAR POSTS COM SUAS CATEGORIAS (JOIN):
   Python: Post.objects.select_related('categoria', 'autor').all()
   SQL: SELECT blog_post.*, blog_categoria.nome, auth_user.username 
        FROM blog_post
        LEFT JOIN blog_categoria ON blog_post.categoria_id = blog_categoria.id
        LEFT JOIN auth_user ON blog_post.autor_id = auth_user.id

7. BUSCAR POSTS COM CONTAGEM DE COMENTÁRIOS:
   Python: Post.objects.annotate(num_comentarios=Count('comentarios'))
   SQL: SELECT blog_post.*, COUNT(blog_comentario.id) as num_comentarios
        FROM blog_post
        LEFT JOIN blog_comentario ON blog_post.id = blog_comentario.post_id
        GROUP BY blog_post.id
"""