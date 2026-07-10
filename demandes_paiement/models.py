# demandes_paiement/models.py
from django.db import models
from utilisateurs.models import Utilisateur
from comptes_bancaires.models import CompteBancaire

class DemandePaiement(models.Model):
    STATUT_DEMANDE = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('paye', 'Payé'),
    ]
    
    compte_bancaire = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name='demandes')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='demandes_paiement')
    date_demande = models.DateField(auto_now_add=True)
    montant = models.FloatField()
    statut = models.CharField(max_length=20, choices=STATUT_DEMANDE, default='en_attente')
    recu_paiement = models.CharField(max_length=255, null=True, blank=True)
    raison = models.CharField(max_length=255, null=True, blank=True)
    type_demande = models.CharField(max_length=100)

    def __str__(self):
        return f"Demande de {self.utilisateur.username} - {self.montant}€ ({self.statut})"