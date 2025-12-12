from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import connection
from .forms import PostForm, CustomUserCreationForm, ComentarioForm


def usuario_e_admin(user):
    """
    Verifica se usuário é admin usando SQL puro
    
    SQL EXECUTADO:
    SELECT tipo_usuario FROM blog_perfilusuario WHERE usuario_id = %s
    """
    if not user.is_authenticated:
        return False
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tipo_usuario 
            FROM blog_perfilusuario 
            WHERE usuario_id = %s
        """, [user.id])
        
        resultado = cursor.fetchone()
        return resultado and resultado[0] == 'admin'


def post_list(request):
    """
    Lista posts com filtro opcional por categoria
    
    SQL EXECUTADO:
    1. SELECT posts (com/sem filtro de categoria)
    2. SELECT categorias com contagem de posts
    3. COUNT total de posts
    """
    categoria_id = request.GET.get('categoria', None)
    categoria_selecionada = None
    
    with connection.cursor() as cursor:
        # Query para posts
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
                
                # SQL: Buscar posts filtrados por categoria
                cursor.execute("""
                    SELECT p.id, p.titulo, p.slug, p.conteudo, p.imagem, 
                           p.criado_em, p.atualizado_em, p.categoria_id,
                           u.id as autor_id, u.username as autor_username,
                           c.nome as categoria_nome,
                           (SELECT COUNT(*) FROM blog_comentario WHERE post_id = p.id) as total_comentarios,
                           (SELECT COUNT(*) FROM blog_reacaousuariopost WHERE post_id = p.id) as total_reacoes
                    FROM blog_post p
                    INNER JOIN auth_user u ON p.autor_id = u.id
                    LEFT JOIN blog_categoria c ON p.categoria_id = c.id
                    WHERE p.categoria_id = %s
                    ORDER BY p.criado_em DESC
                """, [categoria_id])
                
                posts = cursor.fetchall()
                
                # SQL: Buscar nome da categoria selecionada
                cursor.execute("""
                    SELECT id, nome 
                    FROM blog_categoria 
                    WHERE id = %s
                """, [categoria_id])
                
                cat_data = cursor.fetchone()
                if cat_data:
                    categoria_selecionada = {'id': cat_data[0], 'nome': cat_data[1]}
                
            except (ValueError, TypeError):
                categoria_id = None
                # SQL: Buscar todos os posts
                cursor.execute("""
                    SELECT p.id, p.titulo, p.slug, p.conteudo, p.imagem, 
                           p.criado_em, p.atualizado_em, p.categoria_id,
                           u.id as autor_id, u.username as autor_username,
                           c.nome as categoria_nome,
                           (SELECT COUNT(*) FROM blog_comentario WHERE post_id = p.id) as total_comentarios,
                           (SELECT COUNT(*) FROM blog_reacaousuariopost WHERE post_id = p.id) as total_reacoes
                    FROM blog_post p
                    INNER JOIN auth_user u ON p.autor_id = u.id
                    LEFT JOIN blog_categoria c ON p.categoria_id = c.id
                    ORDER BY p.criado_em DESC
                """)
                
                posts = cursor.fetchall()
        else:
            # SQL: Buscar todos os posts
            cursor.execute("""
                SELECT p.id, p.titulo, p.slug, p.conteudo, p.imagem, 
                       p.criado_em, p.atualizado_em, p.categoria_id,
                       u.id as autor_id, u.username as autor_username,
                       c.nome as categoria_nome,
                       (SELECT COUNT(*) FROM blog_comentario WHERE post_id = p.id) as total_comentarios,
                       (SELECT COUNT(*) FROM blog_reacaousuariopost WHERE post_id = p.id) as total_reacoes
                FROM blog_post p
                INNER JOIN auth_user u ON p.autor_id = u.id
                LEFT JOIN blog_categoria c ON p.categoria_id = c.id
                ORDER BY p.criado_em DESC
            """)
            
            posts = cursor.fetchall()
        
        # SQL: Buscar categorias com contagem
        cursor.execute("""
            SELECT c.id, c.nome, COUNT(p.id) as total_posts
            FROM blog_categoria c
            LEFT JOIN blog_post p ON c.id = p.categoria_id
            GROUP BY c.id, c.nome
            ORDER BY c.nome
        """)
        
        categorias = cursor.fetchall()
        
        # SQL: Total de posts
        if categoria_selecionada:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM blog_post 
                WHERE categoria_id = %s
            """, [categoria_id])
        else:
            cursor.execute("SELECT COUNT(*) FROM blog_post")
        
        total_posts = cursor.fetchone()[0]
    
    # Formatar dados para o template
    posts_list = []
    for post in posts:
        # Criar objeto mock para o autor
        class AutorMock:
            def __init__(self, user_id, username):
                self.id = user_id
                self.username = username
            def __str__(self):
                return self.username
        
        # Criar objeto mock para categoria
        class CategoriaMock:
            def __init__(self, nome):
                self.nome = nome if nome else None
            def __str__(self):
                return self.nome if self.nome else ""
        
        # Criar objeto mock para comentários
        class ComentariosMock:
            def __init__(self, total):
                self._total = total
            def count(self):
                return self._total
        
        # Criar objeto mock para reações
        class ReacoesMock:
            def __init__(self, total):
                self._total = total
            def count(self):
                return self._total
        
        # Criar objeto mock para imagem
        class ImagemMock:
            def __init__(self, url):
                # Adicionar prefixo /media/ se não existir
                if url and not url.startswith('/media/') and not url.startswith('http'):
                    self.url = f'/media/{url}'
                else:
                    self.url = url if url else ''
        
        posts_list.append({
            'id': post[0],
            'titulo': post[1],
            'slug': post[2],
            'conteudo': post[3],
            'imagem': ImagemMock(post[4]) if post[4] else None,
            'criado_em': post[5],
            'atualizado_em': post[6],
            'categoria': CategoriaMock(post[10]),
            'autor': AutorMock(post[8], post[9]),
            'comentarios': ComentariosMock(post[11]),
            'reacoes': ReacoesMock(post[12])
        })
    
    categorias_list = []
    for cat in categorias:
        categorias_list.append({
            'id': cat[0],
            'nome': cat[1],
            'total_posts': cat[2]
        })
    
    return render(request, 'blog/post_list.html', {
        'posts': posts_list,
        'categorias': categorias_list,
        'categoria_selecionada': categoria_selecionada,
        'total_posts': total_posts
    })


