from django.db import models
from utilisateurs.models import Utilisateur

class ZoneDeplacement(models.Model):
    id_zone_Deplacement = models.AutoField(primary_key=True)
    zone = models.CharField(max_length=100)


class ZoneDeplacementEnseignant(models.Model):
    id_zone_deplacement = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='zones_deplacement')
    zone_deplacement = models.ForeignKey(ZoneDeplacement, on_delete=models.CASCADE, related_name='enseignants')