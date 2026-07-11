from django.db import models
from authentication.models import Utilisateur

class Rh(models.Model):
    id_rh = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='rhs')

    def __str__(self):
        return f"RH: {self.utilisateur.username}"