def post_detail(request, slug):
    """
    Exibe post com comentários e permite comentar
    
    SQL EXECUTADO:
    1. SELECT post por slug
    2. SELECT comentários do post
    3. SELECT reação do usuário (se autenticado)
    4. SELECT contagem de reações por tipo
    5. INSERT comentário (se POST)
    """
    with connection.cursor() as cursor:
        # SQL: Buscar post por slug
        cursor.execute("""
            SELECT p.id, p.titulo, p.slug, p.conteudo, p.imagem, 
                   p.criado_em, p.atualizado_em, p.categoria_id,
                   u.id as autor_id, u.username as autor_username,
                   c.nome as categoria_nome
            FROM blog_post p
            INNER JOIN auth_user u ON p.autor_id = u.id
            LEFT JOIN blog_categoria c ON p.categoria_id = c.id
            WHERE p.slug = %s
        """, [slug])
        
        post_data = cursor.fetchone()
        
        if not post_data:
            messages.error(request, 'Post não encontrado.')
            return redirect('post_list')
        
        # Criar objetos mock para o template
        class AutorMock:
            def __init__(self, user_id, username):
                self.id = user_id
                self.username = username
            def __str__(self):
                return self.username
            def __eq__(self, other):
                if hasattr(other, 'id'):
                    return self.id == other.id
                return False
        
        class CategoriaMock:
            def __init__(self, nome):
                self.nome = nome
            def __str__(self):
                return self.nome if self.nome else ""
        
        class ImagemMock:
            def __init__(self, url):
                # Adicionar prefixo /media/ se não existir
                if url and not url.startswith('/media/') and not url.startswith('http'):
                    self.url = f'/media/{url}'
                else:
                    self.url = url if url else ''
        
        post = {
            'id': post_data[0],
            'titulo': post_data[1],
            'slug': post_data[2],
            'conteudo': post_data[3],
            'imagem': ImagemMock(post_data[4]) if post_data[4] else None,
            'criado_em': post_data[5],
            'atualizado_em': post_data[6],
            'categoria': CategoriaMock(post_data[10]) if post_data[10] else None,
            'autor': AutorMock(post_data[8], post_data[9])
        }
        
        # SQL: Buscar comentários do post
        cursor.execute("""
            SELECT c.id, c.conteudo, c.criado_em, c.atualizado_em,
                   u.id as autor_id, u.username as autor_username
            FROM blog_comentario c
            INNER JOIN auth_user u ON c.autor_id = u.id
            WHERE c.post_id = %s
            ORDER BY c.criado_em DESC
        """, [post['id']])
        
        comentarios_data = cursor.fetchall()
        comentarios = []
        for com in comentarios_data:
            # Criar objeto mock para autor do comentário
            class ComentarioAutorMock:
                def __init__(self, user_id, username):
                    self.id = user_id
                    self.username = username
                def __str__(self):
                    return self.username
                def __eq__(self, other):
                    if hasattr(other, 'id'):
                        return self.id == other.id
                    return False
            
            comentarios.append({
                'id': com[0],
                'conteudo': com[1],
                'criado_em': com[2],
                'atualizado_em': com[3],
                'autor': ComentarioAutorMock(com[4], com[5])
            })
        
        # Criar wrapper para lista de comentários com método count()
        class ComentariosListMock(list):
            def count(self):
                return len(self)
        
        comentarios = ComentariosListMock(comentarios)
        
        # SQL: Verificar reação do usuário (se autenticado)
        reacao_usuario = None
        if request.user.is_authenticated:
            cursor.execute("""
                SELECT id, tipo_reacao
                FROM blog_reacaousuariopost
                WHERE usuario_id = %s AND post_id = %s
            """, [request.user.id, post['id']])
            
            reacao_data = cursor.fetchone()
            if reacao_data:
                reacao_usuario = {
                    'id': reacao_data[0],
                    'tipo_reacao': reacao_data[1]
                }
        
        # SQL: Contar reações por tipo
        cursor.execute("""
            SELECT tipo_reacao, COUNT(*) as total
            FROM blog_reacaousuariopost
            WHERE post_id = %s
            GROUP BY tipo_reacao
        """, [post['id']])
        
        reacoes_contagem = cursor.fetchall()
        reacoes_dict = {r[0]: r[1] for r in reacoes_contagem}
        
        # SQL: Total de reações
        cursor.execute("""
            SELECT COUNT(*)
            FROM blog_reacaousuariopost
            WHERE post_id = %s
        """, [post['id']])
        
        total_reacoes = cursor.fetchone()[0]
        
        # Processar novo comentário (POST)
        if request.method == 'POST' and request.user.is_authenticated:
            conteudo = request.POST.get('conteudo', '').strip()
            if conteudo:
                try:
                    # SQL: Inserir novo comentário
                    cursor.execute("""
                        INSERT INTO blog_comentario 
                        (post_id, autor_id, conteudo, criado_em, atualizado_em)
                        VALUES (%s, %s, %s, NOW(), NOW())
                    """, [post['id'], request.user.id, conteudo])
                    
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
    """
    Curtir/descurtir post com múltiplas opções de reação via AJAX
    
    SQL EXECUTADO:
    1. SELECT post por slug
    2. SELECT reação existente do usuário
    3. INSERT/UPDATE/DELETE reação
    4. SELECT contagem de reações atualizada
    """
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar post
            cursor.execute("""
                SELECT id FROM blog_post WHERE slug = %s
            """, [slug])
            
            post_data = cursor.fetchone()
            if not post_data:
                return JsonResponse({'erro': 'Post não encontrado', 'sucesso': False}, status=404)
            
            post_id = post_data[0]
            tipo_reacao = request.POST.get('tipo_reacao', 'curtir')
            
            tipos_validos = ['curtir', 'amei', 'engraçado', 'não_gostei']
            if tipo_reacao not in tipos_validos:
                return JsonResponse({'erro': 'Tipo de reação inválido', 'sucesso': False}, status=400)
            
            # SQL: Verificar reação existente
            cursor.execute("""
                SELECT id, tipo_reacao
                FROM blog_reacaousuariopost
                WHERE usuario_id = %s AND post_id = %s
            """, [request.user.id, post_id])
            
            reacao_existente = cursor.fetchone()
            reacao_adicionada = False
            
            if reacao_existente:
                if reacao_existente[1] == tipo_reacao:
                    # SQL: Remover reação (mesmo tipo clicado novamente)
                    cursor.execute("""
                        DELETE FROM blog_reacaousuariopost
                        WHERE id = %s
                    """, [reacao_existente[0]])
                    reacao_adicionada = False
                else:
                    # SQL: Atualizar tipo de reação
                    cursor.execute("""
                        UPDATE blog_reacaousuariopost
                        SET tipo_reacao = %s
                        WHERE id = %s
                    """, [tipo_reacao, reacao_existente[0]])
                    reacao_adicionada = True
            else:
                # SQL: Inserir nova reação
                cursor.execute("""
                    INSERT INTO blog_reacaousuariopost
                    (usuario_id, post_id, tipo_reacao, criado_em)
                    VALUES (%s, %s, %s, NOW())
                """, [request.user.id, post_id, tipo_reacao])
                reacao_adicionada = True
            
            # SQL: Buscar contagem atualizada de reações
            cursor.execute("""
                SELECT tipo_reacao, COUNT(*) as total
                FROM blog_reacaousuariopost
                WHERE post_id = %s
                GROUP BY tipo_reacao
            """, [post_id])
            
            reacoes_contagem = cursor.fetchall()
            reacoes_dict = {r[0]: r[1] for r in reacoes_contagem}
            
            # SQL: Total de reações
            cursor.execute("""
                SELECT COUNT(*)
                FROM blog_reacaousuariopost
                WHERE post_id = %s
            """, [post_id])
            
            total_reacoes = cursor.fetchone()[0]
            
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
    
    SQL EXECUTADO:
    1. SELECT comentário por ID
    2. UPDATE comentário (se POST)
    """
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar comentário
            cursor.execute("""
                SELECT c.id, c.conteudo, c.criado_em, c.atualizado_em,
                       c.post_id, c.autor_id,
                       p.slug as post_slug,
                       u.username as autor_username
                FROM blog_comentario c
                INNER JOIN blog_post p ON c.post_id = p.id
                INNER JOIN auth_user u ON c.autor_id = u.id
                WHERE c.id = %s
            """, [comentario_id])
            
            comentario_data = cursor.fetchone()
            
            if not comentario_data:
                messages.error(request, 'Comentário não encontrado.')
                return redirect('post_list')
            
            comentario = {
                'id': comentario_data[0],
                'conteudo': comentario_data[1],
                'criado_em': comentario_data[2],
                'atualizado_em': comentario_data[3],
                'post': {'id': comentario_data[4], 'slug': comentario_data[6]},
                'autor': {'id': comentario_data[5], 'username': comentario_data[7]}
            }
            
            # Verificar se o usuário é o autor
            if request.user.id != comentario['autor']['id']:
                messages.error(request, 'Você não tem permissão para editar este comentário.')
                return redirect('post_detail', slug=comentario['post']['slug'])
            
            if request.method == 'POST':
                novo_conteudo = request.POST.get('conteudo', '').strip()
                
                if not novo_conteudo:
                    messages.error(request, 'O comentário não pode estar vazio.')
                elif len(novo_conteudo) < 3:
                    messages.error(request, 'O comentário deve ter pelo menos 3 caracteres.')
                else:
                    # SQL: Atualizar comentário
                    cursor.execute("""
                        UPDATE blog_comentario
                        SET conteudo = %s, atualizado_em = NOW()
                        WHERE id = %s
                    """, [novo_conteudo, comentario_id])
                    
                    messages.success(request, 'Comentário atualizado com sucesso!')
                    return redirect('post_detail', slug=comentario['post']['slug'])
            
            # Mock do form para o template
            class MockForm:
                def __init__(self, conteudo):
                    self.conteudo = type('obj', (object,), {
                        'id_for_label': 'id_conteudo',
                        'label': 'Comentário',
                        'errors': [],
                        'help_text': ''
                    })()
                    self.conteudo_value = conteudo
            
            form = MockForm(comentario['conteudo'])
            
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
    
    SQL EXECUTADO:
    1. SELECT comentário por ID
    2. SELECT perfil do usuário (verificar se é admin)
    3. DELETE comentário
    """
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar comentário
            cursor.execute("""
                SELECT c.id, c.autor_id, p.slug
                FROM blog_comentario c
                INNER JOIN blog_post p ON c.post_id = p.id
                WHERE c.id = %s
            """, [comentario_id])
            
            comentario_data = cursor.fetchone()
            
            if not comentario_data:
                messages.error(request, 'Comentário não encontrado.')
                return redirect('post_list')
            
            comentario_id_db = comentario_data[0]
            autor_id = comentario_data[1]
            post_slug = comentario_data[2]
            
            # Verificar se é autor ou admin
            is_autor = request.user.id == autor_id
            is_admin = usuario_e_admin(request.user)
            
            if is_autor or is_admin:
                # SQL: Deletar comentário
                cursor.execute("""
                    DELETE FROM blog_comentario WHERE id = %s
                """, [comentario_id_db])
                
                messages.success(request, 'Comentário excluído com sucesso.')
                return redirect('post_detail', slug=post_slug)
            else:
                messages.error(request, 'Você não tem permissão para excluir este comentário.')
                return redirect('post_detail', slug=post_slug)
                
    except Exception as e:
        messages.error(request, f'Erro ao excluir comentário: {str(e)}')
        return redirect('post_list')


