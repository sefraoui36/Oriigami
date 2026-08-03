# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # La racine / redirige vers la page de connexion
    path('', RedirectView.as_view(url='/auth/connexion/', permanent=False), name='home'),
    
    # Toutes les URLs de l'application authentication
    path('auth/', include('authentication.urls')),
    
    # Autres applications
    path('clients/', include('clients.urls')),
    path('etudiants/', include('etudiants.urls')),
    path('portefeuilles/', include('portefeuilles.urls')),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)