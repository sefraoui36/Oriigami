# portefeuilles/urls.py
from django.urls import path
from . import views

app_name = 'portefeuilles'

urlpatterns = [
    path('mon-portefeuille/', views.mon_portefeuille, name='mon_portefeuille'),
    path('recharger/', views.recharger_portefeuille, name='recharger'),
    path('api/transactions/', views.transactions_api, name='transactions_api'),
]