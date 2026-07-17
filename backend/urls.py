# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('authentication:inscription')),  # Redirige vers l'inscription
    path('', include('authentication.urls')), 
    path('etudiants/', include('etudiants.urls')),# Inclut les URLs de authentication
]