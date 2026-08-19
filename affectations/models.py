# affectations/models.py
from django.db import models
from django.conf import settings
from rh.models import Rh
from forfaits.models import Forfait
from enseignants.models import Enseignant  # ✅ nouvel import

class Affectation(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='affectations', db_index=True
    )
    # 🔥 NOUVEAU : lien direct et fiable vers l'enseignant, indépendant de Rh
    enseignant = models.ForeignKey(
        Enseignant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='affectations'
    )
    # ⚠️ On garde "rh" pour ne rien casser côté migrations/existant,
    # mais on ne l'utilise plus pour afficher le prof d'une affectation.
    rh = models.ForeignKey(Rh, on_delete=models.SET_NULL, null=True, related_name='affectations')
    forfait = models.ForeignKey(Forfait, on_delete=models.CASCADE, related_name='affectations')
    matiere = models.CharField(max_length=100, db_index=True)
    matiere_personnalise = models.CharField(max_length=100, null=True, blank=True)
    prix_renumeration = models.FloatField()
    statut_paiement = models.CharField(max_length=50)
    statut_affectation = models.CharField(max_length=50, db_index=True)
    heures_restantes = models.FloatField()
    a_ete_renouvelee = models.BooleanField(default=False)
    recu = models.CharField(max_length=255, null=True, blank=True)
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Affectation: {self.matiere} - {self.utilisateur.username}"