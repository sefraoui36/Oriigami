# seances/urls.py
from django.urls import path
from . import views

app_name = 'seances'

urlpatterns = [
    path('reserver/', views.reserver_seance, name='reserver_seance'),
    path('suggerer-professeurs/', views.suggerer_professeurs, name='suggerer_professeurs'),
    path('suggerer-professeurs-multiples/', views.suggerer_professeurs_multiples, name='suggerer_professeurs_multiples'),
    path('nouvelle-reservation/', views.reserver_seance, name='nouvelle_reservation'),
    path('confirmer-reservation/', views.confirmer_reservation, name='confirmer_reservation'),
    path('supprimer-reservation/<int:affectation_id>/', views.supprimer_reservation, name='supprimer_reservation'),
]