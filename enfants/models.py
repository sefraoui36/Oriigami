# enfants/models.py
from django.db import models
from clients.models import Client

class Enfant(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='enfants')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    age = models.IntegerField()
    niveau = models.CharField(max_length=50)
    etablissement = models.CharField(max_length=150)
    matricule = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.age} ans)"