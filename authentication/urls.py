# authentication/urls.py
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # La racine /auth/ redirige vers la page de connexion
    path('', views.connexion, name='home'),
    
    # Authentification
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dashboard/', views.dashboard, name='dashboard'),
]