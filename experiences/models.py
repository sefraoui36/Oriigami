from django.db import models
from authentication.models import Utilisateur

class Experience(models.Model):
    id_experience = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='experiences')
    intitule_poste = models.CharField(max_length=150)
    type = models.CharField(max_length=50)
    institution = models.CharField(max_length=150)
    date_debut = models.DateField()
    date_finale = models.DateField(null=True, blank=True)