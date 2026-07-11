from django.db import models
from authentication.models import Utilisateur

class Diplome(models.Model):
    id_diplome = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='diplomes')
    titre = models.CharField(max_length=150)
    specialite = models.CharField(max_length=150)
    date_obtention = models.DateField()