def signup(request):
    """
    Cadastro de novos usuários com email e CPF obrigatórios - 100% SQL PURO
    
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
                # form.save() agora usa SQL puro internamente
                user = form.save()
                
                # Login automático (Django gerencia a sessão)
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
    """
    Criar novo post - 100% SQL PURO
    
    SQL EXECUTADO:
    1. SELECT categorias (para dropdown)
    2. INSERT post (se válido)
    """
    if request.method == 'POST':
        # Processar formulário manualmente
        titulo = request.POST.get('titulo', '').strip()
        conteudo = request.POST.get('conteudo', '').strip()
        categoria_id = request.POST.get('categoria')
        imagem = request.FILES.get('imagem')
        
        # Validações
        if not titulo or len(titulo) < 5:
            messages.error(request, 'O título deve ter pelo menos 5 caracteres.')
        elif not conteudo:
            messages.error(request, 'O conteúdo não pode estar vazio.')
        else:
            # Gerar slug
            from django.utils.text import slugify
            slug = slugify(titulo)
            
            # Processar upload de imagem (se houver)
            imagem_path = None
            if imagem:
                from django.core.files.storage import default_storage
                import uuid
                
                # Validar extensão
                ext = imagem.name.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    messages.error(request, 'Formato de imagem inválido.')
                    form = PostForm()
                    return render(request, 'blog/post_form.html', {'form': form})
                
                # Salvar arquivo
                filename = f"posts/{uuid.uuid4()}.{ext}"
                imagem_path = default_storage.save(filename, imagem)
            
            # Converter categoria vazia para NULL
            if categoria_id == '':
                categoria_id = None
            
            try:
                with connection.cursor() as cursor:
                    # SQL: Inserir novo post
                    cursor.execute("""
                        INSERT INTO blog_post 
                        (titulo, slug, conteudo, imagem, categoria_id, 
                         autor_id, criado_em, atualizado_em)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, [titulo, slug, conteudo, imagem_path, 
                          categoria_id, request.user.id])
                
                messages.success(request, 'Post criado com sucesso!')
                return redirect('post_detail', slug=slug)
            except Exception as e:
                messages.error(request, f'Erro ao criar post: {str(e)}')
    
    # GET: Mostrar formulário vazio
    form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})


