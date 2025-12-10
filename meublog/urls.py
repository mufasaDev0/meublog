from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from blog.views import signup, welcome

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rotas do blog
    path('', include('blog.urls')),
    
    # Customizações primeiro
    path('accounts/signup/', signup, name='signup'),
    path('accounts/welcome/', welcome, name='welcome'),
    
    # URLs de autenticação do Django por último
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
