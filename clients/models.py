# clients/models.py
from django.db import models
from utilisateurs.models import Utilisateur

class Client(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='clients')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    adresse = models.TextField()

    def __str__(self):
        return f"{self.nom} {self.prenom}"