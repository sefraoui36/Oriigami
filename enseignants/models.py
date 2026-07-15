from django.db import models
from utilisateurs.models import Utilisateur


class Enseignant(models.Model):
    id_enseignant = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='enseignants')

    def __str__(self):
        return f"Enseignant: {self.utilisateur.username}"