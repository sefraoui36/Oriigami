# clients/urls.py
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('dashboard-parent/', views.dashboard_parent, name='dashboard_parent'),
    path('enfants/', views.liste_enfants, name='liste_enfants'),
    path('enfants/ajouter/', views.ajouter_enfant, name='ajouter_enfant'),
    path('enseignants/', views.liste_enseignants, name='liste_enseignants'),
    path('forfaits/', views.liste_forfaits, name='liste_forfaits'),
    path('forfaits/acheter/', views.acheter_forfait, name='acheter_forfait'),
    path('creer-profil-parent/', views.creer_profil_parent, name='creer_profil_parent'),
]
