# seances/models.py
from django.db import models
from affectations.models import Affectation

class Seance(models.Model):
    STATUT_SEANCE = [
        ('prevue', 'Prévue'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('reportee', 'Reportée'),
    ]
    
    affectation = models.ForeignKey(Affectation, on_delete=models.CASCADE, related_name='seances')
    date = models.DateField()
    heure = models.TimeField()
    duree = models.CharField(max_length=50)
    qualite = models.CharField(max_length=100, null=True, blank=True)
    type_seance = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=STATUT_SEANCE, default='prevue')

    def __str__(self):
        return f"Séance du {self.date} - {self.affectation.matiere} ({self.statut})"