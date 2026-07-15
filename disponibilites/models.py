from django.db import models
from utilisateurs.models import Utilisateur

class Disponibilite(models.Model):
    id_disponibilite = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='disponibilites')
    jour = models.IntegerField()
    heured = models.IntegerField()
    heuref = models.IntegerField()