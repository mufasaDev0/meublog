from django.urls import path
from . import views

urlpatterns = [
    # Posts
    path('', views.post_list, name='post_list'),
    path('post/novo/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/editar/', views.post_edit, name='post_edit'),
    path('post/<slug:slug>/excluir/', views.post_delete, name='post_delete'),
    
    # Reações (curtidas)
    path('post/<slug:slug>/curtir/', views.toggle_reacao, name='toggle_reacao'),
    
    # Comentários
    path('comentario/<int:comentario_id>/editar/', views.editar_comentario, name='editar_comentario'),
    path('comentario/<int:comentario_id>/excluir/', views.excluir_comentario, name='excluir_comentario'),
    
    # Gestão de usuários (apenas admin)
    path('usuario/<int:usuario_id>/desativar/', views.desativar_usuario, name='desativar_usuario'),
    path('usuario/<int:usuario_id>/ativar/', views.ativar_usuario, name='ativar_usuario'),
    
    # ============================================
    # PAINEL ADMINISTRATIVO
    # ============================================
    path('painel-admin/', views.painel_admin, name='painel_admin'),
    
    # Categorias (CRUD completo)
    path('admin/categorias/', views.admin_categorias, name='admin_categorias'),
    path('admin/categorias/criar/', views.admin_categoria_criar, name='admin_categoria_criar'),
    path('admin/categorias/<int:categoria_id>/editar/', views.admin_categoria_editar, name='admin_categoria_editar'),
    path('admin/categorias/<int:categoria_id>/excluir/', views.admin_categoria_excluir, name='admin_categoria_excluir'),
    
    # Posts (listagem para admin)
    path('admin/posts/', views.admin_posts, name='admin_posts'),
    
    # Usuários (listagem para admin)
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
]