from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Comentario, ReacaoUsuarioPost, Categoria, PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import PostForm, CustomUserCreationForm, ComentarioForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.core.exceptions import PermissionDenied


def usuario_e_admin(user):
    """
    Verifica se usuário é admin
    
    OPERAÇÃO SQL:
    SELECT * FROM blog_perfilusuario WHERE usuario_id = {user.id}
    """
    return hasattr(user, 'perfil') and user.perfil.is_admin()


def post_list(request):
    """Lista posts com filtro opcional por categoria"""
    
    categoria_id = request.GET.get('categoria', None)
    categoria_selecionada = None
    
    if categoria_id:
        try:
            categoria_id = int(categoria_id)
            posts = Post.objects.filter(categoria_id=categoria_id).order_by('-criado_em')
            categoria_selecionada = get_object_or_404(Categoria, id=categoria_id)
        except (ValueError, TypeError):
            posts = Post.objects.all().order_by('-criado_em')
            categoria_selecionada = None
    else:
        posts = Post.objects.all().order_by('-criado_em')
    
    categorias_com_contagem = Categoria.objects.annotate(
        total_posts=Count('post')
    ).order_by('nome')
    
    if categoria_selecionada:
        total_posts = posts.count()
    else:
        total_posts = Post.objects.count()
    
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'categorias': categorias_com_contagem,
        'categoria_selecionada': categoria_selecionada,
        'total_posts': total_posts
    })


def post_detail(request, slug):
    """Exibe post com comentários e permite comentar"""
    
    post = get_object_or_404(Post, slug=slug)
    comentarios = post.comentarios.all().order_by('-criado_em')
    
    reacao_usuario = None
    if request.user.is_authenticated:
        reacao_usuario = post.reacoes.filter(usuario=request.user).first()
    
    reacoes_contagem = post.reacoes.values('tipo_reacao').annotate(
        total=Count('id')
    ).order_by('tipo_reacao')
    
    reacoes_dict = {r['tipo_reacao']: r['total'] for r in reacoes_contagem}
    total_reacoes = post.reacoes.count()
    
    # Processa novo comentário
    if request.method == 'POST' and request.user.is_authenticated:
        conteudo = request.POST.get('conteudo', '').strip()
        if conteudo:
            try:
                # SQL EXECUTADO:
                # INSERT INTO blog_comentario 
                # (post_id, autor_id, conteudo, criado_em, atualizado_em) 
                # VALUES ({post.id}, {request.user.id}, '{conteudo}', NOW(), NOW())
                Comentario.objects.create(
                    post=post,
                    autor=request.user,
                    conteudo=conteudo
                )
                messages.success(request, 'Comentário adicionado com sucesso!')
                return redirect('post_detail', slug=slug)
            except Exception as e:
                messages.error(request, f'Erro ao adicionar comentário: {str(e)}')
        else:
            messages.error(request, 'O comentário não pode estar vazio.')
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comentarios': comentarios,
        'reacao_usuario': reacao_usuario,
        'reacoes_dict': reacoes_dict,
        'total_reacoes': total_reacoes
    })


@login_required
@require_POST
def toggle_reacao(request, slug):
    """Curtir/descurtir post com múltiplas opções de reação via AJAX"""
    
    try:
        post = get_object_or_404(Post, slug=slug)
        tipo_reacao = request.POST.get('tipo_reacao', 'curtir')
        
        tipos_validos = ['curtir', 'amei', 'engraçado', 'não_gostei']
        if tipo_reacao not in tipos_validos:
            return JsonResponse({'erro': 'Tipo de reação inválido', 'sucesso': False}, status=400)
        
        reacao = ReacaoUsuarioPost.objects.filter(usuario=request.user, post=post).first()
        reacao_adicionada = False
        
        if reacao:
            if reacao.tipo_reacao == tipo_reacao:
                reacao.delete()
                reacao_adicionada = False
            else:
                reacao.tipo_reacao = tipo_reacao
                reacao.save()
                reacao_adicionada = True
        else:
            ReacaoUsuarioPost.objects.create(usuario=request.user, post=post, tipo_reacao=tipo_reacao)
            reacao_adicionada = True
        
        reacoes_contagem = post.reacoes.values('tipo_reacao').annotate(total=Count('id')).order_by('tipo_reacao')
        reacoes_dict = {r['tipo_reacao']: r['total'] for r in reacoes_contagem}
        total_reacoes = post.reacoes.count()
        
        return JsonResponse({
            'sucesso': True,
            'reacao_adicionada': reacao_adicionada,
            'tipo_reacao': tipo_reacao,
            'reacoes': reacoes_dict,
            'total_reacoes': total_reacoes
        })
        
    except Exception as e:
        return JsonResponse({'erro': str(e), 'sucesso': False}, status=500)


