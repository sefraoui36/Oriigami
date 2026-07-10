# affectations/models.py
from django.db import models
from utilisateurs.models import Utilisateur
from rh.models import Rh
from forfaits.models import Forfait

class Affectation(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='affectations')
    rh = models.ForeignKey(Rh, on_delete=models.SET_NULL, null=True, related_name='affectations')
    forfait = models.ForeignKey(Forfait, on_delete=models.CASCADE, related_name='affectations')
    matiere = models.CharField(max_length=100)
    matiere_personnalise = models.CharField(max_length=100, null=True, blank=True)
    prix_renumeration = models.FloatField()
    statut_paiement = models.CharField(max_length=50)
    statut_affectation = models.CharField(max_length=50)
    heures_restantes = models.FloatField()
    a_ete_renouvelee = models.BooleanField(default=False)
    recu = models.CharField(max_length=255, null=True, blank=True)
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Affectation: {self.matiere} - {self.utilisateur.username}"