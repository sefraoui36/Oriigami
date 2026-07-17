# etudiants/urls.py
from django.urls import path
from . import views

app_name = 'etudiants'

urlpatterns = [
    path('profil/', views.profil, name='profil'),
    path('enseignants/', views.enseignants, name='enseignants'),
    path('seances/', views.seances, name='seances'),
    path('forfait/', views.forfait, name='forfait'),
    path('portefeuille/', views.portefeuille, name='portefeuille'),
    path('progression/', views.progression, name='progression'),
    path('avis/', views.avis, name='avis'),
    path('notifications/', views.notifications, name='notifications'),
    path('parametres/', views.parametres, name='parametres'),
]