@login_required
def post_edit(request, slug):
    """
    Editar post existente (autor ou admin) - 100% SQL PURO
    
    SQL EXECUTADO:
    1. SELECT post por slug
    2. SELECT perfil do usuário (verificar se é admin)
    3. UPDATE post (se válido)
    """
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar post
            cursor.execute("""
                SELECT id, titulo, slug, conteudo, imagem, categoria_id, autor_id
                FROM blog_post
                WHERE slug = %s
            """, [slug])
            
            post_data = cursor.fetchone()
            
            if not post_data:
                messages.error(request, 'Post não encontrado.')
                return redirect('post_list')
            
            post_id = post_data[0]
            post_titulo = post_data[1]
            post_slug = post_data[2]
            post_conteudo = post_data[3]
            post_imagem = post_data[4]
            post_categoria_id = post_data[5]
            autor_id = post_data[6]
            
            # Verificar permissões
            is_autor = request.user.id == autor_id
            is_admin = usuario_e_admin(request.user)
            
            if not (is_autor or is_admin):
                messages.error(request, 'Você não tem permissão para editar este post.')
                return redirect('post_detail', slug=slug)
            
            if request.method == 'POST':
                # Processar formulário manualmente
                novo_titulo = request.POST.get('titulo', '').strip()
                novo_conteudo = request.POST.get('conteudo', '').strip()
                nova_categoria_id = request.POST.get('categoria')
                nova_imagem = request.FILES.get('imagem')
                
                # Validações
                if not novo_titulo or len(novo_titulo) < 5:
                    messages.error(request, 'O título deve ter pelo menos 5 caracteres.')
                elif not novo_conteudo:
                    messages.error(request, 'O conteúdo não pode estar vazio.')
                else:
                    # Gerar novo slug se título mudou
                    from django.utils.text import slugify
                    novo_slug = slugify(novo_titulo)
                    
                    # Processar upload de imagem (se houver)
                    imagem_path = post_imagem  # Manter imagem atual por padrão
                    if nova_imagem:
                        from django.core.files.storage import default_storage
                        import uuid
                        
                        # Validar extensão
                        ext = nova_imagem.name.split('.')[-1].lower()
                        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                            messages.error(request, 'Formato de imagem inválido.')
                        else:
                            # Salvar arquivo
                            filename = f"posts/{uuid.uuid4()}.{ext}"
                            imagem_path = default_storage.save(filename, nova_imagem)
                    
                    # Converter categoria vazia para NULL
                    if nova_categoria_id == '':
                        nova_categoria_id = None
                    
                    # SQL: Atualizar post
                    cursor.execute("""
                        UPDATE blog_post
                        SET titulo = %s, slug = %s, conteudo = %s, 
                            imagem = %s, categoria_id = %s, atualizado_em = NOW()
                        WHERE id = %s
                    """, [novo_titulo, novo_slug, novo_conteudo, 
                          imagem_path, nova_categoria_id, post_id])
                    
                    messages.success(request, 'Post atualizado com sucesso!')
                    return redirect('post_detail', slug=novo_slug)
            
            # Criar formulário manualmente (GET)
            form = PostForm(initial={
                'titulo': post_titulo,
                'conteudo': post_conteudo,
                'categoria': post_categoria_id or ''
            })
            
            # Mock do post para o template
            class ImagemMock:
                def __init__(self, url):
                    # Adicionar prefixo /media/ se não existir
                    if url and not url.startswith('/media/') and not url.startswith('http'):
                        self.url = f'/media/{url}'
                    else:
                        self.url = url if url else ''
            
            class InstanceMock:
                def __init__(self, pk, imagem):
                    self.pk = pk
                    self.imagem = ImagemMock(imagem) if imagem else None
            
            # Adicionar instance ao form para o template
            form.instance = InstanceMock(post_id, post_imagem)
            
            return render(request, 'blog/post_form.html', {
                'form': form
            })
            
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('post_list')


