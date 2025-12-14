#import os
from pathlib import Path

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança
SECRET_KEY = 'django-insecure-substitua-por-uma-chave-secreta-real'

# ⚠️ Nunca use DEBUG=True em produção!
DEBUG = False

# Hosts permitidos
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

LOGOUT_REDIRECT_URL = '/'

# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do projeto
    'blog',  
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meublog.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meublog.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'sql',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Validações de senha
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configurações de idioma e tempo
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Cuiaba'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos (CSS, JS, imagens)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Arquivos enviados por usuários
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Chave padrão para campo primário
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redirecionamento após login/logout
LOGIN_REDIRECT_URL = '/'

# ==========================================
# CONFIGURAÇÃO DE EMAIL
# ==========================================

# OPÇÃO 1: Para DESENVOLVIMENTO (emails aparecem no console/terminal)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# OPÇÃO 2: Para PRODUÇÃO com Gmail 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seuemail@gmail.com'  # Seu email
EMAIL_HOST_PASSWORD = 'sua_senha_app'    # Senha de app do Gmail
DEFAULT_FROM_EMAIL = 'seuemail@gmail.com'

# OPÇÃO 3: Para PRODUÇÃO com Outlook/Hotmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seuemail@outlook.com'
EMAIL_HOST_PASSWORD = 'sua_senha'
DEFAULT_FROM_EMAIL = 'seuemail@outlook.com'

# Email padrão do remetente (usado em todos os emails do sistema)
DEFAULT_FROM_EMAIL = 'noreply@meublog.com'


# Backend de autenticação customizado
AUTHENTICATION_BACKENDS = [
    'blog.backends.PerfilAtivoBackend',  # Nosso backend customizado
    'django.contrib.auth.backends.ModelBackend',  # Backend padrão (fallback)
]