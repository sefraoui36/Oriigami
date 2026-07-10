# portefeuilles/models.py
from django.db import models
from utilisateurs.models import Utilisateur

class Portefeuille(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='portefeuilles')
    solde = models.FloatField(default=0.0)

    def __str__(self):
        return f"Portefeuille de {self.utilisateur.username} - {self.solde}€"