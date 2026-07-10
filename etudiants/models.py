# etudiants/models.py
from django.db import models
from clients.models import Client

class Etudiant(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='etudiants')
    age = models.IntegerField()
    niveau = models.CharField(max_length=50)
    specialite = models.CharField(max_length=100)
    nom_parent = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    etablissement = models.CharField(max_length=150)
    matricule = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nom_parent} - {self.specialite}"