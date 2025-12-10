from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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

    # Recuperação de senha com templates personalizados
    path(
        'accounts/password_reset/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]