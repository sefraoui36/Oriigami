# forfaits/models.py
from django.db import models
from utilisateurs.models import Utilisateur

class Forfait(models.Model):
    TYPES_FORFAIT = [
        ('horaire', 'Horaire'),
        ('forfait', 'Forfait'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='forfaits')
    date = models.DateField()
    heureA = models.IntegerField()
    type = models.CharField(max_length=20, choices=TYPES_FORFAIT)
    nombre_heure = models.IntegerField()
    prix = models.FloatField()
    seuil = models.IntegerField()

    def __str__(self):
        return f"Forfait {self.type} - {self.utilisateur.username} ({self.prix}€)"