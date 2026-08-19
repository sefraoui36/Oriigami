# enseignants/models.py
from django.db import models
from django.conf import settings  # ← Utiliser settings au lieu de l'import direct

class Enseignant(models.Model):
    id_enseignant = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ← Utiliser le modèle d'authentification principal
        on_delete=models.CASCADE, 
        related_name='enseignants'
    )
    # Ajoutez ces champs si vous les utilisez
    matiere = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    experience = models.CharField(max_length=255, null=True, blank=True)
    diplome = models.CharField(max_length=255, null=True, blank=True)
    disponible = models.BooleanField(default=True)
    tarif_heure = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Enseignant: {self.utilisateur.username}"