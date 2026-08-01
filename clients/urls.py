# clients/urls.py
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('dashboard-parent/', views.dashboard_parent, name='dashboard_parent'),
    path('creer-profil-parent/', views.creer_profil_parent, name='creer_profil_parent'),
]