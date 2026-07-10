# tuteurs/models.py
from django.db import models
from utilisateurs.models import Utilisateur

class Tuteur(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='tuteurs')

    def __str__(self):
        return f"Tuteur: {self.utilisateur.username}"