@login_required
def post_delete(request, slug):
    """
    Excluir post (autor ou admin)
    
    SQL EXECUTADO:
    1. SELECT post por slug
    2. SELECT perfil do usuário (verificar se é admin)
    3. DELETE comentários (CASCADE)
    4. DELETE reações (CASCADE)
    5. DELETE post
    """
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar post
            cursor.execute("""
                SELECT id, titulo, autor_id
                FROM blog_post
                WHERE slug = %s
            """, [slug])
            
            post_data = cursor.fetchone()
            
            if not post_data:
                messages.error(request, 'Post não encontrado.')
                return redirect('post_list')
            
            post_id = post_data[0]
            post_titulo = post_data[1]
            autor_id = post_data[2]
            
            # Verificar permissões
            is_autor = request.user.id == autor_id
            is_admin = usuario_e_admin(request.user)
            
            if not (is_autor or is_admin):
                messages.error(request, "Você não tem permissão para excluir este post.")
                return redirect('post_detail', slug=slug)
            
            if request.method == 'POST':
                try:
                    # SQL: Deletar comentários (CASCADE)
                    cursor.execute("""
                        DELETE FROM blog_comentario WHERE post_id = %s
                    """, [post_id])
                    
                    # SQL: Deletar reações (CASCADE)
                    cursor.execute("""
                        DELETE FROM blog_reacaousuariopost WHERE post_id = %s
                    """, [post_id])
                    
                    # SQL: Deletar post
                    cursor.execute("""
                        DELETE FROM blog_post WHERE id = %s
                    """, [post_id])
                    
                    messages.success(request, "Post excluído com sucesso.")
                    return redirect('post_list')
                except Exception as e:
                    messages.error(request, f'Erro ao excluir post: {str(e)}')
                    return redirect('post_detail', slug=slug)
            
            post_mock = {'titulo': post_titulo, 'slug': slug}
            return render(request, 'blog/post_confirm_delete.html', {'post': post_mock})
            
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('post_list')