@login_required
def editar_comentario(request, comentario_id):
    """
    Permite editar comentário (só o autor)
    
    OPERAÇÕES SQL:
    1. SELECT em blog_comentario (busca o comentário)
    2. UPDATE em blog_comentario (atualiza o comentário)
    """
    
    try:
        # SQL EXECUTADO:
        # SELECT * FROM blog_comentario WHERE id = {comentario_id}
        comentario = get_object_or_404(Comentario, id=comentario_id)
        
        # Apenas o autor pode editar seu próprio comentário
        if request.user != comentario.autor:
            messages.error(request, 'Você não tem permissão para editar este comentário.')
            return redirect('post_detail', slug=comentario.post.slug)
        
        if request.method == 'POST':
            form = ComentarioForm(request.POST, instance=comentario)
            if form.is_valid():
                # SQL EXECUTADO:
                # UPDATE blog_comentario 
                # SET conteudo = '{novo_conteudo}', atualizado_em = NOW()
                # WHERE id = {comentario_id}
                form.save()
                messages.success(request, 'Comentário atualizado com sucesso!')
                return redirect('post_detail', slug=comentario.post.slug)
        else:
            form = ComentarioForm(instance=comentario)
        
        return render(request, 'blog/comentario_form.html', {
            'form': form,
            'comentario': comentario
        })
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('post_list')


@login_required
def excluir_comentario(request, comentario_id):
    """
    Permite excluir comentário (autor ou admin)
    
    OPERAÇÕES SQL:
    1. SELECT em blog_comentario (busca o comentário)
    2. SELECT em blog_perfilusuario (verifica se é admin)
    3. DELETE em blog_comentario (exclui o comentário)
    """
    
    try:
        # SQL EXECUTADO:
        # SELECT * FROM blog_comentario WHERE id = {comentario_id}
        comentario = get_object_or_404(Comentario, id=comentario_id)
        
        # Autor ou admin podem excluir
        # SQL EXECUTADO (para verificar admin):
        # SELECT * FROM blog_perfilusuario WHERE usuario_id = {request.user.id}
        if request.user == comentario.autor or usuario_e_admin(request.user):
            post_slug = comentario.post.slug
            
            # SQL EXECUTADO:
            # DELETE FROM blog_comentario WHERE id = {comentario_id}
            comentario.delete()
            
            messages.success(request, 'Comentário excluído com sucesso.')
            return redirect('post_detail', slug=post_slug)
        else:
            messages.error(request, 'Você não tem permissão para excluir este comentário.')
            return redirect('post_detail', slug=comentario.post.slug)
            
    except Exception as e:
        messages.error(request, f'Erro ao excluir comentário: {str(e)}')
        return redirect('post_list')


def signup(request):
    """
    Cadastro de novos usuários com email e CPF obrigatórios
    
    OPERAÇÕES SQL:
    1. SELECT COUNT em auth_user (validação username)
    2. SELECT COUNT em auth_user (validação email)
    3. SELECT COUNT em blog_perfilusuario (validação CPF)
    4. INSERT em auth_user (cria usuário)
    5. INSERT em blog_perfilusuario (cria perfil)
    6. INSERT em django_session (login automático)
    """
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.username}! Sua conta foi criada com sucesso.')
                return redirect('welcome')
            except Exception as e:
                messages.error(request, f'Erro ao criar conta: {str(e)}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def welcome(request):
    """Página de boas-vindas após cadastro"""
    return render(request, 'registration/welcome.html')


@login_required
def post_create(request):
    """Criar novo post"""
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.autor = request.user
                post.save()
                messages.success(request, 'Post criado com sucesso!')
                return redirect('post_detail', slug=post.slug)
            except Exception as e:
                messages.error(request, f'Erro ao criar post: {str(e)}')
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {'form': form})


