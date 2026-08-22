# seances/urls.py
from django.urls import path
from . import views

app_name = 'seances'

urlpatterns = [
    path('reserver/', views.reserver_seance, name='reserver_seance'),
    path('reserver-parent/', views.reserver_seance_parent, name='reserver_seance_parent'),
    path('suggerer-professeurs/', views.suggerer_professeurs, name='suggerer_professeurs'),
    path('suggerer-professeurs-multiples/', views.suggerer_professeurs_multiples, name='suggerer_professeurs_multiples'),
    path('nouvelle-reservation/', views.reserver_seance, name='nouvelle_reservation'),
    path('confirmer-reservation/', views.confirmer_reservation, name='confirmer_reservation'),
    path('confirmer-reservation-parent/', views.confirmer_reservation_parent, name='confirmer_reservation_parent'), 
    path('supprimer-reservation/<int:affectation_id>/', views.supprimer_reservation, name='supprimer_reservation'),
]