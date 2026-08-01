# clients/urls.py
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('dashboard-parent/', views.dashboard_parent, name='dashboard_parent'),
    path('enfants/', views.liste_enfants, name='liste_enfants'),
    path('enfants/ajouter/', views.ajouter_enfant, name='ajouter_enfant'),
    path('creer-profil-parent/', views.creer_profil_parent, name='creer_profil_parent'),
]