@login_required
def post_edit(request, slug):
    """Editar post existente (autor ou admin)"""
    
    try:
        post = get_object_or_404(Post, slug=slug)

        # Autor ou admin podem editar
        if post.autor != request.user and not usuario_e_admin(request.user):
            messages.error(request, 'Você não tem permissão para editar este post.')
            return redirect('post_detail', slug=slug)

        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES, instance=post)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, 'Post atualizado com sucesso!')
                    return redirect('post_detail', slug=post.slug)
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar post: {str(e)}')
        else:
            form = PostForm(instance=post)
        
        return render(request, 'blog/post_form.html', {'form': form})
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('post_list')


@login_required
def post_delete(request, slug):
    """
    Excluir post (autor ou admin)
    
    OPERAÇÕES SQL:
    1. SELECT em blog_post (busca o post)
    2. SELECT em blog_perfilusuario (verifica se é admin)
    3. DELETE em blog_comentario (CASCADE)
    4. DELETE em blog_reacaousuariopost (CASCADE)
    5. DELETE em blog_post (exclui o post)
    """
    
    try:
        post = get_object_or_404(Post, slug=slug)

        # Autor ou admin podem excluir
        if not (request.user == post.autor or usuario_e_admin(request.user)):
            messages.error(request, "Você não tem permissão para excluir este post.")
            return redirect('post_detail', slug=slug)

        if request.method == 'POST':
            try:
                post.delete()
                messages.success(request, "Post excluído com sucesso.")
                return redirect('post_list')
            except Exception as e:
                messages.error(request, f'Erro ao excluir post: {str(e)}')
                return redirect('post_detail', slug=slug)

        return render(request, 'blog/post_confirm_delete.html', {'post': post})
        
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('post_list')


@login_required
def desativar_usuario(request, usuario_id):
    """
    Desativa um usuário (apenas admin)
    
    OPERAÇÕES SQL:
    1. SELECT em auth_user (busca usuário)
    2. SELECT em blog_perfilusuario (busca perfil)
    3. UPDATE em blog_perfilusuario (desativa usuário)
    """
    
    # Verifica se o usuário logado é admin
    if not usuario_e_admin(request.user):
        messages.error(request, 'Você não tem permissão para desativar usuários.')
        return redirect('post_list')
    
    try:
        # SQL EXECUTADO:
        # SELECT * FROM auth_user WHERE id = {usuario_id}
        usuario = get_object_or_404(User, id=usuario_id)
        
        # Não permite desativar a si mesmo
        if usuario == request.user:
            messages.error(request, 'Você não pode desativar sua própria conta.')
            return redirect('post_list')
        
        # SQL EXECUTADO:
        # SELECT * FROM blog_perfilusuario WHERE usuario_id = {usuario_id}
        if hasattr(usuario, 'perfil'):
            # SQL EXECUTADO:
            # UPDATE blog_perfilusuario 
            # SET ativo = FALSE, atualizado_em = NOW()
            # WHERE usuario_id = {usuario_id}
            usuario.perfil.desativar()
            messages.success(request, f'Usuário {usuario.username} foi desativado.')
        else:
            messages.error(request, 'Usuário não possui perfil.')
        
        return redirect('post_list')
        
    except Exception as e:
        messages.error(request, f'Erro ao desativar usuário: {str(e)}')
        return redirect('post_list')


@login_required
def ativar_usuario(request, usuario_id):
    """
    Reativa um usuário (apenas admin)
    
    OPERAÇÕES SQL:
    1. SELECT em auth_user (busca usuário)
    2. SELECT em blog_perfilusuario (busca perfil)
    3. UPDATE em blog_perfilusuario (ativa usuário)
    """
    
    # Verifica se o usuário logado é admin
    if not usuario_e_admin(request.user):
        messages.error(request, 'Você não tem permissão para ativar usuários.')
        return redirect('post_list')
    
    try:
        usuario = get_object_or_404(User, id=usuario_id)
        
        if hasattr(usuario, 'perfil'):
            # SQL EXECUTADO:
            # UPDATE blog_perfilusuario 
            # SET ativo = TRUE, atualizado_em = NOW()
            # WHERE usuario_id = {usuario_id}
            usuario.perfil.ativar()
            messages.success(request, f'Usuário {usuario.username} foi reativado.')
        else:
            messages.error(request, 'Usuário não possui perfil.')
        
        return redirect('post_list')
        
    except Exception as e:
        messages.error(request, f'Erro ao ativar usuário: {str(e)}')
        return redirect('post_list')