@login_required
def desativar_usuario(request, usuario_id):
    """
    Desativa um usuário (apenas admin)
    
    SQL EXECUTADO:
    1. SELECT perfil do usuário logado (verificar se é admin)
    2. SELECT usuário a ser desativado
    3. SELECT perfil do usuário a ser desativado
    4. UPDATE perfil (ativo = FALSE)
    """
    # Verificar se o usuário logado é admin
    if not usuario_e_admin(request.user):
        messages.error(request, 'Você não tem permissão para desativar usuários.')
        return redirect('post_list')
    
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar usuário
            cursor.execute("""
                SELECT id, username
                FROM auth_user
                WHERE id = %s
            """, [usuario_id])
            
            usuario_data = cursor.fetchone()
            
            if not usuario_data:
                messages.error(request, 'Usuário não encontrado.')
                return redirect('post_list')
            
            user_id = usuario_data[0]
            username = usuario_data[1]
            
            # Não permite desativar a si mesmo
            if user_id == request.user.id:
                messages.error(request, 'Você não pode desativar sua própria conta.')
                return redirect('post_list')
            
            # SQL: Verificar se tem perfil
            cursor.execute("""
                SELECT id
                FROM blog_perfilusuario
                WHERE usuario_id = %s
            """, [user_id])
            
            perfil_data = cursor.fetchone()
            
            if perfil_data:
                # SQL: Desativar perfil
                cursor.execute("""
                    UPDATE blog_perfilusuario
                    SET ativo = FALSE, atualizado_em = NOW()
                    WHERE usuario_id = %s
                """, [user_id])
                
                messages.success(request, f'Usuário {username} foi desativado.')
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
    
    SQL EXECUTADO:
    1. SELECT perfil do usuário logado (verificar se é admin)
    2. SELECT usuário a ser ativado
    3. SELECT perfil do usuário a ser ativado
    4. UPDATE perfil (ativo = TRUE)
    """
    # Verificar se o usuário logado é admin
    if not usuario_e_admin(request.user):
        messages.error(request, 'Você não tem permissão para ativar usuários.')
        return redirect('post_list')
    
    try:
        with connection.cursor() as cursor:
            # SQL: Buscar usuário
            cursor.execute("""
                SELECT id, username
                FROM auth_user
                WHERE id = %s
            """, [usuario_id])
            
            usuario_data = cursor.fetchone()
            
            if not usuario_data:
                messages.error(request, 'Usuário não encontrado.')
                return redirect('post_list')
            
            user_id = usuario_data[0]
            username = usuario_data[1]
            
            # SQL: Verificar se tem perfil
            cursor.execute("""
                SELECT id
                FROM blog_perfilusuario
                WHERE usuario_id = %s
            """, [user_id])
            
            perfil_data = cursor.fetchone()
            
            if perfil_data:
                # SQL: Ativar perfil
                cursor.execute("""
                    UPDATE blog_perfilusuario
                    SET ativo = TRUE, atualizado_em = NOW()
                    WHERE usuario_id = %s
                """, [user_id])
                
                messages.success(request, f'Usuário {username} foi reativado.')
            else:
                messages.error(request, 'Usuário não possui perfil.')
            
            return redirect('post_list')
            
    except Exception as e:
        messages.error(request, f'Erro ao ativar usuário: {str(e)}')
        return redirect('post_list')