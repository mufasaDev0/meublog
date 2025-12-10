from django.contrib import admin
from .models import Post, Categoria, Comentario, ReacaoUsuarioPost, PerfilUsuario

"""
ADMIN DO DJANGO - OPERAÇÕES SQL AUTOMÁTICAS
"""


# ========================================
# REGISTRO: PerfilUsuario (NOVO)
# ========================================
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    """
    OPERAÇÕES SQL EXECUTADAS NO ADMIN DE PERFIS:
    
    1. LISTAR PERFIS:
       SELECT blog_perfilusuario.*, auth_user.username
       FROM blog_perfilusuario
       INNER JOIN auth_user ON blog_perfilusuario.usuario_id = auth_user.id
       ORDER BY id DESC
       LIMIT 100
    
    2. VER DETALHES DE UM PERFIL:
       SELECT * FROM blog_perfilusuario WHERE id = {perfil_id}
    
    3. EDITAR PERFIL (mudar tipo de usuário ou status ativo):
       UPDATE blog_perfilusuario 
       SET tipo_usuario = 'admin', ativo = TRUE, atualizado_em = NOW()
       WHERE id = {perfil_id}
    
    4. FILTRAR POR TIPO:
       SELECT * FROM blog_perfilusuario WHERE tipo_usuario = 'admin'
    
    5. FILTRAR POR STATUS:
       SELECT * FROM blog_perfilusuario WHERE ativo = TRUE
    """
    
    list_display = ['id', 'usuario', 'cpf_formatado', 'tipo_usuario', 'ativo', 'criado_em']
    list_filter = ['tipo_usuario', 'ativo', 'criado_em']
    search_fields = ['usuario__username', 'cpf']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('usuario', 'cpf')
        }),
        ('Tipo e Status', {
            'fields': ('tipo_usuario', 'ativo')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def cpf_formatado(self, obj):
        """Exibe CPF com formatação XXX.XXX.XXX-XX"""
        cpf = obj.cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    cpf_formatado.short_description = 'CPF'


# ========================================
# REGISTRO: Categoria
# ========================================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """
    OPERAÇÕES SQL EXECUTADAS NO ADMIN DE CATEGORIAS:
    
    1. LISTAR CATEGORIAS (página inicial):
       SELECT * FROM blog_categoria 
       ORDER BY id DESC 
       LIMIT 100
    
    2. VER DETALHES DE UMA CATEGORIA:
       SELECT * FROM blog_categoria 
       WHERE id = {categoria_id}
    
    3. ADICIONAR NOVA CATEGORIA:
       INSERT INTO blog_categoria (nome) 
       VALUES ('{nome}')
    
    4. EDITAR CATEGORIA:
       UPDATE blog_categoria 
       SET nome = '{novo_nome}' 
       WHERE id = {categoria_id}
    
    5. EXCLUIR CATEGORIA:
       DELETE FROM blog_categoria 
       WHERE id = {categoria_id}
    """
    
    list_display = ['id', 'nome', 'total_posts']
    search_fields = ['nome']
    ordering = ['nome']
    
    def total_posts(self, obj):
        """Conta quantos posts existem nesta categoria"""
        # SQL EXECUTADO:
        # SELECT COUNT(*) FROM blog_post WHERE categoria_id = {obj.id}
        return obj.post_set.count()
    
    total_posts.short_description = 'Total de Posts'


# ========================================
# REGISTRO: Post
# ========================================
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    OPERAÇÕES SQL EXECUTADAS NO ADMIN DE POSTS
    """
    
    list_display = ['id', 'titulo', 'autor', 'categoria', 'criado_em', 'atualizado_em']
    list_filter = ['categoria', 'criado_em', 'autor']
    search_fields = ['titulo', 'conteudo', 'autor__username']
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'criado_em'
    ordering = ['-criado_em']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Conteúdo', {
            'fields': ('titulo', 'slug', 'conteudo', 'imagem')
        }),
        ('Classificação', {
            'fields': ('autor', 'categoria')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


# ========================================
# REGISTRO: Comentario
# ========================================
@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    """
    OPERAÇÕES SQL EXECUTADAS NO ADMIN DE COMENTÁRIOS
    """
    
    list_display = ['id', 'autor', 'post', 'conteudo_resumido', 'criado_em', 'foi_editado']
    list_filter = ['criado_em', 'autor']
    search_fields = ['conteudo', 'autor__username', 'post__titulo']
    date_hierarchy = 'criado_em'
    ordering = ['-criado_em']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    def conteudo_resumido(self, obj):
        """Exibe apenas os primeiros 50 caracteres do comentário"""
        return obj.conteudo[:50] + '...' if len(obj.conteudo) > 50 else obj.conteudo
    
    conteudo_resumido.short_description = 'Conteúdo'
    
    def foi_editado(self, obj):
        """Indica se o comentário foi editado"""
        return obj.atualizado_em > obj.criado_em
    
    foi_editado.boolean = True
    foi_editado.short_description = 'Editado?'


# ========================================
# REGISTRO: ReacaoUsuarioPost
# ========================================
@admin.register(ReacaoUsuarioPost)
class ReacaoUsuarioPostAdmin(admin.ModelAdmin):
    """
    OPERAÇÕES SQL EXECUTADAS NO ADMIN DE REAÇÕES
    """
    
    list_display = ['id', 'usuario', 'post', 'tipo_reacao_emoji', 'criado_em']
    list_filter = ['tipo_reacao', 'criado_em']
    search_fields = ['usuario__username', 'post__titulo']
    date_hierarchy = 'criado_em'
    ordering = ['-criado_em']
    readonly_fields = ['criado_em']
    
    def tipo_reacao_emoji(self, obj):
        """Exibe o emoji da reação"""
        emojis = {
            'curtir': '👍',
            'amei': '❤️',
            'engraçado': '😂',
            'não_gostei': '👎',
        }
        emoji = emojis.get(obj.tipo_reacao, '❓')
        return f"{emoji} {obj.get_tipo_reacao_display()}"
    
    tipo_reacao_emoji.short_description = 'Reação'


"""
========================================
QUERIES SQL EXTRAS DO ADMIN
========================================

1. LOGIN NO ADMIN:
   SELECT * FROM auth_user 
   WHERE username = '{username}' AND is_staff = 1

2. VERIFICAR PERMISSÕES:
   SELECT * FROM auth_permission 
   WHERE user_id = {user_id}

3. LOG DE AÇÕES (django_admin_log):
   INSERT INTO django_admin_log 
   (user_id, content_type_id, object_id, object_repr, action_flag, change_message)
   VALUES ({user_id}, {content_type_id}, {object_id}, '{object_repr}', {action_flag}, '{change_message}')

4. CONTADORES:
   SELECT COUNT(*) FROM blog_post
   SELECT COUNT(*) FROM blog_comentario
   SELECT COUNT(*) FROM blog_reacaousuariopost
   SELECT COUNT(*) FROM blog_categoria
   SELECT COUNT(*) FROM blog_perfilusuario

========================================
OTIMIZAÇÃO DE QUERIES NO ADMIN
========================================

Se você quiser otimizar as queries do admin (reduzir número de consultas),
você pode usar select_related e prefetch_related:

class PostAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'categoria']
    
    def get_queryset(self, request):
        # SQL: Faz JOIN com autor e categoria em uma única query
        # Em vez de fazer 1 query para posts + N queries para autores + N queries para categorias
        return super().get_queryset(request).select_related('autor', 'categoria')
"""